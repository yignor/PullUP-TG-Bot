#!/usr/bin/env python3
"""
Скрипт для анализа структуры HTML и поиска строк с играми
"""

import asyncio
import re
from pullup_notifications import PullUPNotificationManager
from bs4 import BeautifulSoup

async def debug_html_structure():
    """Анализирует структуру HTML для поиска игр"""
    print("=== АНАЛИЗ СТРУКТУРЫ HTML ===\n")
    
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
        
        # Ищем все строки с играми на текущую дату
        print(f"\n2. Поиск игр на {current_date}...")
        all_games = re.findall(rf'{current_date}\s+\d{{2}}\.\d{{2}}[^-]*-\s*[^-]+[^-]*-\s*[^-]+', page_text)
        print(f"Найдено игр на {current_date}: {len(all_games)}")
        
        for i, game in enumerate(all_games, 1):
            print(f"   {i}. {game}")
        
        # Ищем все строки tr с атрибутами js-period и js-timer
        print(f"\n3. Поиск строк tr с js-period и js-timer...")
        game_rows = soup.find_all('tr')
        rows_with_attributes = []
        
        for row in game_rows:
            js_period = row.get('js-period')
            js_timer = row.get('js-timer')
            if js_period is not None or js_timer is not None:
                rows_with_attributes.append(row)
        
        print(f"Найдено строк с js-period/js-timer: {len(rows_with_attributes)}")
        
        for i, row in enumerate(rows_with_attributes, 1):
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
        
        # Ищем строки с PullUP в тексте
        print(f"\n4. Поиск строк с PullUP в тексте...")
        pullup_rows = []
        
        for row in game_rows:
            row_text = row.get_text().lower()
            if any(re.search(pattern, row_text, re.IGNORECASE) for pattern in [r'pull\s*up', r'PullUP', r'Pull\s*Up']):
                pullup_rows.append(row)
        
        print(f"Найдено строк с PullUP в тексте: {len(pullup_rows)}")
        
        for i, row in enumerate(pullup_rows, 1):
            row_text = row.get_text().strip()
            js_period = row.get('js-period')
            js_timer = row.get('js-timer')
            print(f"   {i}. js-period: {js_period}, js-timer: {js_timer}")
            print(f"      Текст: {row_text[:150]}...")
            print()
        
        # Ищем таблицы с играми
        print(f"\n5. Поиск таблиц с играми...")
        tables = soup.find_all('table')
        print(f"Найдено таблиц: {len(tables)}")
        
        for i, table in enumerate(tables, 1):
            table_text = table.get_text()[:200]
            print(f"   {i}. {table_text}...")
            
            # Проверяем, содержит ли таблица игры на текущую дату
            if current_date in table_text:
                print(f"      ✅ СОДЕРЖИТ ИГРЫ НА {current_date}")
                
                # Ищем строки с PullUP в этой таблице
                rows = table.find_all('tr')
                for row in rows:
                    row_text = row.get_text()
                    if any(re.search(pattern, row_text, re.IGNORECASE) for pattern in [r'pull\s*up', r'PullUP', r'Pull\s*Up']):
                        js_period = row.get('js-period')
                        js_timer = row.get('js-timer')
                        print(f"         PullUP: {row_text[:100]}... | period: {js_period} | timer: {js_timer}")
            print()
        
        print("=== АНАЛИЗ ЗАВЕРШЕН ===")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_html_structure())
