import xml.etree.ElementTree as ET
from word_doc_creator import WordDocCreator
import re
from docx.shared import Pt, RGBColor

class XMLToWordParser:
	def __init__(self, xml_file, output_docx="output.docx"):
		self.xml_file = xml_file
		self.output_docx = output_docx
		self.doc = WordDocCreator(output_docx)
		
	def parse_and_convert(self):
		try:
			with open(self.xml_file, 'r', encoding='utf-8') as f:
				xml_content = f.read().strip()
			root = ET.fromstring(xml_content)
			
			for element in root:
				self._process_element(element)
				
			return self.doc.save()
			
		except ET.ParseError as e:
			return f"Ошибка парсинга XML: {str(e)}"
		except FileNotFoundError:
			return f"Файл {self.xml_file} не найден"
		except Exception as e:
			return f"Ошибка: {str(e)}"
	
	def _process_element(self, element):
		if element.tag == "text":
			self._add_text(element)
		elif element.tag == "table":
			self._add_table(element)
		elif element.tag == "list":
			self._add_list(element)
		elif element.tag == "image":
			self._add_image(element)

	def _add_text(self, text_element):
		text = text_element.text.strip() if text_element.text else ""
		alignment = text_element.get("align", "left")
		if text:
			paragraph = self.doc.document.add_paragraph()
			paragraph.alignment = {
				"left": 0, "center": 1, "right": 2, "justify": 3
			}.get(alignment.lower(), 0)
			
			parts = re.split(r'(<[^>]+>)', text)
			current_run = None
			bold = False
			font_size = 12
			font_name = "Arial"
			font_color = (0, 0, 0)

			for part in parts:
				if part.startswith('<') and part.endswith('>'):
					if part == '<b>':
						bold = True
					elif part == '</b>':
						bold = False
					elif part.startswith('<font'):
						attrs = re.findall(r'(\w+)="([^"]+)"', part)
						for attr, value in attrs:
							if attr == "size":
								font_size = int(value)
							elif attr == "face":
								font_name = value
							elif attr == "color":
								# Ожидаем HEX-цвет в формате "RRGGBB"
								font_color = tuple(int(value[i:i+2], 16) for i in (0, 2, 4))
					elif part == '</font>':
						font_size = 12
						font_name = "Arial"
						font_color = (0, 0, 0)
				else:
					if part.strip():
						current_run = paragraph.add_run(part)
						current_run.font.bold = bold
						current_run.font.size = Pt(font_size)
						current_run.font.name = font_name
						current_run.font.color.rgb = RGBColor(*font_color)
	
	def _add_table(self, table_element):
		rows = []
		for row in table_element.findall("row"):
			cells = [cell.text.strip() if cell.text else "" for cell in row.findall("cell")]
			if cells:
				rows.append(cells)
		if rows:
			col_widths = table_element.get("col_widths")
			if col_widths:
				col_widths = [float(w) for w in col_widths.split(",")]
			self.doc.add_table(rows, col_widths=col_widths)

	def _add_list(self, list_element):
		items = [item.text.strip() for item in list_element.findall("item") if item.text]
		if items:
			list_type = list_element.get("type", "bullet")
			if list_type == "numbered":
				self.doc.add_numbered_list(items)
			else:
				self.doc.add_bullet_list(items)

	def _add_image(self, image_element):
		path = image_element.get("path")
		if path:
			self.doc.add_picture(path)
