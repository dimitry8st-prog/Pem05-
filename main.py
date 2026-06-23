"""
Contract Wizard Bot — главный модуль запуска.
"""
import logging
import asyncio
import sys

# Фикс для Windows + Python 3.12: предотвращает конфликт event loop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)

from config import config
from handlers.start     import start_handler, help_handler
from handlers.document  import document_handler
from handlers.history   import history_handler
from handlers.settings  import settings_handler, settings_callback
from handlers.feedback  import feedback_handler, feedback_text_handler
from handlers.callbacks import main_callback_handler

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def build_app() -> Application:
    app = Application.builder().token(config.TELEGRAM_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start",    start_handler))
    app.add_handler(CommandHandler("help",     help_handler))
    app.add_handler(CommandHandler("history",  history_handler))
    app.add_handler(CommandHandler("settings", settings_handler))
    app.add_handler(CommandHandler("feedback", feedback_handler))

    # Документы и фото
    app.add_handler(MessageHandler(filters.Document.PDF, document_handler))
    app.add_handler(MessageHandler(filters.PHOTO,        document_handler))

    # Inline-кнопки
    app.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings_"))
    app.add_handler(CallbackQueryHandler(main_callback_handler))

    # Текст после /feedback
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, feedback_text_handler
    ))

    return app


def main() -> None:
    logger.info("🚀 Contract Wizard Bot запускается...")
    app = build_app()
    # run_polling сам управляет event loop — asyncio.run() здесь не нужен
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
