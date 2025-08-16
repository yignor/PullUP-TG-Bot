#!/usr/bin/env python3
"""
Отладочный скрипт для анализа контекста игр PullUP
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def debug_context():
    """Анализирует контекст игр PullUP"""
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
                    
                    # Ищем PullUP
                    pullup_pattern = r'pull\s*up'
                    matches = re.findall(pullup_pattern, page_text, re.IGNORECASE)
                    
                    print("🔍 АНАЛИЗ КОНТЕКСТА ИГР PULLUP")
                    print("=" * 50)
                    print(f"Найдено совпадений: {len(matches)}")
                    
                    for i, match in enumerate(matches[:3], 1):  # Анализируем первые 3
                        print(f"\n🎮 АНАЛИЗ ИГРЫ {i}:")
                        print("-" * 30)
                        
                        # Находим позицию совпадения
                        match_pos = page_text.lower().find(match.lower())
                        if match_pos != -1:
                            # Извлекаем контекст
                            start_context = max(0, match_pos - 200)
                            end_context = min(len(page_text), match_pos + 300)
                            context = page_text[start_context:end_context]
                            
                            print(f"Контекст:")
                            print(context)
                            
                            # Ищем команду соперника
                            opponent_patterns = [
                                r'([А-Я][а-я\s]+)\s*[-—]\s*([А-Я][а-я\s]+)',
                                r'([А-Я][а-я\s]+)\s+против\s+([А-Я][а-я\s]+)',
                                r'([А-Я][а-я\s]+)\s+vs\s+([А-Я][а-я\s]+)',
                            ]
                            
                            print(f"\n🔍 ПОИСК СОПЕРНИКА:")
                            for pattern in opponent_patterns:
                                opp_match = re.search(pattern, context)
                                if opp_match:
                                    team1 = opp_match.group(1).strip()
                                    team2 = opp_match.group(2).strip()
                                    print(f"   ✅ Паттерн '{pattern}': {team1} vs {team2}")
                                    
                                    # Определяем соперника
                                    if 'pull' in team1.lower() and 'up' in team1.lower():
                                        print(f"   🏀 Соперник: {team2}")
                                    elif 'pull' in team2.lower() and 'up' in team2.lower():
                                        print(f"   🏀 Соперник: {team1}")
                                    else:
                                        print(f"   ❓ Не удалось определить соперника")
                                else:
                                    print(f"   ❌ Паттерн '{pattern}': не найдено")
                            
                            # Ищем дату и время
                            print(f"\n📅 ПОИСК ДАТЫ И ВРЕМЕНИ:")
                            date_match = re.search(r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})', context)
                            time_match = re.search(r'(\d{1,2}[:.]\d{2})', context)
                            score_match = re.search(r'(\d+[:.]\d+)', context)
                            
                            if date_match:
                                print(f"   📅 Дата: {date_match.group(1)}")
                            if time_match:
                                print(f"   🕐 Время: {time_match.group(1)}")
                            if score_match:
                                print(f"   🏀 Счет: {score_match.group(1)}")
                    
                else:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_context())
