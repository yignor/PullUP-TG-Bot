#!/usr/bin/env python3
"""
Отладочный скрипт для анализа структуры таблицы игр
"""

import asyncio
import os
import re
from bs4 import BeautifulSoup
import aiohttp
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

LETOBASKET_URL = "http://letobasket.ru/"

async def get_fresh_page_content():
    """Получает свежий контент страницы"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(LETOBASKET_URL, headers=headers) as response:
            return await response.text()

def debug_table_structure(html_content):
    """Анализирует структуру таблицы"""
    print("🔍 АНАЛИЗ СТРУКТУРЫ ТАБЛИЦЫ")
    print("=" * 60)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Ищем строки с PullUP
    pullup_patterns = [
        r'pull\s*up',
        r'PullUP',
        r'Pull\s*Up'
    ]
    
    game_rows = soup.find_all('tr')
    
    for i, row in enumerate(game_rows):
        row_text = row.get_text()
        
        # Проверяем, содержит ли строка PullUP
        is_pullup_game = any(re.search(pattern, row_text, re.IGNORECASE) for pattern in pullup_patterns)
        
        if is_pullup_game:
            print(f"\n🏀 НАЙДЕНА ИГРА PULLUP (строка {i+1}):")
            print(f"   Полный текст: {row_text.strip()}")
            
            # Анализируем структуру ячеек
            cells = row.find_all('td')
            print(f"   Количество ячеек: {len(cells)}")
            
            for j, cell in enumerate(cells):
                cell_text = cell.get_text().strip()
                if cell_text:
                    print(f"   Ячейка {j+1}: '{cell_text}'")
            
            # Ищем счет
            score_match = re.search(r'(\d+)\s*:\s*(\d+)', row_text)
            if score_match:
                score1, score2 = score_match.groups()
                print(f"   📊 Счет: {score1} : {score2}")
            
            print("-" * 40)

async def main():
    """Основная функция"""
    print("🔍 АНАЛИЗ СТРУКТУРЫ ТАБЛИЦЫ ИГР")
    print("=" * 60)
    
    try:
        # Получаем свежий контент
        print("📡 Получаем данные с сайта...")
        html_content = await get_fresh_page_content()
        
        # Анализируем структуру таблицы
        debug_table_structure(html_content)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
