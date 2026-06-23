"""
Обработчики /start и /help.
"""
from telegram import Update
from telegram.ext import ContextTypes

from database import get_db, get_or_create_user
from utils.keyboards import main_menu_kb

WELCOME_TEXT = """👋 Привет, {name}!

Я *Contract Wizard* — ваш ИИ-помощник по договорам 🧙‍♂️

Умею за *3–5 минут*:
  ✅ Выделить стороны, сумму, сроки и ответственность
  ⚠️ Найти «красные флаги» и нестандартные пункты
  📋 Дать чёткую рекомендацию: подписывать или нет

*Просто пришлите PDF или фото договора* — и я сразу приступлю.
"""

HELP_TEXT = """📖 *Справка Contract Wizard*

*Команды:*
  /start — главное меню
  /history — последние 20 договоров
  /settings — настройки уведомлений
  /feedback — написать отзыв или сообщить об ошибке
  /help — эта справка

*Форматы файлов:*
  • PDF (текстовый или скан)
  • Фото / скриншот договора (JPG, PNG)

*Как работает анализ:*
  1️⃣ Извлечение текста из документа
  2️⃣ Структурный разбор по 5 блокам
  3️⃣ Проверка на противоречия
  4️⃣ Готовая выжимка с рекомендацией

*Лимиты (бесплатный план):*
  • до 10 договоров в день
  • файлы до 20 МБ

❓ Вопросы? /feedback
"""


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db = get_db()
    try:
        get_or_create_user(
            db,
            telegram_id=user.id,
            username=user.username or "",
            full_name=user.full_name or "",
        )
    finally:
        db.close()

    await update.message.reply_text(
        WELCOME_TEXT.format(name=user.first_name or "коллега"),
        parse_mode="Markdown",
        reply_markup=main_menu_kb(),
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode="Markdown",
        reply_markup=main_menu_kb(),
    )
