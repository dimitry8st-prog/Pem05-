"""
База данных — SQLite через SQLAlchemy (легко заменить на PostgreSQL).
"""
import os
import json
from datetime import datetime, timezone

from sqlalchemy import (
    create_engine, Column, Integer, String, Text,
    DateTime, Boolean, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from config import config

os.makedirs(config.UPLOAD_DIR, exist_ok=True)

engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False},   # нужно для SQLite
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# ── Модели ────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True)
    telegram_id   = Column(Integer, unique=True, nullable=False, index=True)
    username      = Column(String(128))
    full_name     = Column(String(256))
    language      = Column(String(8), default="ru")
    notify_risks  = Column(Boolean, default=True)   # уведомлять только о высоких рисках
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    contracts_today = Column(Integer, default=0)
    last_activity   = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Contract(Base):
    __tablename__ = "contracts"

    id            = Column(Integer, primary_key=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name     = Column(String(512))
    file_path     = Column(String(512))          # путь к сохранённому файлу
    raw_text      = Column(Text)                 # извлечённый текст
    analysis_json = Column(Text)                 # JSON результата анализа
    summary       = Column(Text)                 # финальный текст для Telegram
    risk_level    = Column(String(16))           # low / medium / high
    recommendation = Column(String(32))          # sign / lawyer / counter_proposal
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_deleted    = Column(Boolean, default=False)

    def get_analysis(self) -> dict:
        return json.loads(self.analysis_json) if self.analysis_json else {}


class FeedbackEntry(Base):
    __tablename__ = "feedback"

    id          = Column(Integer, primary_key=True)
    user_id     = Column(Integer, ForeignKey("users.id"))
    message     = Column(Text)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ── Создание таблиц ───────────────────────────────────────────────────

def init_db() -> None:
    Base.metadata.create_all(bind=engine)


# ── Вспомогательные функции ───────────────────────────────────────────

def get_db() -> Session:
    return SessionLocal()


def get_or_create_user(db: Session, telegram_id: int,
                        username: str = "", full_name: str = "") -> User:
    user = db.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username or "",
            full_name=full_name or "",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.last_activity = datetime.now(timezone.utc)
        if username:
            user.username = username
        db.commit()
    return user


def get_user_contracts(db: Session, user_id: int, limit: int = 20) -> list[Contract]:
    return (
        db.query(Contract)
        .filter_by(user_id=user_id, is_deleted=False)
        .order_by(Contract.created_at.desc())
        .limit(limit)
        .all()
    )
