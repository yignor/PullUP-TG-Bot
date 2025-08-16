#!/usr/bin/env python3
"""
Отладочный скрипт для анализа нового подхода
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def debug_new_approach():
    """Анализирует новый подход поиска"""
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
                    
                    print("🔍 НОВЫЙ ПОДХОД ПОИСКА")
                    print("=" * 50)
                    
                    # Ищем дату на странице
                    date_match = re.search(r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})', page_text)
                    current_date = date_match.group(1) if date_match else None
                    print(f"📅 Текущая дата: {current_date}")
                    
                    # Ищем строки с PullUP и текущей датой
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
                    
                    for pattern in pullup_patterns:
                        print(f"\n🔍 Поиск паттерна: {pattern}")
                        
                        # Ищем строки, содержащие PullUP и дату
                        pullup_lines = re.findall(rf'{current_date}[^-\n]*-\s*[^-]*{pattern}[^-]*', page_text, re.IGNORECASE)
                        
                        print(f"   Найдено строк: {len(pullup_lines)}")
                        
                        for line in pullup_lines:
                            print(f"   🔍 Найдена строка: {line}")
                            
                            # Извлекаем время из строки
                            time_match = re.search(rf'{current_date}\s+(\d{{1,2}}[:.]\d{{2}})', line)
                            game_time = time_match.group(1) if time_match else None
                            print(f"      Время: {game_time}")
                            
                            # Извлекаем команды из строки
                            teams_match = re.search(r'-\s*([^-]+?)\s*-\s*([^-]+?)(?:\s|$)', line)
                            if teams_match:
                                team1 = teams_match.group(1).strip()
                                team2 = teams_match.group(2).strip()
                                print(f"      Команда 1: {team1}")
                                print(f"      Команда 2: {team2}")
                                
                                # Определяем, какая команда содержит PullUP
                                if re.search(pattern, team1, re.IGNORECASE):
                                    print(f"      ✅ PullUP найден в команде 1")
                                elif re.search(pattern, team2, re.IGNORECASE):
                                    print(f"      ✅ PullUP найден в команде 2")
                                else:
                                    print(f"      ❌ PullUP не найден в командах")
                            else:
                                print(f"      ❌ Команды не извлечены")
                    
                else:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_new_approach())
