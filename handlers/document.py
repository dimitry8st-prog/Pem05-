"""
Обработчик входящих документов и фото — основной сценарий бота.
"""
import json
import logging
import os
from datetime import datetime, timezone

from telegram import Update, Message
from telegram.ext import ContextTypes

from config import config
from database import get_db, get_or_create_user, Contract
from services.extractor import extract_text
from services.claude_service import full_pipeline
from utils.keyboards import after_analysis_kb
from utils.formatting import RISK_EMOJI, REC_LABEL

logger = logging.getLogger(__name__)


async def _send_progress(message: Message, step: str) -> Message:
    """Отправить / обновить сообщение о прогрессе."""
    steps = {
        "downloading": "⏳ Получаю файл...",
        "extracting":  "🔍 Извлекаю текст из документа...",
        "analyzing":   "🧠 Анализирую договор (шаг 1/3)...",
        "validating":  "✅ Проверяю на противоречия (шаг 2/3)...",
        "summarizing": "📝 Формирую выжимку (шаг 3/3)...",
    }
    return await message.edit_text(steps.get(step, "⏳ Обрабатываю..."))


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    msg  = update.message

    # ── Проверка лимита ──────────────────────────────────────────────
    db = get_db()
    try:
        db_user = get_or_create_user(db, user.id, user.username or "", user.full_name or "")

        # Сброс счётчика если новый день
        last = db_user.last_activity
        now  = datetime.now(timezone.utc)
        if last.date() < now.date():
            db_user.contracts_today = 0

        if db_user.contracts_today >= config.FREE_DAILY_LIMIT:
            await msg.reply_text(
                f"⛔ Вы достигли лимита *{config.FREE_DAILY_LIMIT} договоров в день*.\n"
                "Лимит сбросится завтра.",
                parse_mode="Markdown",
            )
            return
    finally:
        db.close()

    # ── Определяем файл или фото ─────────────────────────────────────
    is_photo = bool(msg.photo)
    if is_photo:
        tg_file = await msg.photo[-1].get_file()
        file_name = f"photo_{user.id}_{int(now.timestamp())}.jpg"
    else:
        doc = msg.document
        file_name = doc.file_name or "document.pdf"
        if doc.file_size > config.MAX_FILE_SIZE_MB * 1024 * 1024:
            await msg.reply_text(
                f"⛔ Файл слишком большой. Максимум — *{config.MAX_FILE_SIZE_MB} МБ*.",
                parse_mode="Markdown",
            )
            return
        tg_file = await doc.get_file()

    # ── Прогресс ─────────────────────────────────────────────────────
    progress_msg = await msg.reply_text("⏳ Получаю файл...")

    try:
        # 1. Скачиваем
        file_bytes = await tg_file.download_as_bytearray()
        file_bytes = bytes(file_bytes)

        # Сохраняем на диск
        save_path = os.path.join(config.UPLOAD_DIR, f"{user.id}_{file_name}")
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        await _send_progress(progress_msg, "extracting")

        # 2. Извлечение текста
        text = extract_text(file_bytes, file_name)
        if not text or len(text.strip()) < 50:
            await progress_msg.edit_text(
                "❌ Не удалось извлечь текст из документа.\n\n"
                "Попробуйте:\n"
                "• Прислать более чёткое фото\n"
                "• Убедиться, что PDF не защищён паролем\n"
                "• Прислать текстовый (не сканированный) PDF"
            )
            return

        await _send_progress(progress_msg, "analyzing")

        # 3. Полный пайплайн Claude
        analysis, validation, summary = full_pipeline(text)

        await _send_progress(progress_msg, "summarizing")

        # Обогащаем analysis данными валидации для хранения
        analysis["_validation"] = validation

        # Определяем уровень риска из анализа
        flags = analysis.get("red_flags", [])
        if any(f.get("severity") == "high" for f in flags):
            risk_level = "high"
        elif any(f.get("severity") == "medium" for f in flags):
            risk_level = "medium"
        else:
            risk_level = "low"

        # 4. Сохраняем в БД
        db = get_db()
        try:
            db_user = get_or_create_user(db, user.id)
            contract = Contract(
                user_id        = db_user.id,
                file_name      = file_name,
                file_path      = save_path,
                raw_text       = text[:10_000],
                analysis_json  = json.dumps(analysis, ensure_ascii=False),
                summary        = summary,
                risk_level     = risk_level,
                recommendation = analysis.get("recommendation", "lawyer"),
            )
            db.add(contract)
            db_user.contracts_today += 1
            db_user.last_activity = datetime.now(timezone.utc)
            db.commit()
            db.refresh(contract)
            contract_id = contract.id
        finally:
            db.close()

        # 5. Отправляем результат
        await progress_msg.delete()
        await msg.reply_text(
            summary,
            parse_mode="Markdown",
            reply_markup=after_analysis_kb(contract_id),
        )

        # Дополнительное предупреждение если валидация нашла проблемы
        if not validation.get("valid", True):
            issues = validation.get("issues", [])
            if issues:
                issues_text = "\n".join(f"  ⛔ {i}" for i in issues)
                await msg.reply_text(
                    f"🚨 *Дополнительно выявлены противоречия:*\n{issues_text}",
                    parse_mode="Markdown",
                )

    except Exception as e:
        logger.exception("Ошибка при обработке документа: %s", e)
        await progress_msg.edit_text(
            "❌ Произошла ошибка при анализе.\n\n"
            "Пожалуйста, попробуйте ещё раз или напишите /feedback."
        )
