#!/usr/bin/env python3
"""
Скрипт для тестирования логики определения завершенных игр
"""

import asyncio
import os
from dotenv import load_dotenv
from pullup_notifications import PullUPNotificationManager
from bs4 import BeautifulSoup

def load_env_variables():
    """Загружает переменные из .env файла"""
    try:
        load_dotenv()
        print("✅ Переменные загружены через python-dotenv")
    except ImportError:
        try:
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            print("✅ Переменные загружены из .env файла")
        except FileNotFoundError:
            print("❌ Файл .env не найден")
            return False
    
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ BOT_TOKEN или CHAT_ID не найдены")
        return False
    
    print(f"✅ BOT_TOKEN: {bot_token[:10]}...")
    print(f"✅ CHAT_ID: {chat_id}")
    return True

async def test_finished_games():
    """Тестирует логику определения завершенных игр"""
    print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕННЫХ ИГР ===\n")
    
    if not load_env_variables():
        return
    
    manager = PullUPNotificationManager()
    
    try:
        # Получаем свежие данные
        print("1. Получение данных с сайта...")
        html_content = await manager.get_fresh_page_content()
        soup = BeautifulSoup(html_content, 'html.parser')
        page_text = soup.get_text()
        
        # Извлекаем текущую дату
        current_date = manager.extract_current_date(page_text)
        if not current_date:
            print("❌ Не удалось извлечь текущую дату")
            return
        
        print(f"✅ Дата: {current_date}")
        
        # Проверяем завершенные игры
        print("\n2. Поиск завершенных игр PullUP...")
        finished_games = manager.check_finished_games(html_content, current_date)
        
        if not finished_games:
            print("⚠️ Завершенных игр PullUP не найдено")
            print("\n3. Анализ всех игр PullUP на странице...")
            
            # Показываем все игры PullUP
            pullup_games = manager.find_pullup_games(page_text, current_date)
            for i, game in enumerate(pullup_games, 1):
                print(f"   {i}. {game['team']} vs {game['opponent']} - {game['time']}")
            
            # Показываем все строки с PullUP
            print("\n4. Анализ HTML строк с PullUP...")
            game_rows = soup.find_all('tr')
            pullup_rows = []
            
            for row in game_rows:
                row_text = row.get_text().lower()
                if any(re.search(pattern, row_text, re.IGNORECASE) for pattern in [r'pull\s*up', r'PullUP', r'Pull\s*Up']):
                    pullup_rows.append(row)
            
            print(f"   Найдено строк с PullUP: {len(pullup_rows)}")
            
            for i, row in enumerate(pullup_rows, 1):
                row_text = row.get_text()
                js_period = row.get('js-period')
                js_timer = row.get('js-timer')
                print(f"   {i}. {row_text[:100]}... | js-period: {js_period} | js-timer: {js_timer}")
        
        else:
            print(f"✅ Найдено завершенных игр: {len(finished_games)}")
            
            # Отправляем уведомления о завершенных играх
            print("\n3. Отправка уведомлений о завершенных играх...")
            for i, game in enumerate(finished_games, 1):
                print(f"   {i}. {game['pullup_team']} vs {game['opponent_team']} - {game['pullup_score']}:{game['opponent_score']}")
                print(f"      Ссылка: {game.get('game_link', 'Не найдена')}")
                
                await manager.send_finish_notification(game)
                print(f"      ✅ Уведомление отправлено")
        
        print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import re
    asyncio.run(test_finished_games())
