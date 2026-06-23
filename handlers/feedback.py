"""
Обработчик /feedback.
"""
from telegram import Update
from telegram.ext import ContextTypes

from database import get_db, get_or_create_user, FeedbackEntry
from utils.keyboards import cancel_kb, main_menu_kb

AWAITING_FEEDBACK = "awaiting_feedback"


async def feedback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[AWAITING_FEEDBACK] = True
    await update.message.reply_text(
        "✍️ Напишите ваш отзыв или опишите проблему — я передам команде.",
        reply_markup=cancel_kb(),
    )


async def feedback_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get(AWAITING_FEEDBACK):
        await update.message.reply_text(
            "📄 Пришлите PDF или фото договора для анализа.\n"
            "Или используйте /help для справки.",
            reply_markup=main_menu_kb(),
        )
        return

    context.user_data[AWAITING_FEEDBACK] = False
    user = update.effective_user
    db   = get_db()
    try:
        db_user = get_or_create_user(db, user.id)
        entry   = FeedbackEntry(user_id=db_user.id, message=update.message.text)
        db.add(entry)
        db.commit()
    finally:
        db.close()

    await update.message.reply_text(
        "✅ Спасибо! Ваш отзыв сохранён.",
        reply_markup=main_menu_kb(),
    )
