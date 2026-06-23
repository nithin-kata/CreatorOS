import io
import logging

logger = logging.getLogger(__name__)

def extract_text_from_file(file_stream, filename):
    ext = filename.split('.')[-1].lower()
    if ext in ['txt', 'md', 'csv', 'json', 'xml', 'html']:
        return file_stream.read().decode('utf-8', errors='ignore')
    elif ext == 'pdf':
        try:
            import pypdf
            pdf_bytes = file_stream.read()
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            return f"[Error parsing PDF content: {e}]"
    elif ext == 'docx':
        try:
            import docx
            doc_bytes = file_stream.read()
            doc = docx.Document(io.BytesIO(doc_bytes))
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return "\n".join(text)
        except Exception as e:
            logger.error(f"Error parsing DOCX: {e}")
            return f"[Error parsing DOCX content: {e}]"
    else:
        try:
            return file_stream.read().decode('utf-8', errors='ignore')
        except Exception:
            return ""
