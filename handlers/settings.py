"""
Обработчик /settings.
"""
from telegram import Update
from telegram.ext import ContextTypes

from database import get_db, get_or_create_user
from utils.keyboards import settings_kb


async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db   = get_db()
    try:
        db_user = get_or_create_user(db, user.id)
        await update.message.reply_text(
            "⚙️ *Настройки*\n\n"
            f"👤 Аккаунт: @{db_user.username or 'без username'}\n"
            f"📋 Договоров сегодня: {db_user.contracts_today}",
            parse_mode="Markdown",
            reply_markup=settings_kb(db_user.notify_risks),
        )
    finally:
        db.close()


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "settings_toggle_notify":
        user = query.from_user
        db   = get_db()
        try:
            db_user = get_or_create_user(db, user.id)
            db_user.notify_risks = not db_user.notify_risks
            db.commit()
            await query.edit_message_reply_markup(
                reply_markup=settings_kb(db_user.notify_risks)
            )
        finally:
            db.close()
