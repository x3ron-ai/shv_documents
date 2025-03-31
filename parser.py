import xml.etree.ElementTree as ET
from word_doc_creator import WordDocCreator
import re
from docx.shared import Pt, RGBColor
from docx import Document
import os

class XMLToWordParser:
    def __init__(self, xml_file, output_docx="output.docx", title_page_path=None):
        self.xml_file = xml_file
        self.output_docx = output_docx
        self.title_page_path = title_page_path
        if self.title_page_path and os.path.exists(self.title_page_path):
            self.doc = WordDocCreator(output_docx, base_doc=Document(self.title_page_path))
        else:
            self.doc = WordDocCreator(output_docx)
        
    def parse_and_convert(self):
        try:
            with open(self.xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read().strip()
            root = ET.fromstring(xml_content)
            
            # Извлекаем отступы из XML
            self.indent_left = float(root.get("indent_left", "0"))
            self.indent_first_line = float(root.get("indent_first_line", "0"))  # По умолчанию 0, а не 1.5
            self.line_spacing = float(root.get("line_spacing", "1.5"))
            
            # Отладочный вывод
            print(f"Parser: Indent left: {self.indent_left}, First line: {self.indent_first_line}, Line spacing: {self.line_spacing}")
            
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
            paragraph = self.doc.add_paragraph(
                text, 
                alignment=alignment, 
                indent_left=self.indent_left, 
                indent_first_line=self.indent_first_line, 
                line_spacing=self.line_spacing
            )
            parts = re.split(r'(<[^>]+>)', text)
            paragraph.clear()  # Очищаем параграф для корректной вставки форматированного текста
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
                self.doc.add_numbered_list(items, indent_left=self.indent_left, indent_first_line=self.indent_first_line, line_spacing=self.line_spacing)
            else:
                self.doc.add_bullet_list(items, indent_left=self.indent_left, indent_first_line=self.indent_first_line, line_spacing=self.line_spacing)

    def _add_image(self, image_element):
        path = image_element.get("path")
        caption = image_element.get("caption")
        if path:
            self.doc.add_picture(path, align="center")
            if caption:
                bold = image_element.get("caption_bold", "false") == "true"
                size = int(image_element.get("caption_size", "12"))
                face = image_element.get("caption_face", "Times New Roman")
                color = image_element.get("caption_color", "000000")
                color_rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                self.doc.add_caption(caption, "Рисунок", bold, size, face, color_rgb)
