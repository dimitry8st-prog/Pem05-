# Contract Wizard Bot 🧙‍♂️

ИИ-помощник для первичного разбора договоров и коммерческих предложений в Telegram.

## Что умеет

- Принимает PDF и фото договоров прямо в чате
- За 3–5 минут выдаёт структурированную выжимку: стороны, сумма, сроки, риски
- Находит «красные флаги» и нестандартные пункты
- Даёт чёткую рекомендацию: подписать / на юриста / встречное предложение
- Хранит историю всех проанализированных договоров

## Быстрый старт

### 1. Клонирование и окружение

```bash
git clone <repo>
cd contract_wizard_bot

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Настройка .env

```bash
cp .env.example .env
```

Откройте `.env` и заполните:
- `TELEGRAM_TOKEN` — получить у [@BotFather](https://t.me/BotFather)
- `ANTHROPIC_API_KEY` — получить на [console.anthropic.com](https://console.anthropic.com)

### 3. Запуск

```bash
python main.py
```

Бот запустится и будет ждать сообщений. Найдите его в Telegram и отправьте `/start`.

---

## Структура проекта

```
contract_wizard_bot/
├── main.py                  # Точка входа, регистрация хендлеров
├── config.py                # Конфигурация через переменные окружения
├── database.py              # SQLAlchemy модели и хелперы
├── requirements.txt
├── .env.example
│
├── handlers/                # Обработчики команд и событий
│   ├── start.py             # /start, /help
│   ├── document.py          # Приём PDF/фото и запуск анализа
│   ├── history.py           # /history
│   ├── settings.py          # /settings
│   ├── feedback.py          # /feedback
│   └── callbacks.py         # Роутер inline-кнопок
│
├── services/                # Бизнес-логика
│   ├── claude_service.py    # Три промпта: анализ → валидация → выжимка
│   └── extractor.py         # Извлечение текста из PDF и изображений
│
├── prompts/                 # Системные промпты Claude
│   └── __init__.py
│
└── utils/                   # Вспомогательные утилиты
    ├── keyboards.py          # Inline-клавиатуры
    └── formatting.py         # Форматирование сообщений
```

---

## Команды бота

| Команда     | Описание                              |
|-------------|---------------------------------------|
| `/start`    | Приветствие и главное меню            |
| `/help`     | Справка                               |
| `/history`  | Последние 20 проанализированных договоров |
| `/settings` | Настройки уведомлений                 |
| `/feedback` | Отправить отзыв                       |

---

## Деплой на сервер (Ubuntu)

```bash
# Установка systemd-сервиса
sudo nano /etc/systemd/system/contract-wizard.service
```

```ini
[Unit]
Description=Contract Wizard Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/contract_wizard_bot
ExecStart=/home/ubuntu/contract_wizard_bot/venv/bin/python main.py
Restart=always
RestartSec=10
EnvironmentFile=/home/ubuntu/contract_wizard_bot/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable contract-wizard
sudo systemctl start contract-wizard
sudo systemctl status contract-wizard
```

---

## Переход на PostgreSQL

Замените в `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/contract_wizard
```

Установите драйвер:
```bash
pip install psycopg2-binary
```

---

## Лицензия

MIT
