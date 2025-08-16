#!/usr/bin/env python3
"""
Отладочный скрипт для анализа одной конкретной игры
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def debug_single_game():
    """Анализирует одну конкретную игру"""
    game_url = "http://letobasket.ru/P2025/podrobno.php?id=228&id1=S"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(game_url) as response:
                if response.status == 200:
                    # Получаем контент с правильной кодировкой
                    html_content = await response.read()
                    
                    # Пытаемся декодировать с правильной кодировкой
                    try:
                        # Сначала пробуем UTF-8
                        html_text = html_content.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            # Если не получилось, пробуем Windows-1251
                            html_text = html_content.decode('windows-1251')
                        except UnicodeDecodeError:
                            # Последняя попытка - cp1251
                            html_text = html_content.decode('cp1251')
                    
                    # Парсим HTML
                    soup = BeautifulSoup(html_text, 'html.parser')
                    
                    print("🔍 АНАЛИЗ ОДНОЙ ИГРЫ")
                    print("=" * 40)
                    print(f"URL: {game_url}")
                    print(f"Размер HTML: {len(html_content)} символов")
                    
                    # Получаем весь текст
                    page_text = soup.get_text()
                    print(f"Размер текста: {len(page_text)} символов")
                    
                    # Ищем ключевые элементы
                    print(f"\n🔍 ПОИСК КЛЮЧЕВЫХ ЭЛЕМЕНТОВ:")
                    
                    # 1. Ищем el-tournament-head
                    head_block = soup.find('div', class_='el-tournament-head')
                    if head_block:
                        head_text = head_block.get_text(separator=' ', strip=True)
                        print(f"✅ el-tournament-head найден: {head_text[:200]}...")
                    else:
                        print(f"❌ el-tournament-head не найден")
                    
                    # 2. Ищем left/right блоки
                    left_block = soup.find('div', class_='left')
                    right_block = soup.find('div', class_='right')
                    
                    if left_block:
                        left_text = left_block.get_text(separator=' ', strip=True)
                        print(f"✅ left блок найден: {left_text[:200]}...")
                    else:
                        print(f"❌ left блок не найден")
                    
                    if right_block:
                        right_text = right_block.get_text(separator=' ', strip=True)
                        print(f"✅ right блок найден: {right_text[:200]}...")
                    else:
                        print(f"❌ right блок не найден")
                    
                    # 3. Ищем comman/name блоки
                    comman_blocks = soup.find_all('div', class_='comman')
                    name_blocks = soup.find_all('div', class_='name')
                    
                    print(f"✅ comman блоков: {len(comman_blocks)}")
                    print(f"✅ name блоков: {len(name_blocks)}")
                    
                    for i, comman in enumerate(comman_blocks[:3], 1):
                        comman_text = comman.get_text(strip=True)
                        print(f"   {i}. comman: {comman_text}")
                    
                    for i, name in enumerate(name_blocks[:3], 1):
                        name_text = name.get_text(strip=True)
                        print(f"   {i}. name: {name_text}")
                    
                    # 4. Ищем команды в тексте
                    print(f"\n🏀 ПОИСК КОМАНД В ТЕКСТЕ:")
                    
                    # Ищем паттерны команд
                    team_patterns = [
                        r'([А-Я][а-я\s]+)\s+[-—]\s+([А-Я][а-я\s]+)',
                        r'([А-Я][а-я\s]+)\s+vs\s+([А-Я][а-я\s]+)',
                        r'([А-Я][а-я\s]+)\s+против\s+([А-Я][а-я\s]+)',
                    ]
                    
                    for pattern in team_patterns:
                        matches = re.findall(pattern, page_text)
                        if matches:
                            print(f"   ✅ Паттерн '{pattern}': найдено {len(matches)} совпадений")
                            for match in matches[:3]:
                                print(f"      {match[0].strip()} vs {match[1].strip()}")
                        else:
                            print(f"   ❌ Паттерн '{pattern}': не найдено")
                    
                    # 5. Ищем время
                    print(f"\n🕐 ПОИСК ВРЕМЕНИ:")
                    time_patterns = [
                        r'\d{1,2}[:.]\d{2}',
                        r'\d{1,2}[./]\d{1,2}[./]\d{2,4}',
                        r'\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)',
                    ]
                    
                    for pattern in time_patterns:
                        matches = re.findall(pattern, page_text)
                        if matches:
                            print(f"   ✅ Паттерн '{pattern}': найдено {len(matches)} совпадений")
                            for match in matches[:3]:
                                print(f"      {match}")
                        else:
                            print(f"   ❌ Паттерн '{pattern}': не найдено")
                    
                    # 6. Показываем первые 500 символов текста
                    print(f"\n📄 ПЕРВЫЕ 500 СИМВОЛОВ ТЕКСТА:")
                    print(page_text[:500])
                    
                else:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_single_game())
