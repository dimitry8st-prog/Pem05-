"""
Вспомогательные функции форматирования.
"""
from datetime import datetime


RISK_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}
RISK_LABEL = {"high": "ВЫСОКИЙ", "medium": "СРЕДНИЙ", "low": "НИЗКИЙ"}

REC_LABEL = {
    "sign":             "✅ Подписать сейчас",
    "lawyer":           "⚖️ На согласование юристу",
    "counter_proposal": "📝 Нужно встречное предложение",
}


def format_amount(amount: dict) -> str:
    if not amount:
        return "не указана"
    total    = amount.get("total", 0)
    currency = amount.get("currency", "RUB")
    adv      = amount.get("advance_percent", 0)
    terms    = amount.get("payment_terms", "")
    parts = []
    if total:
        parts.append(f"*{total:,.0f} {currency}*".replace(",", " "))
    if adv:
        parts.append(f"аванс {adv}%")
    if terms:
        parts.append(terms)
    return ", ".join(parts) if parts else "не указана"


def format_dates(dates: dict) -> str:
    if not dates:
        return "не указаны"
    start = dates.get("start")
    end   = dates.get("end")
    if start and end:
        return f"{start} – {end}"
    if end:
        return f"до {end}"
    return "не указаны"


def format_risks(red_flags: list) -> str:
    if not red_flags:
        return "✅ Рисков не обнаружено"
    lines = [f"⚠️ *РИСКИ ({len(red_flags)} найдено):*"]
    for f in red_flags[:5]:                          # максимум 5 в Telegram
        emoji = RISK_EMOJI.get(f.get("severity", "low"), "🟢")
        clause = f.get("clause", "")
        text   = f.get("text", "")
        clause_str = f"п.{clause} — " if clause else ""
        lines.append(f"  {emoji} {clause_str}{text}")
    return "\n".join(lines)


def format_questions(questions: list) -> str:
    if not questions:
        return "—"
    return "\n".join(f"  • {q}" for q in questions[:3])


def format_full_report(contract) -> str:
    """Форматирует полный текстовый отчёт из сохранённого договора."""
    analysis = contract.get_analysis()
    parties  = analysis.get("parties", {})
    client_p = parties.get("client", "—")
    vendor_p = parties.get("vendor", "—")

    lines = [
        f"📄 *ПОЛНЫЙ ОТЧЁТ*",
        f"🗓 _{contract.created_at.strftime('%d.%m.%Y %H:%M')}_",
        "━━━━━━━━━━━━━━━━━━━━━",
        f"🏢 *Стороны:* {client_p} ↔ {vendor_p}",
        f"📌 *Предмет:* {analysis.get('subject', '—')}",
        f"💰 *Сумма:* {format_amount(analysis.get('amount', {}))}",
        f"📅 *Срок:* {format_dates(analysis.get('dates', {}))}",
        "━━━━━━━━━━━━━━━━━━━━━",
        format_risks(analysis.get("red_flags", [])),
        "━━━━━━━━━━━━━━━━━━━━━",
        f"💬 *Рекомендация:* {REC_LABEL.get(contract.recommendation, '—')}",
        "",
        "❓ *Вопросы клиенту:*",
        format_questions(analysis.get("questions", [])),
    ]

    # Если были замечания валидации
    validation = analysis.get("_validation", {})
    if validation and not validation.get("valid", True):
        issues = validation.get("issues", [])
        lines += ["", "🚨 *Дополнительные предупреждения:*"]
        lines += [f"  ⛔ {i}" for i in issues]

    return "\n".join(lines)


def short_summary(contract) -> str:
    """3–4 строки для быстрого пересылания."""
    analysis = contract.get_analysis()
    risk_emoji = RISK_EMOJI.get(contract.risk_level, "🟢")
    risk_label = RISK_LABEL.get(contract.risk_level, "НИЗКИЙ")
    rec = REC_LABEL.get(contract.recommendation, "—")

    return (
        f"📄 *{contract.file_name}*\n"
        f"📌 {analysis.get('subject', '—')}\n"
        f"💰 {format_amount(analysis.get('amount', {}))}\n"
        f"{risk_emoji} Риск: *{risk_label}*\n"
        f"💬 {rec}"
    )
