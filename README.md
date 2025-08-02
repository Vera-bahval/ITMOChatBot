# ITMO Master's Program Chatbot

Telegram-бот для помощи абитуриентам в выборе магистерских ИИ-программ на основе парсинга данных с сайта и RAG-системы: хранения и поиска данных в векторной БД (векторизация с помощью модели Mistral по API) и ответа на вопроса с помощью LLM по API (DeepSeek). 

## Возможности

- Поиск информации по двум программам: "Искусственный интеллект" и "Управление ИИ-продуктами"
- Персональные рекомендации на основе бэкграунда пользователя
- Информация о поступлении, обучении, карьерных перспективах
- AI-генерируемые ответы с использованием DeepSeek
- Векторный поиск с использованием Mistral embeddings

## Установка и запуск

1. Клонируйте репозиторий
2. Создайте файл `.env` с вашими API ключами:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
OPENROUTER_API_KEY=your_openrouter_key
MISTRAL_API_KEY=your_mistral_key
```
3. Запустите с помощью Docker:
```bash
docker-compose up --build
```

## Архитектура

- **DataParser**: Парсинг данных с сайтов ИТМО
- **VectorDB**: Векторная база данных с эмбеддингами
- **AIAssistant**: Интеграция с DeepSeek для генерации ответов
- **ITMOChatBot**: Основная логика Telegram бота

## Технологии

- Python 3.11
- python-telegram-bot
- BeautifulSoup4 для парсинга
- scikit-learn для векторного поиска
- OpenRouter API (DeepSeek)
- Mistral API для эмбеддингов
- Docker & Docker Compose

## Структура проекта

```
├── main.py              # Точка входа
├── data_parser.py       # Парсинг сайтов
├── vector_db.py         # Векторная база данных
├── ai_assistant.py      # AI интеграция
├── requirements.txt     # Зависимости
├── Dockerfile          # Docker образ
├── docker-compose.yml  # Docker Compose
├── .env               # Переменные окружения
└── data/              # Данные программ
    ├── programs_data.json
    ├── documents.json
    └── embeddings.npy
```