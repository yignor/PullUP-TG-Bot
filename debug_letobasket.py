#!/usr/bin/env python3
"""
Отладочный скрипт для анализа структуры страницы letobasket.ru
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def debug_letobasket_page():
    """Анализирует структуру страницы letobasket.ru"""
    url = "http://letobasket.ru/"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Парсим HTML
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    print("🔍 АНАЛИЗ СТРУКТУРЫ СТРАНИЦЫ LETOBASKET.RU")
                    print("=" * 60)
                    
                    # 1. Получаем весь текст страницы
                    page_text = soup.get_text()
                    print(f"📄 Общий размер текста: {len(page_text)} символов")
                    
                    # 2. Ищем ключевые маркеры
                    markers = [
                        "Табло игры",
                        "online видеотрансляции игр доступны на странице",
                        "PullUP",
                        "pull up",
                        "pullup",
                        "игра",
                        "матч",
                        "команда"
                    ]
                    
                    print("\n🎯 ПОИСК КЛЮЧЕВЫХ МАРКЕРОВ:")
                    for marker in markers:
                        count = page_text.lower().count(marker.lower())
                        if count > 0:
                            print(f"   ✅ '{marker}': найдено {count} раз")
                        else:
                            print(f"   ❌ '{marker}': не найдено")
                    
                    # 3. Ищем все ссылки
                    links = soup.find_all('a', href=True)
                    game_links = []
                    other_links = []
                    
                    for link in links:
                        href = link['href'].lower()
                        if any(k in href for k in ['game.html', 'gameid=', 'match', 'podrobno', 'protocol', 'game']):
                            game_links.append(link['href'])
                        else:
                            other_links.append(link['href'])
                    
                    print(f"\n🔗 ССЫЛКИ:")
                    print(f"   Игровые ссылки: {len(game_links)}")
                    print(f"   Остальные ссылки: {len(other_links)}")
                    
                    if game_links:
                        print("\n🎮 ИГРОВЫЕ ССЫЛКИ:")
                        for i, link in enumerate(game_links[:10], 1):
                            print(f"   {i}. {link}")
                    
                    # 4. Ищем блоки с играми
                    print("\n📋 БЛОКИ С ИГРАМИ:")
                    
                    # Ищем div с классами, которые могут содержать игры
                    game_blocks = soup.find_all(['div', 'table'], class_=re.compile(r'game|match|tournament|schedule', re.I))
                    print(f"   Найдено блоков с играми: {len(game_blocks)}")
                    
                    for i, block in enumerate(game_blocks[:5], 1):
                        block_text = block.get_text()[:200]
                        print(f"   {i}. {block.name}.{block.get('class', [])}: {block_text}...")
                    
                    # 5. Ищем таблицы
                    tables = soup.find_all('table')
                    print(f"\n📊 ТАБЛИЦЫ:")
                    print(f"   Найдено таблиц: {len(tables)}")
                    
                    for i, table in enumerate(tables[:3], 1):
                        table_text = table.get_text()[:200]
                        print(f"   {i}. {table.get('class', [])}: {table_text}...")
                    
                    # 6. Ищем текст с PullUP
                    pullup_patterns = [
                        r'pull\s*up',
                        r'pullup',
                        r'PullUP',
                        r'Pull UP',
                        r'PULL UP'
                    ]
                    
                    print(f"\n🏀 ПОИСК PULLUP:")
                    for pattern in pullup_patterns:
                        matches = re.findall(pattern, page_text, re.IGNORECASE)
                        if matches:
                            print(f"   ✅ '{pattern}': найдено {len(matches)} раз")
                            for match in matches[:3]:
                                # Находим контекст вокруг совпадения
                                start = max(0, page_text.lower().find(match.lower()) - 50)
                                end = min(len(page_text), start + 150)
                                context = page_text[start:end]
                                print(f"      Контекст: ...{context}...")
                        else:
                            print(f"   ❌ '{pattern}': не найдено")
                    
                    # 7. Анализ структуры HTML
                    print(f"\n🏗️ СТРУКТУРА HTML:")
                    main_content = soup.find('main') or soup.find('div', id='content') or soup.find('body')
                    if main_content:
                        print(f"   Основной контент: {main_content.name}")
                        children = list(main_content.children)[:10]
                        for i, child in enumerate(children, 1):
                            if hasattr(child, 'name') and child.name:
                                print(f"   {i}. {child.name}: {child.get('class', [])}")
                    
                else:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_letobasket_page())
