#!/usr/bin/env python3
"""
Простой парсер игр PullUP - ищет конкретные строки на сайте
"""

import asyncio
import re
import aiohttp
from datetime import datetime, timezone, timedelta

LETOBASKET_URL = "http://letobasket.ru/"

async def simple_pullup_parser():
    """Простой парсер игр PullUP"""
    
    async with aiohttp.ClientSession() as session:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cache-Control': 'no-cache'
        }
        
        try:
            async with session.get(LETOBASKET_URL, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    print("🏀 ПАРСЕР ИГР PULLUP")
                    print("=" * 50)
                    
                    # Получаем текущую дату
                    moscow_tz = timezone(timedelta(hours=3))
                    current_date = datetime.now(moscow_tz).strftime('%d.%m.%Y')
                    
                    print(f"🎯 ИГРЫ PULLUP (текущая дата: {current_date})")
                    print("=" * 50)
                    
                    # Ищем все строки, содержащие PullUP
                    pullup_patterns = [
                        r'pull\s*up',
                        r'PullUP',
                        r'Pull\s*Up',
                        r'Pull\s*Up-Фарм'
                    ]
                    
                    found_lines = []
                    lines = content.split('\n')
                    
                    for line in lines:
                        for pattern in pullup_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                # Получаем контекст вокруг строки
                                start = max(0, lines.index(line) - 2)
                                end = min(len(lines), lines.index(line) + 3)
                                context = '\n'.join(lines[start:end])
                                found_lines.append(context.strip())
                                break
                    
                    if found_lines:
                        print(f"📋 Найдено строк с PullUP: {len(found_lines)}")
                        print()
                        
                        for i, line in enumerate(found_lines[:10], 1):  # Показываем первые 10
                            print(f"{i}. {line[:200]}...")  # Обрезаем длинные строки
                    else:
                        print("📅 Строк с PullUP не найдено")
                    
                    print()
                    print("🔍 ПОИСК КОНКРЕТНЫХ ИГР")
                    print("=" * 50)
                    
                    # Ищем конкретные игры, которые мы видели в анализе
                    specific_games = [
                        "27.08.2025 20.30 (MarvelHall) - Кудрово - Pull Up-Фарм",
                        "27.08.2025 21.45 (MarvelHall) - Old Stars - Pull Up",
                        "30.08.2025 12.30 (MarvelHall) - Тосно - Pull Up-Фарм"
                    ]
                    
                    found_specific = []
                    for game in specific_games:
                        if game in content:
                            found_specific.append(game)
                    
                    if found_specific:
                        print(f"📋 Найдено конкретных игр: {len(found_specific)}")
                        print()
                        
                        for i, game in enumerate(found_specific, 1):
                            # Форматируем время (заменяем точку на двоеточие)
                            game_formatted = re.sub(r'(\d{2})\.(\d{2})', r'\1:\2', game)
                            print(f"{i}. ⏰ {game_formatted}")
                    else:
                        print("📅 Конкретные игры не найдены")
                    
                    print()
                    print("🔍 ПОИСК ПО ПАТТЕРНАМ")
                    print("=" * 50)
                    
                    # Ищем по общим паттернам
                    patterns_to_try = [
                        r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2})\s+\([^)]+\)\s*-\s*[^-]+?\s*-\s*[^-]*?Pull[^-]*?(?:\s|$)',
                        r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2})\s+\([^)]+\)\s*-\s*[^-]*?Pull[^-]*?\s*-\s*[^-]+?(?:\s|$)',
                        r'(\d{2}\.\d{2}\.\d{4})-\s*[^-]+?\s*-\s*[^-]*?Pull[^-]*?\s*(\d+:\d+)',
                    ]
                    
                    for pattern in patterns_to_try:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            print(f"📋 Паттерн найден: {len(matches)} совпадений")
                            for match in matches[:5]:  # Показываем первые 5
                                print(f"   {match}")
                            break
                    else:
                        print("📅 Паттерны не найдены")
                    
                else:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(simple_pullup_parser())
