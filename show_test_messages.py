import asyncio
from pullup_notifications import PullUPNotificationManager

async def show_test_messages():
    """Показывает тестовые сообщения без отправки"""
    print("=== ТЕСТОВЫЕ СООБЩЕНИЯ PULLUP ===\n")
    
    manager = PullUPNotificationManager()
    
    # Тест 1: Утреннее уведомление о предстоящих играх
    print("1. УТРЕННЕЕ УВЕДОМЛЕНИЕ (10:00):")
    print("=" * 50)
    
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
    
    # Очищаем множество отправленных уведомлений для теста
    from pullup_notifications import sent_morning_notifications
    sent_morning_notifications.clear()
    
    await manager.send_morning_notification(test_games, test_html)
    
    print("\n" + "=" * 50)
    print()
    
    # Тест 2: Уведомление о завершении игры
    print("2. УВЕДОМЛЕНИЕ О ЗАВЕРШЕНИИ ИГРЫ:")
    print("=" * 50)
    
    test_finished_game = {
        'pullup_team': 'Pull Up',
        'opponent_team': 'IT Basket',
        'pullup_score': 85,
        'opponent_score': 72,
        'date': '16.08.2025'
    }
    
    # Очищаем множество отправленных уведомлений для теста
    from pullup_notifications import sent_finish_notifications
    sent_finish_notifications.clear()
    
    await manager.send_finish_notification(test_finished_game)
    
    print("\n" + "=" * 50)
    print()
    
    # Тест 3: Уведомление о проигрыше
    print("3. УВЕДОМЛЕНИЕ О ПРОИГРЫШЕ:")
    print("=" * 50)
    
    test_lost_game = {
        'pullup_team': 'Pull Up',
        'opponent_team': 'Маиле Карго',
        'pullup_score': 65,
        'opponent_score': 78,
        'date': '16.08.2025'
    }
    
    sent_finish_notifications.clear()
    await manager.send_finish_notification(test_lost_game)
    
    print("\n" + "=" * 50)
    print()
    
    # Тест 4: Уведомление о ничьей
    print("4. УВЕДОМЛЕНИЕ О НИЧЬЕЙ:")
    print("=" * 50)
    
    test_draw_game = {
        'pullup_team': 'Pull Up',
        'opponent_team': 'Тосно',
        'pullup_score': 75,
        'opponent_score': 75,
        'date': '16.08.2025'
    }
    
    sent_finish_notifications.clear()
    await manager.send_finish_notification(test_draw_game)
    
    print("\n" + "=" * 50)
    print()
    print("=== ДЛЯ ОТПРАВКИ РЕАЛЬНЫХ СООБЩЕНИЙ ===")
    print("Установите переменные окружения:")
    print("export BOT_TOKEN='ваш_реальный_токен_бота'")
    print("export CHAT_ID='ваш_реальный_chat_id'")
    print()
    print("Затем запустите:")
    print("python send_test_messages.py")

if __name__ == "__main__":
    asyncio.run(show_test_messages())
