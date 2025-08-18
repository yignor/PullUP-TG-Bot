#!/usr/bin/env python3
"""
Скрипт для проверки текущих игр на сайте
"""
import sys
import os
sys.path.append('..')

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def check_current_games():
    """Проверяет текущие игры на сайте"""
    print("🔍 ПРОВЕРКА ТЕКУЩИХ ИГР НА САЙТЕ")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://letobasket.ru/') as response:
                content = await response.text()
                
        soup = BeautifulSoup(content, 'html.parser')
        
        # Ищем все таблицы
        tables = soup.find_all('table')
        print(f"📊 Найдено таблиц: {len(tables)}")
        
        # Ищем игры с PullUP
        pullup_games = []
        
        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_text = ' '.join([cell.get_text().strip() for cell in cells])
                
                # Ищем PullUP команды
                if re.search(r'pull\s*up', row_text, re.IGNORECASE):
                    print(f"\n🏀 НАЙДЕНА ИГРА PULLUP в таблице {i+1}:")
                    print(f"   Текст: {row_text[:200]}...")
                    
                    # Ищем дату
                    date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', row_text)
                    if date_match:
                        game_date = date_match.group(1)
                        print(f"   Дата: {game_date}")
                        
                        # Ищем счет
                        score_match = re.search(r'(\d+)\s*[:\-–]\s*(\d+)', row_text)
                        if score_match:
                            score1, score2 = score_match.groups()
                            print(f"   Счет: {score1}:{score2}")
                            
                            pullup_games.append({
                                'date': game_date,
                                'score': f"{score1}:{score2}",
                                'text': row_text[:100]
                            })
        
        print(f"\n📈 ИТОГО НАЙДЕНО ИГР PULLUP: {len(pullup_games)}")
        
        if pullup_games:
            print("\n🎯 ДЕТАЛИ ИГР:")
            for i, game in enumerate(pullup_games, 1):
                print(f"   {i}. Дата: {game['date']}, Счет: {game['score']}")
                print(f"      Текст: {game['text']}...")
        else:
            print("✅ Игр PullUP не найдено")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(check_current_games())
