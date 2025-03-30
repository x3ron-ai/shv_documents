from flask import Flask, render_template, request, send_file
from parser import XMLToWordParser
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)

TEMP_XML = "temp.xml"
TEMP_DOCX = "temp.docx"

@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == 'POST':
		blocks = request.form.getlist('block_type[]')
		contents = request.form.getlist('content[]')
		aligns = request.form.getlist('align[]')
		col_widths = request.form.get('col_widths', '2,1,2')
		list_types = request.form.getlist('list_type[]')
		images = request.files.getlist('image[]')

		root = ET.Element("root")
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
					image_path = os.path.join("static", "uploads", image.filename)
					os.makedirs(os.path.dirname(image_path), exist_ok=True)
					image.save(image_path)
					image_elem = ET.SubElement(root, "image")
					image_elem.set("path", image_path)
				image_idx += 1

		xml_str = ET.tostring(root, encoding='utf-8', method='xml', xml_declaration=True)
		print("Generated XML:", xml_str.decode('utf-8'))
		with open(TEMP_XML, 'wb') as f:
			f.write(xml_str)

		parser = XMLToWordParser(TEMP_XML, TEMP_DOCX)
		result = parser.parse_and_convert()

		if "Ошибка" not in result:
			return send_file(TEMP_DOCX, as_attachment=True, download_name="generated_document.docx")
		return f"Ошибка: {result}"

	return render_template('index.html')

@app.teardown_appcontext
def cleanup(exception=None):
	for temp_file in [TEMP_XML, TEMP_DOCX]:
		if os.path.exists(temp_file):
			os.remove(temp_file)

if __name__ == "__main__":
	app.run(debug=True)
