"""
Конфигурация бота. Все секреты — через переменные окружения.
Скопируйте .env.example в .env и заполните свои значения.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # ── Обязательные ────────────────────────────────────────────────
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # ── База данных ──────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///contract_wizard.db")

    # ── Хранилище файлов ─────────────────────────────────────────────
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")

    # ── Лимиты ──────────────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
    FREE_DAILY_LIMIT: int = int(os.getenv("FREE_DAILY_LIMIT", "10"))

    # ── Модель Claude ────────────────────────────────────────────────
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))

    def validate(self) -> None:
        if not self.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN не задан в .env")
        if not self.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY не задан в .env")


config = Config()
