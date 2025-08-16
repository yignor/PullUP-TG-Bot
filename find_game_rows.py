#!/usr/bin/env python3
"""
Простой скрипт для поиска строк с js-period и js-timer
"""

import asyncio
import re
from pullup_notifications import PullUPNotificationManager
from bs4 import BeautifulSoup

async def find_game_rows():
    """Ищет строки с js-period и js-timer"""
    print("=== ПОИСК СТРОК С ИГРАМИ ===\n")
    
    manager = PullUPNotificationManager()
    
    try:
        # Получаем свежие данные
        print("1. Получение данных с сайта...")
        html_content = await manager.get_fresh_page_content()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Ищем все строки tr с атрибутами js-period или js-timer
        print("2. Поиск строк с js-period или js-timer...")
        all_rows = soup.find_all('tr')
        game_rows = []
        
        for row in all_rows:
            js_period = row.get('js-period')
            js_timer = row.get('js-timer')
            if js_period is not None or js_timer is not None:
                game_rows.append(row)
        
        print(f"Найдено строк с js-period/js-timer: {len(game_rows)}")
        
        if not game_rows:
            print("❌ Строки с js-period/js-timer не найдены!")
            print("\n3. Поиск всех атрибутов в строках tr...")
            
            # Показываем все атрибуты в строках tr
            for i, row in enumerate(all_rows[:20], 1):  # Первые 20 строк
                attrs = row.attrs
                if attrs:
                    print(f"   {i}. Атрибуты: {attrs}")
                    row_text = row.get_text().strip()[:50]
                    print(f"      Текст: {row_text}...")
        
        else:
            print("\n3. Анализ найденных строк:")
            for i, row in enumerate(game_rows, 1):
                row_text = row.get_text().strip()
                js_period = row.get('js-period')
                js_timer = row.get('js-timer')
                
                print(f"   {i}. js-period: {js_period}, js-timer: {js_timer}")
                print(f"      Текст: {row_text[:100]}...")
                
                # Проверяем, содержит ли строка PullUP
                if any(re.search(pattern, row_text, re.IGNORECASE) for pattern in [r'pull\s*up', r'PullUP', r'Pull\s*Up']):
                    print(f"      ✅ СОДЕРЖИТ PULLUP!")
                    
                    # Проверяем, завершена ли игра
                    if js_period == '4' and js_timer == '0:00':
                        print(f"      ✅ ИГРА ЗАВЕРШЕНА!")
                    elif '4ч' in row_text or '4 ч' in row_text:
                        print(f"      ✅ ИГРА ЗАВЕРШЕНА (по тексту)!")
                    else:
                        print(f"      ⚠️ Игра не завершена (period: {js_period}, timer: {js_timer})")
                print()
        
        print("=== ПОИСК ЗАВЕРШЕН ===")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(find_game_rows())
