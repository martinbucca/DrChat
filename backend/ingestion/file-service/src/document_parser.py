from PyPDF2 import PdfReader
import io

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() or ""
    return full_text.strip()
