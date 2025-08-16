#!/usr/bin/env python3
"""
Отладочный скрипт для анализа содержимого блока игр
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def debug_block_content():
    """Анализирует содержимое блока игр"""
    url = "http://letobasket.ru/"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Парсим HTML
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Ищем блок между "ТАБЛО ИГР" и "online видеотрансляции игр доступны на странице"
                    page_text = soup.get_text()
                    
                    # Обновленные маркеры
                    start_marker = "ТАБЛО ИГР"
                    end_marker = "online видеотрансляции игр доступны на странице"
                    
                    start_index = page_text.find(start_marker)
                    end_index = page_text.find(end_marker)
                    
                    print("🔍 АНАЛИЗ БЛОКА ИГР")
                    print("=" * 50)
                    
                    if start_index != -1 and end_index != -1 and start_index < end_index:
                        # Извлекаем нужный блок текста
                        target_block = page_text[start_index:end_index]
                        print(f"✅ Найден блок игр между маркерами")
                        print(f"Размер блока: {len(target_block)} символов")
                        
                        print(f"\n📄 СОДЕРЖИМОЕ БЛОКА:")
                        print("-" * 30)
                        print(target_block)
                        
                        print(f"\n🔍 ПОИСК PULLUP:")
                        print("-" * 20)
                        
                        # Ищем все вариации PullUP
                        pullup_patterns = [
                            r'pull\s*up',
                            r'pullup',
                            r'PullUP',
                            r'Pull UP',
                            r'PULL UP',
                            r'pull\s*up\s*фарм',
                            r'PullUP\s*фарм',
                            r'Pull UP\s*фарм',
                            r'PULL UP\s*фарм'
                        ]
                        
                        for pattern in pullup_patterns:
                            matches = re.findall(pattern, target_block, re.IGNORECASE)
                            if matches:
                                print(f"✅ Паттерн '{pattern}': найдено {len(matches)} совпадений")
                                for match in matches:
                                    print(f"   - {match}")
                            else:
                                print(f"❌ Паттерн '{pattern}': не найдено")
                        
                        # Ищем любые упоминания pull
                        print(f"\n🔍 ПОИСК ЛЮБЫХ УПОМИНАНИЙ PULL:")
                        print("-" * 35)
                        pull_matches = re.findall(r'pull', target_block, re.IGNORECASE)
                        if pull_matches:
                            print(f"✅ Найдено {len(pull_matches)} упоминаний 'pull'")
                        else:
                            print(f"❌ Упоминания 'pull' не найдены")
                        
                        # Ищем любые упоминания up
                        print(f"\n🔍 ПОИСК ЛЮБЫХ УПОМИНАНИЙ UP:")
                        print("-" * 30)
                        up_matches = re.findall(r'\bup\b', target_block, re.IGNORECASE)
                        if up_matches:
                            print(f"✅ Найдено {len(up_matches)} упоминаний 'up'")
                        else:
                            print(f"❌ Упоминания 'up' не найдены")
                        
                    else:
                        print("❌ Не найдены ожидаемые маркеры")
                        print(f"start_marker позиция: {start_index}")
                        print(f"end_marker позиция: {end_index}")
                        
                else:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_block_content())
