"""
Генераторы inline-клавиатур.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 Загрузить договор", callback_data="upload_hint")],
        [
            InlineKeyboardButton("📊 История",  callback_data="history"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        ],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")],
    ])


def after_analysis_kb(contract_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 Краткая выжимка", callback_data=f"short_{contract_id}"),
            InlineKeyboardButton("📥 Полный отчёт",    callback_data=f"full_{contract_id}"),
        ],
        [
            InlineKeyboardButton("❓ Задать вопрос",   callback_data=f"ask_{contract_id}"),
            InlineKeyboardButton("🔁 Новый договор",   callback_data="upload_hint"),
        ],
        [InlineKeyboardButton("📊 История",            callback_data="history")],
    ])


def history_kb(contracts: list) -> InlineKeyboardMarkup:
    rows = []
    for c in contracts[:10]:
        label = f"{'🔴' if c.risk_level == 'high' else '🟡' if c.risk_level == 'medium' else '🟢'} {c.file_name[:30]}"
        rows.append([InlineKeyboardButton(label, callback_data=f"full_{c.id}")])
    rows.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)


def settings_kb(notify_risks: bool) -> InlineKeyboardMarkup:
    notify_label = f"🔔 Уведомления: {'ВКЛ ✅' if notify_risks else 'ВЫКЛ ❌'}"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(notify_label, callback_data="settings_toggle_notify")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]
    ])
