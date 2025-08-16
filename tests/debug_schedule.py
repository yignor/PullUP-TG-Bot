#!/usr/bin/env python3
"""
Отладочный скрипт для анализа блока "РАСПИСАНИЕ ИГР"
"""

import asyncio
import os
import re
from bs4 import BeautifulSoup
import aiohttp
from dotenv import load_dotenv
from datetime import datetime

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

def debug_schedule(html_content):
    """Анализирует блок расписания игр"""
    print("🔍 АНАЛИЗ БЛОКА 'РАСПИСАНИЕ ИГР'")
    print("=" * 60)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Ищем блок "РАСПИСАНИЕ ИГР"
    schedule_text = soup.get_text()
    
    # Ищем все строки с расписанием
    schedule_pattern = r'\d{2}\.\d{2}\.\d{4}\s+\d{2}\.\d{2}\s*\([^)]+\)\s*-\s*[^-]+[^-]*-\s*[^-]+'
    schedule_matches = re.findall(schedule_pattern, schedule_text)
    
    print(f"📅 Найдено записей в расписании: {len(schedule_matches)}")
    
    pullup_games = []
    
    for i, match in enumerate(schedule_matches):
        print(f"\n🏀 Запись {i+1}: {match.strip()}")
        
        # Проверяем, содержит ли запись PullUP
        pullup_patterns = [
            r'pull\s*up',
            r'PullUP',
            r'Pull\s*Up'
        ]
        
        is_pullup_game = any(re.search(pattern, match, re.IGNORECASE) for pattern in pullup_patterns)
        
        if is_pullup_game:
            print(f"   ✅ ЭТО ИГРА PULLUP!")
            
            # Парсим дату и время
            date_time_match = re.search(r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2})', match)
            if date_time_match:
                date_str = date_time_match.group(1)
                time_str = date_time_match.group(2)
                print(f"   Дата: {date_str}")
                print(f"   Время: {time_str}")
                
                # Конвертируем дату для получения дня недели
                try:
                    date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                    weekday_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
                    weekday = weekday_names[date_obj.weekday()]
                    print(f"   День недели: {weekday}")
                except:
                    weekday = "Неизвестно"
            
            # Парсим адрес зала
            venue_match = re.search(r'\(([^)]+)\)', match)
            if venue_match:
                venue = venue_match.group(1)
                print(f"   Адрес зала: {venue}")
            
            # Парсим команды
            teams_match = re.search(r'-\s*([^-]+?)\s*-\s*([^-]+?)(?:\s|$)', match)
            if teams_match:
                team1 = teams_match.group(1).strip()
                team2 = teams_match.group(2).strip()
                print(f"   Команда 1: {team1}")
                print(f"   Команда 2: {team2}")
                
                # Определяем, какая команда PullUP
                pullup_team = None
                opponent_team = None
                
                if any(re.search(pattern, team1, re.IGNORECASE) for pattern in pullup_patterns):
                    pullup_team = team1
                    opponent_team = team2
                elif any(re.search(pattern, team2, re.IGNORECASE) for pattern in pullup_patterns):
                    pullup_team = team2
                    opponent_team = team1
                
                if pullup_team and opponent_team:
                    print(f"   PullUP команда: {pullup_team}")
                    print(f"   Соперник: {opponent_team}")
                    
                    pullup_games.append({
                        'date': date_str if date_time_match else None,
                        'time': time_str if date_time_match else None,
                        'weekday': weekday,
                        'venue': venue if venue_match else None,
                        'pullup_team': pullup_team,
                        'opponent_team': opponent_team,
                        'full_text': match.strip()
                    })
        else:
            print(f"   ❌ Не игра PullUP")
    
    print(f"\n📈 ИТОГО ИГР PULLUP В РАСПИСАНИИ: {len(pullup_games)}")
    
    if pullup_games:
        print("\n🏁 ИГРЫ PULLUP В РАСПИСАНИИ:")
        for i, game in enumerate(pullup_games, 1):
            print(f"   {i}. {game['pullup_team']} vs {game['opponent_team']}")
            print(f"      Дата: {game['date']} ({game['weekday']})")
            print(f"      Время: {game['time']}")
            print(f"      Зал: {game['venue']}")
            print()
    
    return pullup_games

async def main():
    """Основная функция"""
    print("🔍 АНАЛИЗ РАСПИСАНИЯ ИГР")
    print("=" * 60)
    
    try:
        # Получаем свежий контент
        print("📡 Получаем данные с сайта...")
        html_content = await get_fresh_page_content()
        
        # Анализируем расписание
        pullup_games = debug_schedule(html_content)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
