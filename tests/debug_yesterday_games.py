#!/usr/bin/env python3
"""
Отладочный скрипт для анализа игр на 16.08.2025
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

def debug_yesterday_games(html_content):
    """Анализирует игры на 16.08.2025"""
    print("🔍 АНАЛИЗ ИГР НА 16.08.2025")
    print("=" * 60)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Ищем все игры на 16.08.2025
    yesterday_date = "16.08.2025"
    
    # Ищем строки с играми на 16.08.2025
    game_pattern = rf'{yesterday_date}[^-]*-\s*[^-]+[^-]*-\s*[^-]+'
    all_games = re.findall(game_pattern, html_content)
    
    print(f"📅 Найдено игр на {yesterday_date}: {len(all_games)}")
    
    pullup_games = []
    
    for i, game_text in enumerate(all_games):
        print(f"\n🏀 Игра {i+1}: {game_text.strip()}")
        
        # Проверяем, содержит ли игра PullUP
        pullup_patterns = [
            r'pull\s*up',
            r'PullUP',
            r'Pull\s*Up'
        ]
        
        is_pullup_game = any(re.search(pattern, game_text, re.IGNORECASE) for pattern in pullup_patterns)
        
        if is_pullup_game:
            print(f"   ✅ ЭТО ИГРА PULLUP!")
            
            # Извлекаем команды - исправленное регулярное выражение
            # Ищем формат: "Команда1 - Команда2"
            teams_match = re.search(r'-\s*([^-]+?)\s*-\s*([^-]+?)\s*\d+:\d+', game_text)
            if teams_match:
                team1 = teams_match.group(1).strip()
                team2 = teams_match.group(2).strip()
                print(f"   Команда 1: {team1}")
                print(f"   Команда 2: {team2}")
            else:
                # Альтернативный поиск
                print(f"   ❌ Не удалось извлечь команды")
                print(f"   Полный текст: {game_text}")
            
            # Извлекаем счет
            score_match = re.search(r'(\d+)\s*:\s*(\d+)', game_text)
            if score_match:
                score1, score2 = score_match.groups()
                print(f"   Счет: {score1} : {score2}")
            
            # Извлекаем время
            time_match = re.search(r'\d{2}\.\d{2}', game_text)
            if time_match:
                game_time = time_match.group()
                print(f"   Время: {game_time}")
            
            # Извлекаем ссылку на игру
            link_match = re.search(r'href="([^"]+)"', game_text)
            if link_match:
                game_link = link_match.group(1)
                print(f"   Ссылка: {game_link}")
            
            pullup_games.append({
                'text': game_text.strip(),
                'team1': team1 if teams_match else 'Неизвестно',
                'team2': team2 if teams_match else 'Неизвестно',
                'score': (score1, score2) if score_match else None,
                'time': game_time if time_match else None,
                'link': game_link if link_match else None
            })
        else:
            print(f"   ❌ Не игра PullUP")
    
    print(f"\n📈 ИТОГО ИГР PULLUP НА {yesterday_date}: {len(pullup_games)}")
    
    if pullup_games:
        print("\n🏁 ИГРЫ PULLUP НА 16.08.2025:")
        for i, game in enumerate(pullup_games, 1):
            print(f"   {i}. {game['team1']} vs {game['team2']}")
            if game['score']:
                print(f"      Счет: {game['score'][0]} : {game['score'][1]}")
            if game['time']:
                print(f"      Время: {game['time']}")
            if game['link']:
                print(f"      Ссылка: {game['link']}")
    
    return pullup_games

async def main():
    """Основная функция"""
    print("🔍 АНАЛИЗ ИГР PULLUP НА 16.08.2025")
    print("=" * 60)
    
    try:
        # Получаем свежий контент
        print("📡 Получаем данные с сайта...")
        html_content = await get_fresh_page_content()
        
        # Анализируем игры на 16.08.2025
        pullup_games = debug_yesterday_games(html_content)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
