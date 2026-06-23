"""
Главный роутер callback-запросов от inline-кнопок.
"""
import logging

from telegram import Update
from telegram.ext import ContextTypes

from database import get_db, get_or_create_user, Contract, get_user_contracts
from utils.keyboards import main_menu_kb, after_analysis_kb, history_kb
from utils.formatting import format_full_report, short_summary
from handlers.start import WELCOME_TEXT, HELP_TEXT

logger = logging.getLogger(__name__)


async def main_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data  = query.data
    user  = query.from_user

    # ── Главное меню ─────────────────────────────────────────────────
    if data == "main_menu":
        await query.edit_message_text(
            WELCOME_TEXT.format(name=user.first_name or "коллега"),
            parse_mode="Markdown",
            reply_markup=main_menu_kb(),
        )
        return

    if data == "help":
        await query.edit_message_text(
            HELP_TEXT, parse_mode="Markdown", reply_markup=main_menu_kb()
        )
        return

    if data == "upload_hint":
        await query.edit_message_text(
            "📎 Просто пришлите *PDF* или *фото договора* — я сразу начну анализ.",
            parse_mode="Markdown",
            reply_markup=main_menu_kb(),
        )
        return

    # ── История ──────────────────────────────────────────────────────
    if data == "history":
        db = get_db()
        try:
            db_user   = get_or_create_user(db, user.id)
            contracts = get_user_contracts(db, db_user.id, limit=20)
            if not contracts:
                await query.edit_message_text(
                    "📂 История пуста.\nПришлите договор для анализа.",
                    reply_markup=main_menu_kb(),
                )
                return
            lines = ["📊 *Ваши последние договоры:*\n"]
            for i, c in enumerate(contracts, 1):
                from utils.formatting import RISK_EMOJI
                emoji = RISK_EMOJI.get(c.risk_level, "🟢")
                date  = c.created_at.strftime("%d.%m.%Y")
                lines.append(f"{i}. {emoji} {c.file_name[:35]} _({date})_")
            await query.edit_message_text(
                "\n".join(lines),
                parse_mode="Markdown",
                reply_markup=history_kb(contracts),
            )
        finally:
            db.close()
        return

    # ── Краткая выжимка ───────────────────────────────────────────────
    if data.startswith("short_"):
        contract_id = int(data.split("_", 1)[1])
        db = get_db()
        try:
            contract = db.query(Contract).filter_by(id=contract_id).first()
            if not contract:
                await query.edit_message_text("❌ Договор не найден.")
                return
            text = short_summary(contract)
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=after_analysis_kb(contract_id),
            )
        finally:
            db.close()
        return

    # ── Полный отчёт ─────────────────────────────────────────────────
    if data.startswith("full_"):
        contract_id = int(data.split("_", 1)[1])
        db = get_db()
        try:
            contract = db.query(Contract).filter_by(id=contract_id).first()
            if not contract:
                await query.edit_message_text("❌ Договор не найден.")
                return
            text = format_full_report(contract)
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=after_analysis_kb(contract_id),
            )
        finally:
            db.close()
        return

    # ── Вопрос по договору ───────────────────────────────────────────
    if data.startswith("ask_"):
        contract_id = int(data.split("_", 1)[1])
        context.user_data["ask_contract_id"] = contract_id
        await query.edit_message_text(
            "❓ Задайте любой вопрос по этому договору — я отвечу на основе его текста.\n\n"
            "_Например: «Какой штраф за просрочку?» или «Кто отвечает за обновления?»_",
            parse_mode="Markdown",
            reply_markup=main_menu_kb(),
        )
        return

    logger.warning("Неизвестный callback: %s", data)
