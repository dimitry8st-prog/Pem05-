"""
Обработчик /history — история договоров пользователя.
"""
from telegram import Update
from telegram.ext import ContextTypes

from database import get_db, get_or_create_user, get_user_contracts
from utils.keyboards import history_kb, main_menu_kb
from utils.formatting import RISK_EMOJI, RISK_LABEL


async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db   = get_db()
    try:
        db_user   = get_or_create_user(db, user.id)
        contracts = get_user_contracts(db, db_user.id, limit=20)

        if not contracts:
            await update.message.reply_text(
                "📂 История пуста.\n\nПришлите договор — и он появится здесь.",
                reply_markup=main_menu_kb(),
            )
            return

        lines = ["📊 *Ваши последние договоры:*\n"]
        for i, c in enumerate(contracts, 1):
            emoji = RISK_EMOJI.get(c.risk_level, "🟢")
            date  = c.created_at.strftime("%d.%m.%Y")
            lines.append(f"{i}. {emoji} {c.file_name[:35]} _({date})_")

        await update.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=history_kb(contracts),
        )
    finally:
        db.close()
