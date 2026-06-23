"""
Сервис извлечения текста из PDF и изображений.
"""
import io
import logging
import os

logger = logging.getLogger(__name__)


def extract_from_pdf(file_bytes: bytes) -> str:
    """Извлекает текст из PDF через pdfplumber."""
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        text = "\n\n".join(text_parts).strip()
        if text:
            return text
    except Exception as e:
        logger.warning("pdfplumber не смог извлечь текст: %s", e)

    # Фолбэк на PyPDF2
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
        return "\n\n".join(text_parts).strip()
    except Exception as e:
        logger.error("PyPDF2 тоже не смог: %s", e)
        return ""


def extract_from_image(file_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """
    OCR через Claude Vision API.
    Модель видит изображение и возвращает распознанный текст.
    """
    import anthropic
    import base64
    from config import config

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    b64 = base64.standard_b64encode(file_bytes).decode()

    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": b64,
                    },
                },
                {
                    "type": "text",
                    "text": (
                        "Это скан или фото юридического документа. "
                        "Извлеки весь текст дословно, сохраняя структуру и нумерацию пунктов. "
                        "Не добавляй пояснений — только текст документа."
                    ),
                },
            ],
        }],
    )
    return response.content[0].text


def extract_text(file_bytes: bytes, file_name: str = "") -> str:
    """
    Универсальный экстрактор: определяет тип по расширению.
    """
    ext = os.path.splitext(file_name.lower())[1] if file_name else ""

    if ext == ".pdf":
        text = extract_from_pdf(file_bytes)
        if not text:
            # Попробуем как изображение (скан-PDF)
            logger.info("PDF пустой — пробуем OCR через Vision")
            text = extract_from_image(file_bytes, "image/jpeg")
        return text

    if ext in (".jpg", ".jpeg"):
        return extract_from_image(file_bytes, "image/jpeg")
    if ext == ".png":
        return extract_from_image(file_bytes, "image/png")
    if ext in (".webp",):
        return extract_from_image(file_bytes, "image/webp")

    # Неизвестный тип — пробуем PDF
    return extract_from_pdf(file_bytes)
