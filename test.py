import os
import subprocess
import logging

os.remove('test.log')

logging.basicConfig(level=logging.INFO, filename='test.log', format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
PREVIEW_DIR = 'static/previews'
TEMP_DIR = 'uploads'  # Локальная папка для временных файлов
def generate_preview(docx_path):
    print(docx_path)
    safe_filename = docx_path
    print(safe_filename)
    preview_filename = f"preview_{safe_filename.replace('.docx', '.png')}"
    preview_path = os.path.join(PREVIEW_DIR, preview_filename)
    pdf_path = os.path.join(TEMP_DIR, f"{safe_filename.replace('.docx', '.pdf')}")  # Используем локальную папку

    logger.info(f"Генерация PDF из {docx_path} в {pdf_path}")
    try:
        result = subprocess.run(
            ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', TEMP_DIR, docx_path],
            check=True, capture_output=True, text=True
        )
        logger.info(f"PDF успешно создан: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при конвертации DOCX в PDF: {e.stderr}")
        raise

    logger.info(f"Конвертация PDF {pdf_path} в PNG {preview_path}")
    try:
        # Теперь правильный путь для PDF и его конвертация в PNG
        result = subprocess.run(
            ['pdftoppm', pdf_path, preview_path.replace('.png', ''), '-png'],
            check=True, capture_output=True, text=True
        )
        logger.info(f"PNG успешно создан: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при конвертации PDF в PNG: {e.stderr}")
        raise

    return f"previews/{preview_filename}"

if __name__ == "__main__":
    docx_path = "/home/x3ron/diplom/uploads/template_1_123123_2943.docx"
    try:
        result = generate_preview(docx_path)
        print(f"Результат: {result}")
    except Exception as e:
        print(f"Ошибка: {e}")
    print(open('test.log').read())
