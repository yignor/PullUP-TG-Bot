import asyncio
import os
from test_pullup_notifications import TestPullUPNotificationManager

async def send_test_messages():
    """Отправляет тестовые сообщения"""
    print("=== ОТПРАВКА ТЕСТОВЫХ СООБЩЕНИЙ В ТЕСТОВЫЙ КАНАЛ ===\n")
    
    # Проверяем переменные окружения
    bot_token = os.getenv('BOT_TOKEN')
    test_chat_id = os.getenv('TEST_CHAT_ID')
    
    if not bot_token or bot_token == "ваш_токен_бота":
        print("❌ BOT_TOKEN не установлен или установлен неправильно")
        print("Установите правильный токен: export BOT_TOKEN='ваш_реальный_токен'")
        return
    
    if not test_chat_id:
        print("❌ TEST_CHAT_ID не установлен")
        print("Добавьте TEST_CHAT_ID в .env для тестирования")
        return
    
    print("✅ Переменные окружения установлены")
    print()
    
    manager = TestPullUPNotificationManager()
    
    # Тест 1: Утреннее уведомление о предстоящих играх
    print("1. Отправка утреннего уведомления о предстоящих играх:")
    
    test_games = [
        {
            'team': 'Pull Up',
            'opponent': 'IT Basket',
            'time': '12.30',
            'order': 2
        },
        {
            'team': 'Pull Up',
            'opponent': 'Маиле Карго',
            'time': '14.00',
            'order': 3
        }
    ]
    
    test_links = [
        'game.html?gameId=921732&apiUrl=https://reg.infobasket.su&lang=ru',
        'game.html?gameId=921733&apiUrl=https://reg.infobasket.su&lang=ru',
        'game.html?gameId=921726&apiUrl=https://reg.infobasket.su&lang=ru'
    ]
    
    # Формируем HTML с ссылками для теста
    test_html = f"""
    <html>
        <a href="{test_links[0]}">Link 1</a>
        <a href="{test_links[1]}">Link 2</a>
        <a href="{test_links[2]}">Link 3</a>
    </html>
    """
    
    try:
        await manager.send_test_morning_notification(test_games, test_html)
        print("✅ Тестовое утреннее уведомление отправлено в тестовый канал")
    except Exception as e:
        print(f"❌ Ошибка отправки тестового утреннего уведомления: {e}")
    
    print()
    
    # Тест 2: Уведомление о завершении игры
    print("2. Отправка уведомления о завершении игры:")
    
    test_finished_game = {
        'pullup_team': 'Pull Up',
        'opponent_team': 'IT Basket',
        'pullup_score': 85,
        'opponent_score': 72,
        'date': '16.08.2025'
    }
    
    try:
        await manager.send_test_finish_notification(test_finished_game)
        print("✅ Тестовое уведомление о завершении игры отправлено в тестовый канал")
    except Exception as e:
        print(f"❌ Ошибка отправки тестового уведомления о завершении: {e}")
    
    print()
    print("=== ТЕСТОВЫЕ СООБЩЕНИЯ ОТПРАВЛЕНЫ В ТЕСТОВЫЙ КАНАЛ ===")

if __name__ == "__main__":
    asyncio.run(send_test_messages())
