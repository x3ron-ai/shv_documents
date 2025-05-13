import os, random, string, subprocess, psycopg2, xml.etree.ElementTree as ET, logging, mimetypes
from flask import Flask, render_template, request, redirect, url_for, send_file, make_response, jsonify
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from parser import XMLToWordParser
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET')

with open('app.log', 'w') as f: f.write('')

logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

DB_CONFIG = {'dbname': os.getenv('DB_NAME'),'user': os.getenv('DB_USER'),'password': os.getenv('DB_PASSWORD'),'host': os.getenv('DB_HOST'),'port': os.getenv('DB_PORT')}
UPLOADS_DIR = 'uploads'; DOCUMENTS_DIR = 'documents'; PREVIEW_DIR = 'static/previews'; TEMP_DOCX = 'temp.doc'; TEMP_DIR = 'static/previews'
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(DOCUMENTS_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

def get_db_connection(): return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def generate_session_token(): return ''.join(random.choices(string.ascii_letters + string.digits, k=128))

def get_current_user():
    session_token = request.cookies.get('session_token')
    if not session_token: return None
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id FROM sessions WHERE session_token = %s AND expires_at > NOW()', (session_token,))
            session = cur.fetchone()
            if session:
                cur.execute('SELECT id, username FROM users WHERE id = %s', (session['user_id'],))
                return cur.fetchone()
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id, password_hash FROM users WHERE username = %s', (username,))
                user = cur.fetchone()
                if user and check_password_hash(user['password_hash'], password):
                    session_token = generate_session_token()
                    cur.execute('INSERT INTO sessions (user_id, session_token, expires_at) VALUES (%s, %s, NOW() + INTERVAL \'7 days\')', (user['id'], session_token))
                    conn.commit()
                    resp = make_response(redirect(url_for('index')))
                    resp.set_cookie('session_token', session_token, max_age=7*24*60*60)
                    return resp
                return render_template('login.html', templates=get_all_templates(), error='Неверный логин или пароль')
    return render_template('login.html', templates=get_all_templates(), error=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username, password, email = request.form['username'], request.form['password'], request.form['email']
        logger.info(f"REGISTER - {username} {password} {email}")
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute('INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)',(username, generate_password_hash(password), email))
                    conn.commit()
                    return redirect(url_for('login'))
                except psycopg2.IntegrityError:
                    conn.rollback()
                    return render_template('register.html', error='Пользователь с таким именем или email уже существует')
    return render_template('register.html', error=None)

@app.route('/logout')
def logout():
    session_token = request.cookies.get('session_token')
    if session_token:
        with get_db_connection() as conn:
            with conn.cursor() as cur: cur.execute('DELETE FROM sessions WHERE session_token = %s', (session_token,)); conn.commit()
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('session_token', '', expires=0)
    return resp

def get_all_templates():
    with get_db_connection() as conn:
        with conn.cursor() as cur: cur.execute('SELECT id, title, preview_path FROM templates'); return cur.fetchall()

@app.route('/')
def index():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''SELECT documents.id, documents.title, documents.created_at, templates.preview_path FROM  documents JOIN templates ON documents.template_id = templates.id WHERE documents.owner_id = %s ORDER BY documents.created_at DESC''', (user['id'],))
            documents = cur.fetchall()
    templates = get_all_templates()
    return render_template('index.html', documents=documents, templates=templates, user=user)

@app.route('/create', methods=['GET'])
def create():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    return redirect(url_for('edit_document', doc_id=0))

def validate_image(file):
    MAX_FILE_SIZE = 10 * 1024 * 1024
    ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/bmp'}

    if file.content_length > MAX_FILE_SIZE: return False, "Файл слишком большой. Максимальный размер: 10 МБ."
    mime_type, _ = mimetypes.guess_type(file.filename)
    if mime_type not in ALLOWED_MIME_TYPES: return False, "Недопустимый формат файла. Поддерживаются: JPEG, PNG, GIF, BMP."
    return True, None

@app.route('/document/<int:doc_id>', methods=['GET', 'POST'])
def edit_document(doc_id):
    user = get_current_user()
    if not user: return redirect(url_for('login'))

    document = None
    if doc_id != 0:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM documents WHERE id = %s AND owner_id = %s', (doc_id, user['id']))
                document = cur.fetchone()
                if not document: return 'Документ не найден или не принадлежит вам', 403
        logger.info(f"Загружен существующий документ: id={doc_id}, title={document['title']}")

    if request.method == 'POST':
        logger.info(f"Получен POST-запрос для doc_id={doc_id}")
        
        if doc_id == 0:
            title = request.form.get('title', '').strip()
            template_id = request.form.get('template_id')
            if not title: return jsonify({'error': 'Название документа не может быть пустым'}), 400
            if not template_id: return jsonify({'error': 'Выбор шаблона обязателен'}), 400
            xml_path = f"{DOCUMENTS_DIR}/{user['id']}_{title.replace(' ', '_')}_{random.randint(1000, 9999)}.xml"
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('INSERT INTO documents (owner_id, template_id, title, xml_path) VALUES (%s, %s, %s, %s) RETURNING id', (user['id'], template_id, title, xml_path)); doc_id = cur.fetchone()['id']; conn.commit()
            document = {'id': doc_id, 'title': title, 'xml_path': xml_path, 'template_id': template_id}
            logger.info(f"Создан новый документ: id={doc_id}, title={title}")
        else:
            if not document: return jsonify({'error': 'Документ не найден'}), 404
            logger.info(f"Обновление существующего документа: id={doc_id}, title={document['title']}")

        blocks = request.form.getlist('block_type[]')
        contents = request.form.getlist('content[]')
        aligns = request.form.getlist('align[]')
        indents_left = request.form.getlist('indent_left[]')
        indents_first_line = request.form.getlist('indent_first_line[]')
        line_spacings = request.form.getlist('line_spacing[]')
        col_widths = request.form.get('col_widths', '2,1,2')
        images = request.files.getlist('image[]')
        image_paths = request.form.getlist('image_path[]')
        image_captions = request.form.getlist('image_caption[]')
        caption_bolds = request.form.getlist('caption_bold[]')
        caption_sizes = request.form.getlist('caption_size[]')
        caption_faces = request.form.getlist('caption_face[]')
        caption_colors = request.form.getlist('caption_color[]')
        list_item_numbers = request.form.getlist('list_item_number[]')

        logger.info(f"blocks: {blocks}")
        logger.info(f"contents: {contents}")
        logger.info(f"list_item_numbers: {list_item_numbers}")

        root = ET.Element("root")

        content_idx = image_idx = list_item_idx = style_idx= 0
        
        for block_idx, block in enumerate(blocks):
            logger.info(f"Обработка блока {block_idx}: {block}")
            if block == "text" and content_idx < len(contents):
                text_elem = ET.SubElement(root, "text")
                text_elem.text = contents[content_idx]
                text_elem.set("align", aligns[style_idx] if style_idx < len(aligns) else "justify")
                text_elem.set("indent_left", indents_left[style_idx] if style_idx < len(indents_left) else "0")
                text_elem.set("indent_first_line", indents_first_line[style_idx] if style_idx < len(indents_first_line) else "0")
                text_elem.set("line_spacing", line_spacings[style_idx] if style_idx < len(line_spacings) else "1.5")
                font_face = request.form.get(f'face_block_{style_idx}', 'Times New Roman')
                font_size = request.form.get(f'size_block_{style_idx}', '14')
                text_elem.set("font_face", font_face)
                text_elem.set("font_size", font_size)
                content_idx += 1
                style_idx += 1
            elif block == "list_item" and content_idx < len(contents):
                text_elem = ET.SubElement(root, "list_item")
                text_elem.text = contents[content_idx]
                text_elem.set("align", aligns[style_idx] if style_idx < len(aligns) else "justify")
                text_elem.set("indent_left", indents_left[style_idx] if style_idx < len(indents_left) else "0")
                text_elem.set("indent_first_line", indents_first_line[style_idx] if style_idx < len(indents_first_line) else "0")
                text_elem.set("line_spacing", line_spacings[style_idx] if style_idx < len(line_spacings) else "1.5")
                font_face = request.form.get(f'face_block_{style_idx}', 'Times New Roman')
                font_size = request.form.get(f'size_block_{style_idx}', '14')
                text_elem.set("font_face", font_face)
                text_elem.set("font_size", font_size)
                if list_item_idx < len(list_item_numbers) and list_item_numbers[list_item_idx].strip():
                    text_elem.set("list_item_number", list_item_numbers[list_item_idx])
                    logger.info(f"Присвоен list_item_number: {list_item_numbers[list_item_idx]} для блока {block_idx}")
                    list_item_idx += 1
                else: logger.info(f"Нет list_item_number для блока {block_idx}, пропущено")
                content_idx += 1
                style_idx += 1
            elif block == "comment" and content_idx < len(contents):
                comment_elem = ET.SubElement(root, "comment")
                comment_elem.text = contents[content_idx]
                content_idx += 1
            elif block == "table" and content_idx < len(contents):
                table_elem = ET.SubElement(root, "table")
                table_elem.set("col_widths", col_widths)
                rows = contents[content_idx].split('\n')
                for row in rows:
                    if row.strip():
                        row_elem = ET.SubElement(table_elem, "row")
                        cells = row.split(',')
                        for cell in cells:
                            cell_elem = ET.SubElement(row_elem, "cell")
                            cell_elem.text = cell.strip()
                content_idx += 1
            elif block == "image" and image_idx < len(images):
                image_elem = ET.SubElement(root, "image")
                if images[image_idx] and images[image_idx].filename:
                    is_valid, error = validate_image(images[image_idx])
                    if not is_valid: return jsonify({'error': f"Ошибка загрузки изображения: {error}"}), 400
                    unique_filename = f"{user['id']}_{image_idx}_{random.randint(1000, 9999)}_{images[image_idx].filename}"
                    image_path = os.path.join(UPLOADS_DIR, unique_filename)
                    images[image_idx].save(image_path)
                    image_elem.set("path", image_path)
                elif image_idx < len(image_paths) and image_paths[image_idx]: image_elem.set("path", image_paths[image_idx].lstrip('/'))
                if image_idx < len(image_captions) and image_captions[image_idx].strip():
                    image_elem.set("caption", image_captions[image_idx])
                    image_elem.set("caption_bold", "true" if image_idx < len(caption_bolds) and caption_bolds[image_idx] == "on" else "false")
                    image_elem.set("caption_size", caption_sizes[image_idx] if image_idx < len(caption_sizes) else "12")
                    image_elem.set("caption_face", caption_faces[image_idx] if image_idx < len(caption_faces) else "Times New Roman")
                    image_elem.set("caption_color", caption_colors[image_idx].lstrip('#') if image_idx < len(caption_colors) else "000000")
                image_idx += 1
            else: logger.warning(f"Пропущен блок {block_idx}: {block}, нет соответствующих данных")

        xml_str = ET.tostring(root, encoding='utf-8', method='xml')
        with open(document['xml_path'], 'wb') as f: f.write(xml_str)
        logger.info(f"Сохранен XML в {document['xml_path']}")

        if 'generate' in request.form:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT title_page_path FROM templates WHERE id = %s', (document['template_id'],))
                    template = cur.fetchone()
            if not template: return jsonify({'error': 'Шаблон не найден'}), 400
            title_page_path = template['title_page_path']
            logger.info(f"Сгенерирован XML: {ET.tostring(root, encoding='unicode')}")
            parser = XMLToWordParser(document['xml_path'], TEMP_DOCX, title_page_path)
            result = parser.parse_and_convert()
            if "Ошибка" not in result:
                logger.info(f"Сгенерирован DOCX для документа id={doc_id}")
                return send_file(TEMP_DOCX, as_attachment=True, download_name=f"{document['title']}_{doc_id}.docx")
            logger.error(f"Ошибка генерации: {result}")
            return jsonify({'error': f"Ошибка генерации: {result}"}), 500
        
        return jsonify({'success': True, 'doc_id': doc_id})

    logger.info(f"Рендеринг страницы редактирования для doc_id={doc_id}")
    return render_template('edit.html', template_id=doc_id, templates=get_all_templates(), error=None)

@app.route('/uploads/<path:filename>')
def serve_uploaded_file(filename): return send_file(os.path.join(UPLOADS_DIR, filename))

@app.route('/upload_image', methods=['POST'])
def upload_image():
    user = get_current_user()
    if not user: return jsonify({'error': 'Не авторизован'}), 401
    image = request.files.get('image')
    if image and image.filename:
        is_valid, error = validate_image(image)
        if not is_valid: return jsonify({'error': error}), 400
        unique_filename = f"{user['id']}_{random.randint(1000, 9999)}_{image.filename}"
        image_path = os.path.join(UPLOADS_DIR, unique_filename)
        image.save(image_path)
        return jsonify({'path': f"/uploads/{unique_filename}"})
    return jsonify({'error': 'Изображение не загружено'}), 400

@app.route('/create_template', methods=['GET', 'POST'])
def create_template():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title'].strip()
        title_page = request.files.get('title_page')
        font_face = request.form.get('font_face', 'Times New Roman')
        font_size = request.form.get('font_size', '14')
        indent_left = request.form.get('indent_left', '0')
        indent_first_line = request.form.get('indent_first_line', '0')
        line_spacing = request.form.get('line_spacing', '1.5')

        logger.info(f"Создание шаблона: title={title}, title_page={title_page.filename if title_page else None}")

        if not title or not title_page or not title_page.filename:
            logger.warning("Не заполнены обязательные поля")
            return render_template('create_template.html', error='Заполните все обязательные поля')

        safe_title = ''.join(c for c in title if c.isalnum() or c in ' _-')
        title_page_path = os.path.join(UPLOADS_DIR, f"template_{user['id']}_{safe_title}_{random.randint(1000, 9999)}.docx")
        title_page.save(title_page_path)
        logger.info(f"Файл титульной страницы сохранён: {title_page_path}")

        preview_path = generate_preview(title_page_path)
        if preview_path:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('INSERT INTO templates (author_id, title, title_page_path, preview_path, default_font_face, default_font_size, default_indent_left, default_indent_first_line, default_line_spacing) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', (user['id'], title, title_page_path, preview_path, font_face, font_size, indent_left, indent_first_line, line_spacing))
                    conn.commit()
            logger.info(f"Шаблон '{title}' успешно добавлен в базу данных")
            return redirect(url_for('index'))
        logger.error(f"Не удалось создать предпросмотр для шаблона '{title}'")
        return render_template('create_template.html', error='Не удалось создать предпросмотр шаблона. Проверьте файл и попробуйте снова.')
    return render_template('create_template.html', error=None)

@app.route('/get_template/<int:doc_id>')
def get_template(doc_id):
    user = get_current_user()
    if not user: return jsonify({'error': 'Не авторизован'}), 401
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT xml_path, template_id FROM documents WHERE id = %s AND owner_id = %s', (doc_id, user['id']))
            document = cur.fetchone()
            if not document: return jsonify({'error': 'Документ не найден'}), 403
            data = {"blocks": [], "contents": [], "aligns": [], "indents_left": [], "indents_first_line": [], "line_spacings": [], "paths": [], "captions": [], "font_faces": [], "font_sizes": [], "col_widths": "2,1,2", "list_item_numbers": [], "global_indent_left": "0", "global_indent_first_line": "0", "global_line_spacing": "1.5"}

            if os.path.exists(document['xml_path']):
                with open(document['xml_path'], 'r', encoding='utf-8') as f:
                    root = ET.fromstring(f.read())
                    data["global_indent_left"] = root.get("global_indent_left", "0")
                    data["global_indent_first_line"] = root.get("global_indent_first_line", "0")
                    data["global_line_spacing"] = root.get("global_line_spacing", "1.5")
                    for elem in root:
                        if elem.tag in ["text", "list_item"]:
                            data["blocks"].append(elem.tag)
                            data["contents"].append(elem.text or "")
                            data["aligns"].append(elem.get("align", "justify"))
                            data["indents_left"].append(elem.get("indent_left", "0"))
                            data["indents_first_line"].append(elem.get("indent_first_line", "0"))
                            data["line_spacings"].append(elem.get("line_spacing", "1.5"))
                            data["font_faces"].append(elem.get("font_face", "Times New Roman"))
                            data["font_sizes"].append(elem.get("font_size", "14"))
                            data["paths"].append("")
                            data["captions"].append("")
                            data["list_item_numbers"].append(elem.get("list_item_number", "") if elem.tag == "list_item" else "")
                        elif elem.tag == "comment":
                            data["blocks"].append("comment")
                            data["contents"].append(elem.text or "")
                            data["aligns"].append("")
                            data["indents_left"].append("0")
                            data["indents_first_line"].append("0")
                            data["line_spacings"].append("1.5")
                            data["font_faces"].append("")
                            data["font_sizes"].append("")
                            data["paths"].append("")
                            data["captions"].append("")
                            data["list_item_numbers"].append("")
                        elif elem.tag == "table":
                            data["blocks"].append("table")
                            rows = [",".join(cell.text or "" for cell in row.findall("cell")) for row in elem.findall("row")]
                            data["contents"].append("\n".join(rows))
                            data["aligns"].append("")
                            data["indents_left"].append("0")
                            data["indents_first_line"].append("0")
                            data["line_spacings"].append("1.5")
                            data["font_faces"].append("")
                            data["font_sizes"].append("")
                            data["paths"].append("")
                            data["captions"].append("")
                            data["list_item_numbers"].append("")
                            data["col_widths"] = elem.get("col_widths", "2,1,2")
                        elif elem.tag == "image":
                            data["blocks"].append("image")
                            data["contents"].append("")
                            data["aligns"].append("")
                            data["indents_left"].append("0")
                            data["indents_first_line"].append("0")
                            data["line_spacings"].append("1.5")
                            data["font_faces"].append("")
                            data["font_sizes"].append("")
                            image_path = elem.get("path", "")
                            data["paths"].append(f"/uploads/{os.path.basename(image_path)}" if image_path else "")
                            data["captions"].append(elem.get("caption", ""))
                            data["list_item_numbers"].append("")

            if document['template_id']:
                cur.execute('SELECT default_font_face, default_font_size, default_indent_left, default_indent_first_line, default_line_spacing FROM templates WHERE id = %s', (document['template_id'],))
                template = cur.fetchone()
                if template: data.update({ "default_font_face": template['default_font_face'], "default_font_size": template['default_font_size'], "default_indent_left": template['default_indent_left'], "default_indent_first_line": template['default_indent_first_line'], "default_line_spacing": template['default_line_spacing']})
            logger.info(f"Returning template data for doc_id={doc_id}: {data}")
    return jsonify(data)

def generate_preview(docx_path):
    safe_filename = docx_path
    preview_filename = f"static/previews/{safe_filename.replace('.docx', '.png').replace('uploads/', '')}"
    preview_path = preview_filename
    pdf_path = os.path.join(TEMP_DIR, f"{safe_filename.replace('.docx', '.pdf').replace('uploads/', '')}")

    try:
        result = subprocess.run( ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', TEMP_DIR, docx_path], check=True, capture_output=True, text=True)
        logger.info(f"PDF успешно создан: {result.stdout}")
    except: logger.info(f"gg")
    try:
        result = subprocess.run(['pdftoppm', pdf_path, preview_path.replace('.png', ''), '-png', '-f', '1', '-l', '1', '-singlefile'], check=True, capture_output=True, text=True)
        logger.info(f"PNG успешно создан: {result.stdout}")
        os.remove(pdf_path)
        return f"{preview_filename}"
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка генерации предпросмотра: {e.stderr}")
        if os.path.exists(pdf_path): os.remove(pdf_path)
        return None
    except Exception as e:
        logger.error(f"Неизвестная ошибка при генерации предпросмотра: {str(e)}")
        return None

if __name__ == '__main__': app.run(host='0.0.0.0', port=5724, debug=True)