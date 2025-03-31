from flask import Flask, render_template, request, send_file, redirect, url_for
from parser import XMLToWordParser
import xml.etree.ElementTree as ET
import os
import uuid
import glob
from docx import Document

app = Flask(__name__)

TEMP_XML = "temp.xml"
TEMP_DOCX = "temp.docx"
UPLOADS_DIR = "static/uploads"
TEMPLATES_DIR = "templates"

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    templates = [os.path.basename(f) for f in glob.glob(os.path.join(TEMPLATES_DIR, "*.xml"))]
    return render_template('index.html', templates=templates)

@app.route('/upload_image', methods=['POST'])
def upload_image():
    image = request.files.get('image')
    if image:
        unique_filename = f"{uuid.uuid4()}{os.path.splitext(image.filename)[1]}"
        image_path = os.path.join(UPLOADS_DIR, unique_filename)
        image.save(image_path)
        return {"path": image_path}
    return {"error": "No image uploaded"}, 400

@app.route('/create', methods=['GET', 'POST'])
def create_document():
    if request.method == 'POST':
        blocks = request.form.getlist('block_type[]')
        contents = request.form.getlist('content[]')
        aligns = request.form.getlist('align[]')
        col_widths = request.form.get('col_widths', '2,1,2')
        list_types = request.form.getlist('list_type[]')
        images = request.files.getlist('image[]')
        image_captions = request.form.getlist('image_caption[]')
        caption_bolds = request.form.getlist('caption_bold[]')
        caption_sizes = request.form.getlist('caption_size[]')
        caption_faces = request.form.getlist('caption_face[]')
        caption_colors = request.form.getlist('caption_color[]')
        title_page = request.files.get('title_page')
        indent_left = request.form.get('indent_left', '0')
        indent_first_line = request.form.get('indent_first_line', '0')
        line_spacing = request.form.get('line_spacing', '1.5')

        root = ET.Element("root")
        root.set("indent_left", indent_left)
        root.set("indent_first_line", indent_first_line)
        root.set("line_spacing", line_spacing)
        
        content_idx = 0
        image_idx = 0

        for block in blocks:
            if block == "text" and content_idx < len(contents):
                text_elem = ET.SubElement(root, "text")
                text_elem.text = contents[content_idx]
                text_elem.set("align", aligns[content_idx] if content_idx < len(aligns) else "left")
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
            elif block == "image" and image_idx < len(images):
                image = images[image_idx]
                if image:
                    unique_filename = f"{uuid.uuid4()}{os.path.splitext(image.filename)[1]}"
                    image_path = os.path.join(UPLOADS_DIR, unique_filename)
                    image.save(image_path)
                    image_elem = ET.SubElement(root, "image")
                    image_elem.set("path", image_path)
                    if image_idx < len(image_captions) and image_captions[image_idx].strip():
                        image_elem.set("caption", image_captions[image_idx])
                        image_elem.set("caption_bold", "true" if image_idx < len(caption_bolds) and caption_bolds[image_idx] == "on" else "false")
                        image_elem.set("caption_size", caption_sizes[image_idx] if image_idx < len(caption_sizes) else "12")
                        image_elem.set("caption_face", caption_faces[image_idx] if image_idx < len(caption_faces) else "Times New Roman")
                        image_elem.set("caption_color", caption_colors[image_idx].lstrip('#') if image_idx < len(caption_colors) else "000000")
                image_idx += 1

        template_id = uuid.uuid4().hex
        template_path = os.path.join(TEMPLATES_DIR, f"{template_id}.xml")
        xml_str = ET.tostring(root, encoding='utf-8', method='xml', xml_declaration=True)
        with open(template_path, 'wb') as f:
            f.write(xml_str)

        if 'generate' in request.form:
            title_page_path = None
            if title_page and title_page.filename.endswith('.docx'):
                unique_title_filename = f"{uuid.uuid4()}.docx"
                title_page_path = os.path.join(UPLOADS_DIR, unique_title_filename)
                title_page.save(title_page_path)

            parser = XMLToWordParser(template_path, TEMP_DOCX, title_page_path)
            result = parser.parse_and_convert()

            if "Ошибка" not in result:
                return send_file(TEMP_DOCX, as_attachment=True, download_name=f"document_{template_id}.docx")
            return f"Ошибка: {result}"

    return render_template('create.html')

@app.route('/document/<template_id>', methods=['GET', 'POST'])
def edit_document(template_id):
    template_path = os.path.join(TEMPLATES_DIR, f"{template_id}.xml")
    if not os.path.exists(template_path):
        return "Шаблон не найден", 404

    if request.method == 'POST':
        blocks = request.form.getlist('block_type[]')
        contents = request.form.getlist('content[]')
        aligns = request.form.getlist('align[]')
        col_widths = request.form.get('col_widths', '2,1,2')
        list_types = request.form.getlist('list_type[]')
        images = request.files.getlist('image[]')
        image_paths = request.form.getlist('image_path[]')
        image_captions = request.form.getlist('image_caption[]')
        caption_bolds = request.form.getlist('caption_bold[]')
        caption_sizes = request.form.getlist('caption_size[]')
        caption_faces = request.form.getlist('caption_face[]')
        caption_colors = request.form.getlist('caption_color[]')
        title_page = request.files.get('title_page')
        indent_left = request.form.get('indent_left', '0')
        indent_first_line = request.form.get('indent_first_line', '0')
        line_spacing = request.form.get('line_spacing', '1.5')

        root = ET.Element("root")
        
        content_idx = 0
        image_idx = 0

        for block in blocks:
            if block == "text" and content_idx < len(contents):
                text_elem = ET.SubElement(root, "text")
                text_elem.text = contents[content_idx]
                text_elem.set("align", aligns[content_idx] if content_idx < len(aligns) else "left")
                text_elem.set("indent_left", indent_left)
                text_elem.set("indent_first_line", indent_first_line)
                text_elem.set("line_spacing", line_spacing)
                font_face = request.form.get(f'face_block_{content_idx}', 'Times New Roman')
                text_elem.set("font_face", font_face)
                font_size = request.form.get(f'size_block_{content_idx}', '14')  # Новый атрибут
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
                list_elem.set("indent_left", indent_left)
                list_elem.set("indent_first_line", indent_first_line)
                list_elem.set("line_spacing", line_spacing)
                items = contents[content_idx].split('\n')
                for item in items:
                    if item.strip():
                        item_elem = ET.SubElement(list_elem, "item")
                        item_elem.text = item.strip()
                content_idx += 1
            elif block == "image" and image_idx < len(image_paths):
                image_elem = ET.SubElement(root, "image")
                if image_idx < len(images) and images[image_idx]:
                    unique_filename = f"{uuid.uuid4()}{os.path.splitext(images[image_idx].filename)[1]}"
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
        with open(template_path, 'wb') as f:
            f.write(xml_str)

        if 'generate' in request.form:
            title_page_path = None
            if title_page and title_page.filename.endswith('.docx'):
                unique_title_filename = f"{uuid.uuid4()}.docx"
                title_page_path = os.path.join(UPLOADS_DIR, unique_title_filename)
                title_page.save(title_page_path)

            parser = XMLToWordParser(template_path, TEMP_DOCX, title_page_path)
            result = parser.parse_and_convert()

            if "Ошибка" not in result:
                return send_file(TEMP_DOCX, as_attachment=True, download_name=f"document_{template_id}.docx")
            return f"Ошибка: {result}"

        return "", 204

    return render_template('edit.html', template_id=template_id, template_path=template_path)

@app.route('/get_template/<template_id>')
def get_template(template_id):
    template_path = os.path.join(TEMPLATES_DIR, f"{template_id}.xml")
    if not os.path.exists(template_path):
        return "Шаблон не найден", 404

    with open(template_path, 'r', encoding='utf-8') as f:
        root = ET.fromstring(f.read())
    
    data = {
        "blocks": [],
        "contents": [],
        "aligns": [],
        "paths": [],
        "captions": [],
        "indents_left": [],
        "indents_first_line": [],
        "line_spacings": [],
        "font_faces": [],
        "font_sizes": [],
        "col_widths": "2,1,2"
    }
    
    for elem in root:
        data["blocks"].append(elem.tag)
        if elem.tag == "text":
            data["contents"].append(elem.text or "")
            data["aligns"].append(elem.get("align", "left"))
            data["paths"].append("")
            data["captions"].append("")
            data["indents_left"].append(elem.get("indent_left", "0"))
            data["indents_first_line"].append(elem.get("indent_first_line", "0"))
            data["line_spacings"].append(elem.get("line_spacing", "1.5"))
            data["font_faces"].append(elem.get("font_face", "Times New Roman"))
            data["font_sizes"].append(elem.get("font_size", "14"))
        elif elem.tag == "table":
            rows = [",".join(cell.text or "" for cell in row.findall("cell")) for row in elem.findall("row")]
            data["contents"].append("\n".join(rows))
            data["aligns"].append("")
            data["paths"].append("")
            data["captions"].append("")
            data["indents_left"].append("0")
            data["indents_first_line"].append("0")
            data["line_spacings"].append("1.5")
            data["font_faces"].append("")
            data["font_sizes"].append("")
        elif elem.tag in ["numbered_list", "bullet_list"]:
            items = [item.text or "" for item in elem.findall("item")]
            data["contents"].append("\n".join(items))
            data["aligns"].append("")
            data["paths"].append("")
            data["captions"].append("")
            data["indents_left"].append(elem.get("indent_left", "0"))
            data["indents_first_line"].append(elem.get("indent_first_line", "0"))
            data["line_spacings"].append(elem.get("line_spacing", "1.5"))
            data["font_faces"].append("")
            data["font_sizes"].append("")
        elif elem.tag == "image":
            data["contents"].append("")
            data["aligns"].append("")
            data["paths"].append(elem.get("path", ""))
            data["captions"].append(elem.get("caption", ""))
            data["indents_left"].append("0")
            data["indents_first_line"].append("0")
            data["line_spacings"].append("1.5")
            data["font_faces"].append("")
            data["font_sizes"].append("")

    return data

@app.teardown_appcontext
def cleanup(exception=None):
    for temp_file in [TEMP_XML, TEMP_DOCX]:
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == "__main__":
    app.run(debug=True)
