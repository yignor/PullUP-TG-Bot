#!/usr/bin/env python3
"""
Отладочный скрипт для анализа блока игр
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def debug_games_block():
    """Анализирует блок игр"""
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
                    
                    # Ищем блок между "ТАБЛО ИГР" и "online видеотрансляции игр доступны на странице"
                    start_marker = "ТАБЛО ИГР"
                    end_marker = "online видеотрансляции игр доступны на странице"
                    
                    start_index = page_text.find(start_marker)
                    end_index = page_text.find(end_marker)
                    
                    print("🔍 АНАЛИЗ БЛОКА ИГР")
                    print("=" * 50)
                    
                    if start_index != -1 and end_index != -1 and start_index < end_index:
                        # Извлекаем блок игр
                        games_block = page_text[start_index:end_index]
                        print(f"✅ Найден блок игр между маркерами")
                        print(f"Размер блока: {len(games_block)} символов")
                        
                        # Ищем дату в блоке игр
                        date_match = re.search(r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})', games_block)
                        current_date = date_match.group(1) if date_match else None
                        print(f"📅 Дата игр: {current_date}")
                        
                        print(f"\n📄 СОДЕРЖИМОЕ БЛОКА ИГР:")
                        print("-" * 40)
                        print(games_block)
                        
                        print(f"\n🔍 ПОИСК PULLUP:")
                        print("-" * 20)
                        
                        # Ищем все вариации PullUP
                        pullup_patterns = [
                            r'PULL UP ФАРМ',
                            r'PULL UP',
                            r'pull up фарм',
                            r'pull up',
                            r'PullUP Фарм',
                            r'PullUP'
                        ]
                        
                        for pattern in pullup_patterns:
                            matches = re.findall(pattern, games_block, re.IGNORECASE)
                            if matches:
                                print(f"✅ Паттерн '{pattern}': найдено {len(matches)} совпадений")
                                for match in matches:
                                    print(f"   - {match}")
                            else:
                                print(f"❌ Паттерн '{pattern}': не найдено")
                        
                        # Ищем любые упоминания pull
                        print(f"\n🔍 ПОИСК ЛЮБЫХ УПОМИНАНИЙ PULL:")
                        print("-" * 35)
                        pull_matches = re.findall(r'pull', games_block, re.IGNORECASE)
                        if pull_matches:
                            print(f"✅ Найдено {len(pull_matches)} упоминаний 'pull'")
                        else:
                            print(f"❌ Упоминания 'pull' не найдены")
                        
                        # Ищем любые упоминания up
                        print(f"\n🔍 ПОИСК ЛЮБЫХ УПОМИНАНИЙ UP:")
                        print("-" * 30)
                        up_matches = re.findall(r'\bup\b', games_block, re.IGNORECASE)
                        if up_matches:
                            print(f"✅ Найдено {len(up_matches)} упоминаний 'up'")
                        else:
                            print(f"❌ Упоминания 'up' не найдены")
                        
                        # Ищем команды в блоке
                        print(f"\n🏀 ПОИСК КОМАНД:")
                        print("-" * 20)
                        
                        # Ищем слова, которые могут быть названиями команд
                        team_words = re.findall(r'\b[A-Z][A-Z\s]+\b', games_block)
                        if team_words:
                            print(f"✅ Найдено {len(team_words)} потенциальных команд:")
                            for word in team_words[:10]:  # Показываем первые 10
                                print(f"   - {word}")
                        else:
                            print(f"❌ Команды не найдены")
                        
                    else:
                        print("❌ Не найдены ожидаемые маркеры")
                        print(f"start_marker позиция: {start_index}")
                        print(f"end_marker позиция: {end_index}")
                        
                else:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_games_block())
