#!/usr/bin/env python3
"""
Отладочный скрипт для анализа контекста вокруг PullUP
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def debug_pullup_context():
    """Анализирует контекст вокруг PullUP"""
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
                    
                    print("🔍 АНАЛИЗ КОНТЕКСТА PULLUP")
                    print("=" * 50)
                    
                    # Ищем PullUP
                    pullup_pattern = r'PULL UP'
                    matches = re.findall(pullup_pattern, page_text, re.IGNORECASE)
                    
                    print(f"Найдено совпадений: {len(matches)}")
                    
                    for i, match in enumerate(matches[:3], 1):  # Анализируем первые 3
                        print(f"\n🎮 АНАЛИЗ PULLUP {i}:")
                        print("-" * 30)
                        
                        # Находим позицию совпадения
                        match_pos = page_text.lower().find(match.lower())
                        if match_pos != -1:
                            # Извлекаем контекст
                            start_context = max(0, match_pos - 300)
                            end_context = min(len(page_text), match_pos + 400)
                            context = page_text[start_context:end_context]
                            
                            print(f"Контекст:")
                            print(context)
                            
                            # Ищем команду соперника
                            print(f"\n🔍 ПОИСК СОПЕРНИКА:")
                            opponent_patterns = [
                                r'([А-Я][а-я\s]+)\s+vs\s+([А-Я][а-я\s]+)',
                                r'([А-Я][а-я\s]+)\s*[-—]\s*([А-Я][а-я\s]+)',
                                r'([А-Я][а-я\s]+)\s+против\s+([А-Я][а-я\s]+)',
                            ]
                            
                            for pattern in opponent_patterns:
                                opp_match = re.search(pattern, context)
                                if opp_match:
                                    team1 = opp_match.group(1).strip()
                                    team2 = opp_match.group(2).strip()
                                    print(f"   ✅ Паттерн '{pattern}': {team1} vs {team2}")
                                else:
                                    print(f"   ❌ Паттерн '{pattern}': не найдено")
                            
                            # Ищем статус игры
                            print(f"\n📊 ПОИСК СТАТУСА:")
                            status_match = re.search(r'(\d+)ч', context)
                            if status_match:
                                print(f"   ✅ Статус: {status_match.group(1)}ч")
                            else:
                                print(f"   ❌ Статус не найден")
                            
                            # Ищем время
                            print(f"\n🕐 ПОИСК ВРЕМЕНИ:")
                            time_match = re.search(r'(\d{1,2}[:.]\d{2})', context)
                            if time_match:
                                print(f"   ✅ Время: {time_match.group(1)}")
                            else:
                                print(f"   ❌ Время не найдено")
                            
                            # Ищем счет
                            print(f"\n🏀 ПОИСК СЧЕТА:")
                            score_match = re.search(r'(\d+)\s*[-—]\s*(\d+)', context)
                            if score_match:
                                print(f"   ✅ Счет: {score_match.group(1)}:{score_match.group(2)}")
                            else:
                                print(f"   ❌ Счет не найден")
                            
                            # Ищем ссылку в HTML
                            print(f"\n🔗 ПОИСК ССЫЛКИ:")
                            context_start = html_content.lower().find(context[:50].lower())
                            if context_start != -1:
                                search_start = max(0, context_start - 500)
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
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_pullup_context())
