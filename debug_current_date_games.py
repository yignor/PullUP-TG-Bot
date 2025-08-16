#!/usr/bin/env python3
"""
Отладочный скрипт для анализа игр с текущей датой
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def debug_current_date_games():
    """Анализирует игры с текущей датой"""
    url = "http://letobasket.ru/"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Парсим HTML
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Получаем весь текст страницы
                    page_text = soup.get_text()
                    
                    print("🔍 АНАЛИЗ ИГР С ТЕКУЩЕЙ ДАТОЙ")
                    print("=" * 50)
                    
                    # Ищем дату на странице
                    date_match = re.search(r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})', page_text)
                    current_date = date_match.group(1) if date_match else None
                    print(f"📅 Текущая дата: {current_date}")
                    
                    # Ищем игры с текущей датой
                    current_date_games_pattern = rf'{current_date}\s+(\d{{1,2}}[:.]\d{{2}})\s*\([^)]*\)\s*-\s*([^-]+?)\s*-\s*([^-]+?)(?:\s|$)'
                    current_date_games = re.findall(current_date_games_pattern, page_text, re.IGNORECASE)
                    
                    print(f"✅ Найдено игр с датой {current_date}: {len(current_date_games)}")
                    
                    for i, game_match in enumerate(current_date_games, 1):
                        game_time = game_match[0]
                        team1 = game_match[1].strip()
                        team2 = game_match[2].strip()
                        
                        print(f"\n🎮 Игра {i}:")
                        print(f"   🕐 Время: {game_time}")
                        print(f"   🏀 Команда 1: {team1}")
                        print(f"   🏀 Команда 2: {team2}")
                        
                        # Проверяем на PullUP
                        pullup_patterns = [
                            r'PULL UP ФАРМ',
                            r'PULL UP-ФАРМ',
                            r'Pull Up-Фарм',
                            r'pull up-фарм',
                            r'PULL UP',
                            r'Pull Up',
                            r'pull up',
                            r'PullUP Фарм',
                            r'PullUP'
                        ]
                        
                        pullup_found = False
                        for pattern in pullup_patterns:
                            if re.search(pattern, team1, re.IGNORECASE) or re.search(pattern, team2, re.IGNORECASE):
                                pullup_found = True
                                print(f"   ✅ НАЙДЕН PULLUP!")
                                break
                        
                        if not pullup_found:
                            print(f"   ❌ PullUP не найден")
                    
                    # Также покажем все строки с датой
                    print(f"\n📋 ВСЕ СТРОКИ С ДАТОЙ {current_date}:")
                    all_date_lines = re.findall(rf'{current_date}[^-\n]*', page_text)
                    for line in all_date_lines:
                        print(f"   - {line.strip()}")
                    
                else:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_current_date_games())
