#!/usr/bin/env python3
"""
Простой парсер для анализа структуры данных на сайте letobasket.ru
"""

import asyncio
import re
from bs4 import BeautifulSoup
import aiohttp
from datetime import datetime, timezone, timedelta

LETOBASKET_URL = "http://letobasket.ru/"

async def analyze_site_structure():
    """Анализирует структуру сайта для понимания формата данных"""
    
    async with aiohttp.ClientSession() as session:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cache-Control': 'no-cache'
        }
        
        try:
            async with session.get(LETOBASKET_URL, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    print("🔍 АНАЛИЗ СТРУКТУРЫ САЙТА")
                    print("=" * 50)
                    
                    # Ищем все даты на странице
                    date_pattern = r'\d{2}\.\d{2}\.\d{4}'
                    dates = re.findall(date_pattern, content)
                    unique_dates = list(set(dates))
                    
                    print(f"📅 Найдено дат: {len(unique_dates)}")
                    for date in sorted(unique_dates):
                        print(f"   {date}")
                    
                    print()
                    
                    # Ищем все упоминания PullUP
                    pullup_patterns = [
                        r'pull\s*up',
                        r'PullUP',
                        r'Pull\s*Up',
                        r'Pull\s*Up-Фарм'
                    ]
                    
                    pullup_matches = []
                    for pattern in pullup_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            # Получаем контекст вокруг совпадения
                            start = max(0, match.start() - 100)
                            end = min(len(content), match.end() + 100)
                            context = content[start:end]
                            pullup_matches.append(context.strip())
                    
                    print(f"🏀 Найдено упоминаний PullUP: {len(pullup_matches)}")
                    for i, match in enumerate(pullup_matches[:10], 1):  # Показываем первые 10
                        print(f"   {i}. {match}")
                    
                    print()
                    
                    # Ищем игры в формате "команда vs команда"
                    vs_patterns = [
                        r'([^-]+?)\s+vs\s+([^-]+?)(?:\s|$)',
                        r'([^-]+?)\s+-\s+([^-]+?)(?:\s|$)',
                        r'([^-]+?)\s+против\s+([^-]+?)(?:\s|$)',
                    ]
                    
                    all_games = []
                    for pattern in vs_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            team1, team2 = match
                            team1 = team1.strip()
                            team2 = team2.strip()
                            
                            # Фильтруем слишком короткие названия
                            if len(team1) > 2 and len(team2) > 2:
                                all_games.append((team1, team2))
                    
                    print(f"🎮 Найдено игр: {len(all_games)}")
                    for i, (team1, team2) in enumerate(all_games[:15], 1):  # Показываем первые 15
                        print(f"   {i}. {team1} vs {team2}")
                    
                    print()
                    
                    # Ищем строки с датами и временем
                    datetime_pattern = r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})'
                    datetime_matches = re.findall(datetime_pattern, content)
                    
                    print(f"⏰ Найдено дат с временем: {len(datetime_matches)}")
                    for i, (date, time) in enumerate(datetime_matches[:10], 1):
                        print(f"   {i}. {date} {time}")
                    
                    print()
                    
                    # Ищем таблицы
                    soup = BeautifulSoup(content, 'html.parser')
                    tables = soup.find_all('table')
                    
                    print(f"📊 Найдено таблиц: {len(tables)}")
                    for i, table in enumerate(tables[:5], 1):  # Показываем первые 5 таблиц
                        rows = table.find_all('tr')
                        print(f"   Таблица {i}: {len(rows)} строк")
                        
                        # Показываем первые 3 строки каждой таблицы
                        for j, row in enumerate(rows[:3], 1):
                            cells = row.find_all(['td', 'th'])
                            row_text = ' | '.join([cell.get_text().strip() for cell in cells])
                            if row_text:
                                print(f"     Строка {j}: {row_text}")
                    
                else:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_site_structure())
