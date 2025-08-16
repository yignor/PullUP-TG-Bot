#!/usr/bin/env python3
"""
Отладочный скрипт для проверки завершенных игр PullUP
"""

import asyncio
import os
import re
from datetime import datetime
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

def extract_current_date(page_text):
    """Извлекает текущую дату со страницы"""
    date_pattern = r'(\d{2}\.\d{2}\.\d{4})'
    date_match = re.search(date_pattern, page_text)
    return date_match.group(1) if date_match else None

def debug_finished_games(html_content, current_date):
    """Отладочная функция для проверки завершенных игр"""
    print(f"🔍 ОТЛАДКА ЗАВЕРШЕННЫХ ИГР НА {current_date}")
    print("=" * 60)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Ищем все строки с играми
    game_rows = soup.find_all('tr')
    print(f"📊 Найдено строк с играми: {len(game_rows)}")
    
    # Ищем строки с PullUP
    pullup_patterns = [
        r'pull\s*up',
        r'PullUP',
        r'Pull\s*Up'
    ]
    
    pullup_games = []
    
    for i, row in enumerate(game_rows):
        row_text = row.get_text()
        row_text_lower = row_text.lower()
        
        # Проверяем, содержит ли строка PullUP
        is_pullup_game = any(re.search(pattern, row_text, re.IGNORECASE) for pattern in pullup_patterns)
        
        # Ищем счет в строке
        score_match = re.search(r'(\d+)\s*:\s*(\d+)', row_text)
        
        if is_pullup_game:
            print(f"\n🏀 НАЙДЕНА ИГРА PULLUP (строка {i+1}):")
            print(f"   Текст: {row_text.strip()}")
            
            # Проверяем атрибуты
            js_period = row.get('js-period')
            js_timer = row.get('js-timer')
            
            print(f"   js-period: {js_period}")
            print(f"   js-timer: {js_timer}")
            
            # Проверяем завершение
            is_finished = False
            if js_period == '4' and js_timer == '0:00':
                is_finished = True
                print("   ✅ Игра завершена (js-period=4, js-timer=0:00)")
            elif js_period == '4' and (js_timer == '0:00' or js_timer == '00:00'):
                is_finished = True
                print("   ✅ Игра завершена (js-period=4, js-timer=00:00)")
            elif '4ч' in row_text or '4 ч' in row_text:
                is_finished = True
                print("   ✅ Игра завершена (найдено '4ч' в тексте)")
            elif score_match:
                is_finished = True
                print("   ✅ Игра завершена (есть полный счет)")
            else:
                print("   ❌ Игра не завершена")
            
            # Ищем счет
            score_match = re.search(r'(\d+)\s*:\s*(\d+)', row_text)
            if score_match:
                score1, score2 = score_match.groups()
                print(f"   📊 Счет: {score1} : {score2}")
            else:
                print("   📊 Счет не найден")
            
            pullup_games.append({
                'row_index': i,
                'text': row_text.strip(),
                'js_period': js_period,
                'js_timer': js_timer,
                'is_finished': is_finished,
                'score': score_match.groups() if score_match else None
            })
    
    print(f"\n📈 ИТОГО НАЙДЕНО ИГР PULLUP: {len(pullup_games)}")
    
    # Проверяем альтернативный метод поиска
    print(f"\n🔍 АЛЬТЕРНАТИВНЫЙ ПОИСК ПО РЕГУЛЯРНЫМ ВЫРАЖЕНИЯМ:")
    
    # Ищем все игры на текущую дату
    all_games_pattern = rf'{current_date}\s+\d{{2}}\.\d{{2}}[^-]*-\s*[^-]+[^-]*-\s*[^-]+'
    all_games = re.findall(all_games_pattern, html_content)
    
    print(f"   Найдено игр на {current_date}: {len(all_games)}")
    
    pullup_games_regex = []
    for i, game_text in enumerate(all_games):
        if any(re.search(pattern, game_text, re.IGNORECASE) for pattern in pullup_patterns):
            print(f"   🏀 Игра {i+1}: {game_text.strip()}")
            
            # Проверяем счет
            score_match = re.search(r'(\d+)\s*:\s*(\d+)', game_text)
            if score_match:
                score1, score2 = score_match.groups()
                print(f"      📊 Счет: {score1} : {score2}")
                pullup_games_regex.append({
                    'index': i,
                    'text': game_text.strip(),
                    'score': (score1, score2)
                })
            else:
                print(f"      📊 Счет не найден")
    
    print(f"\n📈 ИТОГО НАЙДЕНО ИГР PULLUP (regex): {len(pullup_games_regex)}")
    
    return pullup_games, pullup_games_regex

async def main():
    """Основная функция"""
    print("🔍 ОТЛАДКА ЗАВЕРШЕННЫХ ИГР PULLUP")
    print("=" * 60)
    
    try:
        # Получаем свежий контент
        print("📡 Получаем данные с сайта...")
        html_content = await get_fresh_page_content()
        
        # Извлекаем текущую дату
        current_date = extract_current_date(html_content)
        if not current_date:
            print("❌ Не удалось извлечь текущую дату")
            return
        
        print(f"📅 Текущая дата: {current_date}")
        
        # Отлаживаем завершенные игры
        pullup_games, pullup_games_regex = debug_finished_games(html_content, current_date)
        
        print(f"\n🎯 РЕЗУЛЬТАТ ОТЛАДКИ:")
        print(f"   Игр найдено через DOM: {len(pullup_games)}")
        print(f"   Игр найдено через regex: {len(pullup_games_regex)}")
        
        # Проверяем, какие игры завершены
        finished_games = [game for game in pullup_games if game['is_finished']]
        print(f"   Завершенных игр: {len(finished_games)}")
        
        if finished_games:
            print("\n🏁 ЗАВЕРШЕННЫЕ ИГРЫ:")
            for game in finished_games:
                print(f"   - {game['text']}")
                if game['score']:
                    print(f"     Счет: {game['score'][0]} : {game['score'][1]}")
        
        if pullup_games_regex:
            print("\n📊 ИГРЫ С СЧЕТОМ (regex):")
            for game in pullup_games_regex:
                print(f"   - {game['text']}")
                print(f"     Счет: {game['score'][0]} : {game['score'][1]}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
