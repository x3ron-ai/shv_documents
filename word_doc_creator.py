from docx import Document
from docx.oxml.ns import qn
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_BREAK
from docx.shared import Pt, RGBColor, Inches
import os

class WordDocCreator:
	def __init__(self, filename="document.docx"):
		self.document = Document()
		self.filename = filename

	def add_paragraph(self, text, alignment="left", font_size=12, bold=False, italic=False, 
					 font_name="Arial", color=(0, 0, 0)):
		paragraph = self.document.add_paragraph()
		run = paragraph.add_run(text)
		alignments = {
			"left": WD_PARAGRAPH_ALIGNMENT.LEFT,
			"center": WD_PARAGRAPH_ALIGNMENT.CENTER,
			"right": WD_PARAGRAPH_ALIGNMENT.RIGHT,
			"justify": WD_PARAGRAPH_ALIGNMENT.JUSTIFY
		}
		paragraph.alignment = alignments.get(alignment.lower(), WD_PARAGRAPH_ALIGNMENT.LEFT)
		run.font.size = Pt(font_size)
		run.font.bold = bold
		run.font.italic = italic
		run.font.name = font_name
		run.font.color.rgb = RGBColor(*color)
		return paragraph

	def add_numbered_list(self, items, start=1):
		for i, item in enumerate(items, start):
			paragraph = self.document.add_paragraph(f"{i}. {item}")
			paragraph.style = 'List Number'
		return paragraph

	def add_bullet_list(self, items):
		for item in items:
			paragraph = self.document.add_paragraph(item)
			paragraph.style = 'List Bullet'
		return paragraph

	def add_table(self, data, col_widths=None):
		rows = len(data)
		cols = len(data[0]) if data else 0
		if rows == 0 or cols == 0:
			return None
		table = self.document.add_table(rows=rows, cols=cols)
		table.style = 'Table Grid'
		if col_widths and len(col_widths) == cols:
			for i, width in enumerate(col_widths):
				for cell in table.columns[i].cells:
					cell.width = Inches(width)
		for i, row in enumerate(data):
			for j, value in enumerate(row):
				table.rows[i].cells[j].text = str(value)
		return table

	def add_picture(self, image_path, width=None, height=None):
		if not os.path.exists(image_path):
			raise FileNotFoundError(f"Файл изображения {image_path} не найден")
		if width and height:
			self.document.add_picture(image_path, width=Inches(width), height=Inches(height))
		elif width:
			self.document.add_picture(image_path, width=Inches(width))
		elif height:
			self.document.add_picture(image_path, height=Inches(height))
		else:
			self.document.add_picture(image_path)
		return self.document.paragraphs[-1]

	def save(self):
		try:
			self.document.save(self.filename)
			return f"Документ сохранен как {os.path.abspath(self.filename)}"
		except Exception as e:
			return f"Ошибка при сохранении: {str(e)}"
