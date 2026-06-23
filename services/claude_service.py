"""
Сервис взаимодействия с Claude API.
"""
import json
import logging
import re

import anthropic

from config import config
from prompts import (
    SYSTEM_ANALYZE, PROMPT_ANALYZE,
    SYSTEM_VALIDATE, PROMPT_VALIDATE,
    SYSTEM_SUMMARY, PROMPT_SUMMARY,
)

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def _call_claude(system: str, user: str) -> str:
    """Базовый вызов Claude API."""
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=config.MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def _parse_json(raw: str) -> dict:
    """Вытащить JSON из ответа модели (на случай если обернут в ```json```)."""
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
    if match:
        raw = match.group(1).strip()
    return json.loads(raw)


def analyze_contract(text: str) -> dict:
    """
    Шаг 1 — структурный разбор.
    Возвращает dict с полями: type, parties, subject, amount, dates,
    liability, red_flags, recommendation, questions.
    """
    prompt = PROMPT_ANALYZE.format(text=text[:12_000])   # обрезаем очень длинные тексты
    raw = _call_claude(SYSTEM_ANALYZE, prompt)
    return _parse_json(raw)


def validate_analysis(analysis: dict) -> dict:
    """
    Шаг 2 — проверка на противоречия.
    Возвращает: {"valid": bool, "issues": [...]}
    """
    prompt = PROMPT_VALIDATE.format(analysis_json=json.dumps(analysis, ensure_ascii=False))
    raw = _call_claude(SYSTEM_VALIDATE, prompt)
    return _parse_json(raw)


def generate_summary(analysis: dict, validation: dict) -> str:
    """
    Шаг 3 — финальный текст для Telegram.
    Возвращает строку в Markdown.
    """
    prompt = PROMPT_SUMMARY.format(
        parties="...",          # заполняется моделью из JSON
        subject="...",
        amount="...",
        dates="...",
        risks_block="...",
        recommendation_text="...",
        recommendation_detail="...",
        questions="...",
        analysis_json=json.dumps(analysis, ensure_ascii=False),
        validation_json=json.dumps(validation, ensure_ascii=False),
    )
    return _call_claude(SYSTEM_SUMMARY, prompt)


def full_pipeline(text: str) -> tuple[dict, dict, str]:
    """
    Полный пайплайн: анализ → валидация → выжимка.
    Возвращает (analysis, validation, summary_text).
    """
    analysis   = analyze_contract(text)
    validation = validate_analysis(analysis)
    summary    = generate_summary(analysis, validation)
    return analysis, validation, summary
