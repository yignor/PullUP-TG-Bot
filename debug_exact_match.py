#!/usr/bin/env python3
"""
Отладочный скрипт для точного поиска строки с IT Basket - Pull Up-Фарм
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def debug_exact_match():
    """Анализирует точную строку с IT Basket - Pull Up-Фарм"""
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
                    
                    print("🔍 ТОЧНЫЙ ПОИСК IT BASKET - PULL UP-ФАРМ")
                    print("=" * 50)
                    
                    # Ищем точную строку
                    exact_pattern = r'16\.08\.2025\s+12\.30\s*\([^)]*\)\s*-\s*IT\s+Basket\s*-\s*Pull\s+Up-Фарм'
                    exact_match = re.search(exact_pattern, page_text, re.IGNORECASE)
                    
                    if exact_match:
                        print(f"✅ Найдена точная строка!")
                        print(f"Строка: {exact_match.group(0)}")
                        
                        # Извлекаем контекст вокруг
                        match_pos = exact_match.start()
                        start_context = max(0, match_pos - 200)
                        end_context = min(len(page_text), match_pos + 300)
                        context = page_text[start_context:end_context]
                        
                        print(f"\n📄 Контекст:")
                        print(context)
                        
                        # Парсим компоненты
                        print(f"\n🔍 ПАРСИНГ КОМПОНЕНТОВ:")
                        
                        # Дата
                        date_match = re.search(r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})', exact_match.group(0))
                        if date_match:
                            print(f"   📅 Дата: {date_match.group(1)}")
                        
                        # Время
                        time_match = re.search(r'(\d{1,2}[:.]\d{2})', exact_match.group(0))
                        if time_match:
                            print(f"   🕐 Время: {time_match.group(1)}")
                        
                        # Место
                        place_match = re.search(r'\(([^)]+)\)', exact_match.group(0))
                        if place_match:
                            print(f"   🏟️ Место: {place_match.group(1)}")
                        
                        # Команды
                        teams_match = re.search(r'-\s*([^-]+)\s*-\s*([^-]+)', exact_match.group(0))
                        if teams_match:
                            team1 = teams_match.group(1).strip()
                            team2 = teams_match.group(2).strip()
                            print(f"   🏀 Команда 1: {team1}")
                            print(f"   🏀 Команда 2: {team2}")
                            
                            # Определяем соперника
                            if 'pull' in team1.lower() and 'up' in team1.lower():
                                print(f"   🎯 Соперник: {team2}")
                            elif 'pull' in team2.lower() and 'up' in team2.lower():
                                print(f"   🎯 Соперник: {team1}")
                        
                        # Ищем ссылку в HTML
                        print(f"\n🔗 ПОИСК ССЫЛКИ:")
                        context_start = html_content.lower().find(context[:50].lower())
                        if context_start != -1:
                            search_start = max(0, context_start - 1000)
                            search_end = min(len(html_content), context_start + 1000)
                            search_area = html_content[search_start:search_end]
                            
                            # Ищем "СТРАНИЦА ИГРЫ"
                            page_link_match = re.search(r'СТРАНИЦА ИГРЫ[^>]*href=["\']([^"\']+)["\']', search_area, re.IGNORECASE)
                            if page_link_match:
                                print(f"   ✅ Ссылка найдена: {page_link_match.group(1)}")
                            else:
                                print(f"   ❌ Ссылка не найдена")
                                
                                # Ищем любые ссылки
                                all_links = re.findall(r'href=["\']([^"\']+)["\']', search_area)
                                if all_links:
                                    print(f"   📋 Найдено {len(all_links)} ссылок в области:")
                                    for link in all_links[:5]:
                                        print(f"      - {link}")
                        else:
                            print(f"   ❌ Контекст не найден в HTML")
                    else:
                        print(f"❌ Точная строка не найдена")
                        
                        # Ищем похожие строки
                        print(f"\n🔍 ПОИСК ПОХОЖИХ СТРОК:")
                        similar_pattern = r'16\.08\.2025.*IT.*Basket.*Pull.*Up'
                        similar_matches = re.findall(similar_pattern, page_text, re.IGNORECASE)
                        if similar_matches:
                            print(f"✅ Найдено {len(similar_matches)} похожих строк:")
                            for match in similar_matches:
                                print(f"   - {match}")
                        else:
                            print(f"❌ Похожие строки не найдены")
                    
                else:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_exact_match())
