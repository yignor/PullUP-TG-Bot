import asyncio
import os
from datetime import datetime
from pullup_notifications import PullUPNotificationManager
from bs4 import BeautifulSoup

async def test_notifications():
    """Тестирует формат уведомлений"""
    manager = PullUPNotificationManager()
    
    print("=== ТЕСТ УВЕДОМЛЕНИЙ PULLUP ===\n")
    
    # Тест 1: Утреннее уведомление
    print("1. Тест утреннего уведомления:")
    
    # Создаем тестовые данные
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
    
    # Формируем сообщение
    lines = []
    for game in test_games:
        lines.append(f"🏀 Сегодня игра против **{game['opponent']}**")
        lines.append(f"⏰ Время игры: **{game['time']}**")
        
        # Получаем ссылку на игру
        game_link = "http://letobasket.ru/"
        if game['order'] and game['order'] <= len(test_links):
            game_link = "http://letobasket.ru/" + test_links[game['order'] - 1]
        
        lines.append(f"🔗 Ссылка на игру: [тут]({game_link})")
        lines.append("")  # Пустая строка между играми
    
    morning_message = "\n".join(lines)
    print(morning_message)
    
    print("\n" + "="*50 + "\n")
    
    # Тест 2: Уведомление о завершении игры
    print("2. Тест уведомления о завершении игры:")
    
    test_finished_game = {
        'pullup_team': 'Pull Up',
        'opponent_team': 'IT Basket',
        'pullup_score': 85,
        'opponent_score': 72,
        'date': '16.08.2025'
    }
    
    # Определяем победителя
    if test_finished_game['pullup_score'] > test_finished_game['opponent_score']:
        result_emoji = "🏆"
        result_text = "победили"
    elif test_finished_game['pullup_score'] < test_finished_game['opponent_score']:
        result_emoji = "😔"
        result_text = "проиграли"
    else:
        result_emoji = "🤝"
        result_text = "сыграли вничью"
    
    finish_message = f"🏀 Игра против **{test_finished_game['opponent_team']}** закончилась\n"
    finish_message += f"{result_emoji} Счет: **{test_finished_game['pullup_team']} {test_finished_game['pullup_score']} : {test_finished_game['opponent_score']} {test_finished_game['opponent_team']}** ({result_text})\n"
    finish_message += f"📊 Ссылка на протокол: [тут](http://letobasket.ru/)"
    
    print(finish_message)
    
    print("\n" + "="*50 + "\n")
    
    # Тест 3: Проверка реальных данных
    print("3. Проверка реальных данных с сайта:")
    
    try:
        # Получаем свежий контент
        html_content = await manager.get_fresh_page_content()
        soup = BeautifulSoup(html_content, 'html.parser')
        page_text = soup.get_text()
        
        # Извлекаем текущую дату
        current_date = manager.extract_current_date(page_text)
        if current_date:
            print(f"📅 Текущая дата на сайте: {current_date}")
            
            # Ищем игры PullUP
            pullup_games = manager.find_pullup_games(page_text, current_date)
            if pullup_games:
                print(f"🏀 Найдено игр PullUP: {len(pullup_games)}")
                for i, game in enumerate(pullup_games):
                    print(f"  {i+1}. {game['team']} vs {game['opponent']} - {game['time']} (позиция: {game['order']})")
            else:
                print("❌ Игры PullUP не найдены")
            
            # Проверяем завершенные игры
            finished_games = manager.check_finished_games(html_content, current_date)
            if finished_games:
                print(f"🏁 Найдено завершенных игр: {len(finished_games)}")
                for i, game in enumerate(finished_games):
                    print(f"  {i+1}. {game['pullup_team']} {game['pullup_score']} : {game['opponent_score']} {game['opponent_team']}")
            else:
                print("✅ Завершенных игр не найдено")
        else:
            print("❌ Не удалось извлечь дату")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке реальных данных: {e}")

if __name__ == "__main__":
    asyncio.run(test_notifications())
