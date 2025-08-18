#!/usr/bin/env python3
"""
Скрипт для отладки содержимого строк с играми
"""
import sys
import os
sys.path.append('..')

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def debug_row_content():
    """Отлаживает содержимое строк с играми"""
    print("🔍 ОТЛАДКА СОДЕРЖИМОГО СТРОК С ИГРАМИ")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://letobasket.ru/') as response:
                content = await response.text()
                
        soup = BeautifulSoup(content, 'html.parser')
        
        # Ищем строки с PullUP
        game_rows = soup.find_all('tr')
        
        for i, row in enumerate(game_rows):
            row_text = row.get_text()
            
            # Проверяем, содержит ли строка PullUP
            if re.search(r'pull\s*up', row_text, re.IGNORECASE):
                print(f"\n🏀 СТРОКА #{i+1} С PULLUP:")
                print(f"   Полный текст: {row_text}")
                
                # Ищем дату
                date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', row_text)
                if date_match:
                    print(f"   Найдена дата: {date_match.group(1)}")
                else:
                    print(f"   Дата НЕ найдена")
                
                # Ищем счет
                score_match = re.search(r'(\d+)\s*:\s*(\d+)', row_text)
                if score_match:
                    print(f"   Найден счет: {score_match.group(1)}:{score_match.group(2)}")
                else:
                    print(f"   Счет НЕ найден")
                
                # Показываем HTML структуру
                cells = row.find_all(['td', 'th'])
                print(f"   Ячеек: {len(cells)}")
                for j, cell in enumerate(cells[:3]):  # Показываем первые 3 ячейки
                    cell_text = cell.get_text().strip()
                    print(f"     Ячейка {j+1}: '{cell_text}'")
                
                print("-" * 40)
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_row_content())
