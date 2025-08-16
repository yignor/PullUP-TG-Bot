import asyncio
import os
import sys
sys.path.append('..')
from pullup_notifications import PullUPNotificationManager

async def final_test():
    """Финальный тест всей системы уведомлений"""
    print("=== ФИНАЛЬНЫЙ ТЕСТ СИСТЕМЫ УВЕДОМЛЕНИЙ PULLUP ===\n")
    
    # Проверяем переменные окружения
    print("1. Проверка переменных окружения:")
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if bot_token:
        print("✅ BOT_TOKEN установлен")
    else:
        print("❌ BOT_TOKEN не установлен")
    
    if chat_id:
        print("✅ CHAT_ID установлен")
    else:
        print("❌ CHAT_ID не установлен")
    
    print()
    
    # Создаем менеджер уведомлений
    manager = PullUPNotificationManager()
    
    # Тестируем получение свежих данных
    print("2. Тест получения свежих данных с сайта:")
    try:
        html_content = await manager.get_fresh_page_content()
        print("✅ Данные успешно получены")
        print(f"   Размер HTML: {len(html_content)} символов")
    except Exception as e:
        print(f"❌ Ошибка получения данных: {e}")
        return
    
    print()
    
    # Тестируем извлечение даты
    print("3. Тест извлечения даты:")
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    page_text = soup.get_text()
    
    current_date = manager.extract_current_date(page_text)
    if current_date:
        print(f"✅ Дата извлечена: {current_date}")
    else:
        print("❌ Не удалось извлечь дату")
        return
    
    print()
    
    # Тестируем поиск игр PullUP
    print("4. Тест поиска игр PullUP:")
    pullup_games = manager.find_pullup_games(page_text, current_date)
    if pullup_games:
        print(f"✅ Найдено игр PullUP: {len(pullup_games)}")
        for i, game in enumerate(pullup_games):
            print(f"   {i+1}. {game['team']} vs {game['opponent']} - {game['time']} (позиция: {game['order']})")
    else:
        print("❌ Игры PullUP не найдены")
    
    print()
    
    # Тестируем поиск завершенных игр
    print("5. Тест поиска завершенных игр:")
    finished_games = manager.check_finished_games(html_content, current_date)
    if finished_games:
        print(f"✅ Найдено завершенных игр: {len(finished_games)}")
        for i, game in enumerate(finished_games):
            print(f"   {i+1}. {game['pullup_team']} {game['pullup_score']} : {game['opponent_score']} {game['opponent_team']}")
    else:
        print("✅ Завершенных игр не найдено")
    
    print()
    
    # Тестируем формат утреннего уведомления
    print("6. Тест формата утреннего уведомления:")
    if pullup_games:
        await manager.send_morning_notification(pullup_games, html_content)
    else:
        print("⚠️ Нет игр для тестирования утреннего уведомления")
    
    print()
    
    # Тестируем формат уведомления о завершении
    print("7. Тест формата уведомления о завершении:")
    if finished_games:
        for game in finished_games:
            await manager.send_finish_notification(game)
    else:
        print("⚠️ Нет завершенных игр для тестирования")
    
    print()
    print("=== ТЕСТ ЗАВЕРШЕН ===")
    print()
    print("Для запуска постоянного мониторинга выполните:")
    print("  ./start_monitor.sh")
    print()
    print("Для остановки мониторинга выполните:")
    print("  ./stop_monitor.sh")

if __name__ == "__main__":
    asyncio.run(final_test())
