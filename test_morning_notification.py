import asyncio
import os
from datetime import datetime, time
from pullup_notifications import PullUPNotificationManager

async def test_morning_notification():
    """Тестирует утреннее уведомление"""
    print("=== ТЕСТ УТРЕННЕГО УВЕДОМЛЕНИЯ ===\n")
    
    # Проверяем переменные окружения
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or bot_token == "ваш_токен_бота":
        print("❌ BOT_TOKEN не установлен")
        print("Установите: export BOT_TOKEN='ваш_реальный_токен'")
        return
    
    if not chat_id or chat_id == "ваш_chat_id":
        print("❌ CHAT_ID не установлен")
        print("Установите: export CHAT_ID='ваш_реальный_chat_id'")
        return
    
    print("✅ Переменные окружения установлены")
    
    manager = PullUPNotificationManager()
    
    try:
        # Получаем свежие данные
        print("Получение данных с сайта...")
        html_content = await manager.get_fresh_page_content()
        soup = BeautifulSoup(html_content, 'html.parser')
        page_text = soup.get_text()
        
        # Извлекаем дату
        current_date = manager.extract_current_date(page_text)
        if not current_date:
            print("❌ Не удалось извлечь дату")
            return
        
        print(f"✅ Дата: {current_date}")
        
        # Ищем игры PullUP
        pullup_games = manager.find_pullup_games(page_text, current_date)
        if pullup_games:
            print(f"✅ Найдено игр PullUP: {len(pullup_games)}")
            for i, game in enumerate(pullup_games):
                print(f"   {i+1}. {game['team']} vs {game['opponent']} - {game['time']}")
            
            # Отправляем уведомление
            print("\nОтправка утреннего уведомления...")
            await manager.send_morning_notification(pullup_games, html_content)
            print("✅ Утреннее уведомление отправлено!")
        else:
            print("❌ Игры PullUP не найдены")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    from bs4 import BeautifulSoup
    asyncio.run(test_morning_notification())
