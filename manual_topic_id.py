#!/usr/bin/env python3
"""
Ручной способ получения ID топика "АНОНСЫ ТРЕНИРОВОК"
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def show_instructions():
    """Показывает инструкции по получению ID топика"""
    
    bot_token = os.getenv('BOT_TOKEN')
    
    print("📱 РУЧНОЙ СПОСОБ ПОЛУЧЕНИЯ ID ТОПИКА")
    print("=" * 50)
    
    print("\n📋 Шаг 1: Отправка сообщения")
    print("1. Откройте Telegram")
    print("2. Перейдите в чат с топиками")
    print("3. Найдите топик 'АНОНСЫ ТРЕНИРОВОК'")
    print("4. Отправьте ЛЮБОЕ сообщение от бота в этот топик")
    print("   (можно просто написать 'тест' или 'hello')")
    
    print("\n📋 Шаг 2: Получение ID")
    print("После отправки сообщения перейдите по ссылке:")
    if bot_token:
        print(f"🔗 https://api.telegram.org/bot{bot_token}/getUpdates")
    else:
        print("❌ BOT_TOKEN не настроен в .env файле")
        return
    
    print("\n📋 Шаг 3: Поиск ID")
    print("В ответе найдите JSON объект с вашим сообщением")
    print("Ищите поле 'message_thread_id' - это и есть ID топика")
    
    print("\n📋 Пример ответа:")
    print("""
{
  "ok": true,
  "result": [
    {
      "update_id": 123456789,
      "message": {
        "message_id": 123,
        "from": {...},
        "chat": {...},
        "date": 1234567890,
        "text": "тест",
        "message_thread_id": 456789  ← ЭТО ID ТОПИКА
      }
    }
  ]
}
    """)
    
    print("\n📋 Шаг 4: Настройка")
    print("Скопируйте значение 'message_thread_id' и добавьте в .env:")
    print("ANNOUNCEMENTS_TOPIC_ID=456789")
    
    print("\n📋 Шаг 5: Проверка")
    print("Запустите этот скрипт снова для проверки:")
    print("python manual_topic_id.py --check")

def check_topic_id():
    """Проверяет, настроен ли ID топика"""
    
    topic_id = os.getenv('ANNOUNCEMENTS_TOPIC_ID')
    
    print("🔍 ПРОВЕРКА НАСТРОЙКИ ID ТОПИКА")
    print("=" * 40)
    
    if topic_id:
        print(f"✅ ANNOUNCEMENTS_TOPIC_ID настроен: {topic_id}")
        print("\n📝 Теперь можно протестировать отправку:")
        print("python test_topic_send.py")
    else:
        print("❌ ANNOUNCEMENTS_TOPIC_ID не настроен")
        print("\n📝 Следуйте инструкциям выше для настройки")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_topic_id()
    else:
        show_instructions()
