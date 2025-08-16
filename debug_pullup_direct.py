#!/usr/bin/env python3
"""
Отладочный скрипт для прямого поиска PullUP
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def debug_pullup_direct():
    """Анализирует прямой поиск PullUP"""
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
                    
                    print("🔍 ПРЯМОЙ ПОИСК PULLUP")
                    print("=" * 50)
                    
                    # Ищем дату на странице
                    date_match = re.search(r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})', page_text)
                    current_date = date_match.group(1) if date_match else None
                    print(f"📅 Текущая дата: {current_date}")
                    
                    # Ищем строки с PullUP и текущей датой напрямую
                    pullup_date_pattern = rf'{current_date}[^-]*-\s*([^-]+?)\s*-\s*([^-]+?)(?:\s|$)'
                    pullup_matches = re.findall(pullup_date_pattern, page_text, re.IGNORECASE)
                    
                    print(f"✅ Найдено строк с датой {current_date}: {len(pullup_matches)}")
                    
                    for i, match in enumerate(pullup_matches, 1):
                        team1 = match[0].strip()
                        team2 = match[1].strip()
                        
                        print(f"\n🎮 Строка {i}:")
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
                    
                    # Также покажем все строки с PullUP
                    print(f"\n📋 ВСЕ СТРОКИ С PULLUP:")
                    pullup_lines = re.findall(r'[^-\n]*pull[^-\n]*up[^-\n]*', page_text, re.IGNORECASE)
                    for line in pullup_lines:
                        print(f"   - {line.strip()}")
                    
                else:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_pullup_direct())
