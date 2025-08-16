#!/usr/bin/env python3
"""
Отладочный скрипт для поиска игр с IT Basket
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

def debug_it_basket_games(html_content):
    """Анализирует игры с IT Basket"""
    print("🔍 АНАЛИЗ ИГР С IT BASKET")
    print("=" * 60)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Ищем все игры с IT Basket
    it_basket_patterns = [
        r'IT\s*Basket',
        r'it\s*basket',
        r'It\s*Basket'
    ]
    
    # Ищем строки с играми
    game_rows = soup.find_all('tr')
    
    it_basket_games = []
    
    for i, row in enumerate(game_rows):
        row_text = row.get_text()
        
        # Проверяем, содержит ли строка IT Basket
        is_it_basket_game = any(re.search(pattern, row_text, re.IGNORECASE) for pattern in it_basket_patterns)
        
        if is_it_basket_game:
            print(f"\n🏀 НАЙДЕНА ИГРА С IT BASKET (строка {i+1}):")
            print(f"   Текст: {row_text.strip()}")
            
            # Извлекаем счет
            score_match = re.search(r'(\d+)\s*:\s*(\d+)', row_text)
            if score_match:
                score1, score2 = score_match.groups()
                print(f"   📊 Счет: {score1} : {score2}")
            
            # Проверяем, есть ли PullUP в этой игре
            pullup_patterns = [
                r'pull\s*up',
                r'PullUP',
                r'Pull\s*Up'
            ]
            
            is_pullup_game = any(re.search(pattern, row_text, re.IGNORECASE) for pattern in pullup_patterns)
            if is_pullup_game:
                print(f"   ✅ ЭТО ИГРА PULLUP vs IT BASKET!")
            else:
                print(f"   ❌ Не игра PullUP")
            
            it_basket_games.append({
                'row_index': i,
                'text': row_text.strip(),
                'score': score_match.groups() if score_match else None,
                'is_pullup': is_pullup_game
            })
    
    print(f"\n📈 ИТОГО НАЙДЕНО ИГР С IT BASKET: {len(it_basket_games)}")
    
    # Ищем игры PullUP vs IT Basket
    pullup_vs_it_basket = [game for game in it_basket_games if game['is_pullup']]
    
    if pullup_vs_it_basket:
        print(f"\n🏁 ИГРЫ PULLUP vs IT BASKET:")
        for i, game in enumerate(pullup_vs_it_basket, 1):
            print(f"   {i}. Строка {game['row_index']+1}")
            print(f"      Текст: {game['text']}")
            if game['score']:
                print(f"      Счет: {game['score'][0]} : {game['score'][1]}")
    
    return it_basket_games

async def main():
    """Основная функция"""
    print("🔍 АНАЛИЗ ИГР С IT BASKET")
    print("=" * 60)
    
    try:
        # Получаем свежий контент
        print("📡 Получаем данные с сайта...")
        html_content = await get_fresh_page_content()
        
        # Анализируем игры с IT Basket
        it_basket_games = debug_it_basket_games(html_content)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
