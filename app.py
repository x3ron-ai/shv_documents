import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, send_file, make_response
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
import xml.etree.ElementTree as ET
from parser import XMLToWordParser
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'ебаный_случай_2025'

DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

UPLOADS_DIR = 'uploads'
DOCUMENTS_DIR = 'documents'
PREVIEW_DIR = 'static/previews'  # Изменили на static/previews
TEMP_DOCX = 'temp.docx'

def generate_preview(docx_path):
    preview_path = os.path.join(PREVIEW_DIR, f"preview_{os.path.basename(docx_path).replace('.docx', '.png')}")
    os.system(f"convert {docx_path}[0] {preview_path}")
    return preview_path

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(DOCUMENTS_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def generate_session_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=128))

def get_current_user():
    session_token = request.cookies.get('session_token')
    if not session_token:
        return None
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT user_id FROM sessions WHERE session_token = %s AND expires_at > NOW()', (session_token,))
    session = cur.fetchone()
    if session:
        cur.execute('SELECT id, username FROM users WHERE id = %s', (session['user_id'],))
        user = cur.fetchone()
        conn.close()
        return user
    conn.close()
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, password_hash FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session_token = generate_session_token()
            cur.execute('INSERT INTO sessions (user_id, session_token, expires_at) VALUES (%s, %s, NOW() + INTERVAL \'7 days\')',
                        (user['id'], session_token))
            conn.commit()
            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('session_token', session_token, max_age=7*24*60*60)
            conn.close()
            return resp
        conn.close()
        return 'Неверный логин или пароль, пиздец тебе'
    templates = get_all_templates()
    return render_template('login.html', templates=templates)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)',
                        (username, generate_password_hash(password), email))
            conn.commit()
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            conn.rollback()
            return 'Такой юзер уже есть, пиздец'
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session_token = request.cookies.get('session_token')
    if session_token:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM sessions WHERE session_token = %s', (session_token,))
        conn.commit()
        conn.close()
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('session_token', '', expires=0)
    return resp

def get_all_templates():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, title, preview_path FROM templates')
    templates = cur.fetchall()
    conn.close()
    return templates

@app.route('/')
def index():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, title, created_at FROM documents WHERE owner_id = %s', (user['id'],))
    documents = cur.fetchall()
    templates = get_all_templates()
    conn.close()
    return render_template('index.html', documents=documents, templates=templates, user=user)

@app.route('/create', methods=['GET', 'POST'])
def create():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if request.method == 'POST':
        template_id = request.form.get('template_id')
        title = request.form['title']
        xml_path = f"{DOCUMENTS_DIR}/{user['id']}_{title.replace(' ', '_')}.xml"  # Изменили TEMPLATES_DIR на DOCUMENTS_DIR
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO documents (owner_id, template_id, title, xml_path) VALUES (%s, %s, %s, %s) RETURNING id',
                    (user['id'], template_id if template_id else None, title, xml_path))
        doc_id = cur.fetchone()['id']
        conn.commit()
        conn.close()
        return redirect(url_for('edit_document', doc_id=doc_id))
    templates = get_all_templates()
    return render_template('create.html', templates=templates)

@app.route('/document/<int:doc_id>', methods=['GET', 'POST'])
def edit_document(doc_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM documents WHERE id = %s AND owner_id = %s', (doc_id, user['id']))
    document = cur.fetchone()
    if not document:
        conn.close()
        return 'Документ не найден или не твой, пиздец', 403

    if request.method == 'POST':
        blocks = request.form.getlist('block_type[]')
        contents = request.form.getlist('content[]')
        aligns = request.form.getlist('align[]')
        indents_left = request.form.getlist('indent_left[]')
        indents_first_line = request.form.getlist('indent_first_line[]')
        line_spacings = request.form.getlist('line_spacing[]')
        col_widths = request.form.get('col_widths', '2,1,2')
        list_types = request.form.getlist('list_type[]')
        images = request.files.getlist('image[]')
        image_paths = request.form.getlist('image_path[]')
        image_captions = request.form.getlist('image_caption[]')
        caption_bolds = request.form.getlist('caption_bold[]')
        caption_sizes = request.form.getlist('caption_size[]')
        caption_faces = request.form.getlist('caption_face[]')
        caption_colors = request.form.getlist('caption_color[]')

        root = ET.Element("root")
        content_idx = 0
        image_idx = 0

        for block in blocks:
            if block == "text" and content_idx < len(contents):
                text_elem = ET.SubElement(root, "text")
                text_elem.text = contents[content_idx]
                text_elem.set("align", aligns[content_idx] if content_idx < len(aligns) else "justify")
                text_elem.set("indent_left", indents_left[content_idx] if content_idx < len(indents_left) else "0")
                text_elem.set("indent_first_line", indents_first_line[content_idx] if content_idx < len(indents_first_line) else "0")
                text_elem.set("line_spacing", line_spacings[content_idx] if content_idx < len(line_spacings) else "1.5")
                font_face = request.form.get(f'face_block_{content_idx}', 'Times New Roman')
                font_size = request.form.get(f'size_block_{content_idx}', '14')
                text_elem.set("font_face", font_face)
                text_elem.set("font_size", font_size)
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
            elif block in ["numbered_list", "bullet_list"] and content_idx < len(contents):
                list_elem = ET.SubElement(root, "list")
                list_elem.set("type", "numbered" if block == "numbered_list" else "bullet")
                items = contents[content_idx].split('\n')
                for item in items:
                    if item.strip():
                        item_elem = ET.SubElement(list_elem, "item")
                        item_elem.text = item.strip()
                content_idx += 1
            elif block == "image" and image_idx < len(image_paths):
                image_elem = ET.SubElement(root, "image")
                if image_idx < len(images) and images[image_idx]:
                    unique_filename = f"{user['id']}_{image_idx}_{images[image_idx].filename}"
                    image_path = os.path.join(UPLOADS_DIR, unique_filename)
                    images[image_idx].save(image_path)
                    image_elem.set("path", image_path)
                elif image_paths[image_idx]:
                    image_elem.set("path", image_paths[image_idx])
                if image_idx < len(image_captions) and image_captions[image_idx].strip():
                    image_elem.set("caption", image_captions[image_idx])
                    image_elem.set("caption_bold", "true" if image_idx < len(caption_bolds) and caption_bolds[image_idx] == "on" else "false")
                    image_elem.set("caption_size", caption_sizes[image_idx] if image_idx < len(caption_sizes) else "12")
                    image_elem.set("caption_face", caption_faces[image_idx] if image_idx < len(caption_faces) else "Times New Roman")
                    image_elem.set("caption_color", caption_colors[image_idx].lstrip('#') if image_idx < len(caption_colors) else "000000")
                image_idx += 1

        xml_str = ET.tostring(root, encoding='utf-8', method='xml', xml_declaration=True)
        with open(document['xml_path'], 'wb') as f:
            f.write(xml_str)

        if 'generate' in request.form:
            cur.execute('SELECT title_page_path FROM templates WHERE id = %s', (document['template_id'],))
            template = cur.fetchone()
            title_page_path = template['title_page_path'] if template else None
            parser = XMLToWordParser(document['xml_path'], TEMP_DOCX, title_page_path)
            result = parser.parse_and_convert()
            conn.close()
            if "Ошибка" not in result:
                return send_file(TEMP_DOCX, as_attachment=True, download_name=f"document_{doc_id}.docx")
            return f"Ошибка: {result}"

        conn.close()
        return "", 204

    conn.close()
    return render_template('edit.html', template_id=doc_id)

@app.route('/create_template', methods=['GET', 'POST'])
def create_template():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        title_page = request.files['title_page']
        font_face = request.form.get('font_face', 'Times New Roman')
        font_size = request.form.get('font_size', '14')
        indent_left = request.form.get('indent_left', '0')
        indent_first_line = request.form.get('indent_first_line', '0')
        line_spacing = request.form.get('line_spacing', '1.5')

        title_page_path = os.path.join(UPLOADS_DIR, f"template_{user['id']}_{title.replace(' ', '_')}.docx")
        title_page.save(title_page_path)
        preview_path = generate_preview(title_page_path)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO templates (author_id, title, title_page_path, preview_path, default_font_face, default_font_size, default_indent_left, default_indent_first_line, default_line_spacing) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (user['id'], title, title_page_path, preview_path, font_face, font_size, indent_left, indent_first_line, line_spacing))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('create_template.html')

@app.route('/previews/<path:filename>')
def serve_previews(filename):
    return send_file(os.path.join(PREVIEW_DIR, filename))

@app.route('/get_template/<int:doc_id>')
def get_template(doc_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT xml_path, template_id FROM documents WHERE id = %s AND owner_id = %s', (doc_id, user['id']))
    document = cur.fetchone()
    if not document:
        conn.close()
        return 'Документ не твой или не существует', 403

    data = {
        "blocks": [],
        "contents": [],
        "aligns": [],
        "indents_left": [],
        "indents_first_line": [],
        "line_spacings": [],
        "paths": [],
        "captions": [],
        "font_faces": [],
        "font_sizes": [],
        "col_widths": "2,1,2"
    }

    if os.path.exists(document['xml_path']):
        with open(document['xml_path'], 'r', encoding='utf-8') as f:
            root = ET.fromstring(f.read())
            for elem in root:
                data["blocks"].append(elem.tag)
                if elem.tag == "text":
                    data["contents"].append(elem.text or "")
                    data["aligns"].append(elem.get("align", "justify"))
                    data["indents_left"].append(elem.get("indent_left", "0"))
                    data["indents_first_line"].append(elem.get("indent_first_line", "0"))
                    data["line_spacings"].append(elem.get("line_spacing", "1.5"))
                    data["paths"].append("")
                    data["captions"].append("")
                    data["font_faces"].append(elem.get("font_face", "Times New Roman"))
                    data["font_sizes"].append(elem.get("font_size", "14"))
                elif elem.tag == "table":
                    rows = [",".join(cell.text or "" for cell in row.findall("cell")) for row in elem.findall("row")]
                    data["contents"].append("\n".join(rows))
                    data["aligns"].append("")
                    data["indents_left"].append("0")
                    data["indents_first_line"].append("0")
                    data["line_spacings"].append("1.5")
                    data["paths"].append("")
                    data["captions"].append("")
                    data["font_faces"].append("")
                    data["font_sizes"].append("")
                elif elem.tag in ["numbered_list", "bullet_list"]:
                    items = [item.text or "" for item in elem.findall("item")]
                    data["contents"].append("\n".join(items))
                    data["aligns"].append("")
                    data["indents_left"].append("0")
                    data["indents_first_line"].append("0")
                    data["line_spacings"].append("1.5")
                    data["paths"].append("")
                    data["captions"].append("")
                    data["font_faces"].append("")
                    data["font_sizes"].append("")
                elif elem.tag == "image":
                    data["contents"].append("")
                    data["aligns"].append("")
                    data["indents_left"].append("0")
                    data["indents_first_line"].append("0")
                    data["line_spacings"].append("1.5")
                    data["paths"].append(elem.get("path", ""))
                    data["captions"].append(elem.get("caption", ""))
                    data["font_faces"].append("")
                    data["font_sizes"].append("")

    if document['template_id']:
        cur.execute('SELECT default_font_face, default_font_size, default_indent_left, default_indent_first_line, default_line_spacing FROM templates WHERE id = %s', (document['template_id'],))
        template = cur.fetchone()
        data.update({
            "default_font_face": template['default_font_face'],
            "default_font_size": template['default_font_size'],
            "default_indent_left": template['default_indent_left'],
            "default_indent_first_line": template['default_indent_first_line'],
            "default_line_spacing": template['default_line_spacing']
        })

    conn.close()
    return data

def generate_preview(docx_path):
    preview_path = os.path.join(PREVIEW_DIR, f"preview_{os.path.basename(docx_path).replace('.docx', '.png')}")
    os.system(f"convert {docx_path}[0] {preview_path}")
    return preview_path

if __name__ == '__main__':
    app.run(debug=True)
