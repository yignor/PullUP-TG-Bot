#!/usr/bin/env python3
"""
Скрипт для анализа структуры сайта
"""
import sys
import os
sys.path.append('..')

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def debug_site_structure():
    """Анализирует структуру сайта"""
    print("🔍 АНАЛИЗ СТРУКТУРЫ САЙТА")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://letobasket.ru/') as response:
                content = await response.text()
                
        soup = BeautifulSoup(content, 'html.parser')
        
        # Ищем блоки с играми
        print("📊 ПОИСК БЛОКОВ С ИГРАМИ:")
        
        # Ищем заголовки
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for header in headers:
            header_text = header.get_text().strip()
            if any(word in header_text.lower() for word in ['игра', 'матч', 'расписание', 'результат']):
                print(f"   Заголовок: {header_text}")
        
        # Ищем div с классами
        divs = soup.find_all('div', class_=True)
        for div in divs:
            class_name = ' '.join(div.get('class', []))
            if any(word in class_name.lower() for word in ['game', 'match', 'result', 'schedule']):
                print(f"   Div с классом: {class_name}")
        
        # Ищем таблицы с датами
        tables = soup.find_all('table')
        print(f"\n📅 ТАБЛИЦЫ С ДАТАМИ:")
        
        for i, table in enumerate(tables):
            table_text = table.get_text()
            
            # Ищем даты в таблице
            dates = re.findall(r'\d{2}\.\d{2}\.\d{4}', table_text)
            if dates:
                print(f"   Таблица {i+1}: найдено {len(dates)} дат")
                print(f"     Даты: {dates[:3]}...")  # Показываем первые 3 даты
                
                # Проверяем, есть ли PullUP в этой таблице
                if re.search(r'pull\s*up', table_text, re.IGNORECASE):
                    print(f"     ✅ Содержит PullUP!")
                    
                    # Показываем строки с PullUP
                    rows = table.find_all('tr')
                    for row in rows:
                        row_text = row.get_text()
                        if re.search(r'pull\s*up', row_text, re.IGNORECASE):
                            print(f"       Строка: {row_text[:100]}...")
        
        # Ищем конкретные игры с датами
        print(f"\n🎯 ПОИСК КОНКРЕТНЫХ ИГР:")
        
        # Ищем паттерн "дата - команда1 - команда2 - счет"
        game_pattern = r'(\d{2}\.\d{2}\.\d{4})\s*-\s*([^-]+)\s*-\s*([^-]+)\s*(\d+:\d+)'
        matches = re.findall(game_pattern, content)
        
        for match in matches:
            date, team1, team2, score = match
            if 'pull' in team1.lower() or 'pull' in team2.lower():
                print(f"   Игра: {date} - {team1.strip()} vs {team2.strip()} - {score}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_site_structure())
