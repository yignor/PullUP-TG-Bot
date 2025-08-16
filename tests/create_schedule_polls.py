#!/usr/bin/env python3
"""
Скрипт для создания голосований по расписанию игр PullUP
"""

import asyncio
import os
import re
import sys
from bs4 import BeautifulSoup
import aiohttp
from dotenv import load_dotenv
from datetime import datetime
from telegram import Bot

# Добавляем корневую папку в путь для импорта
sys.path.append('..')

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

def parse_schedule(html_content):
    """Парсит расписание игр"""
    soup = BeautifulSoup(html_content, 'html.parser')
    schedule_text = soup.get_text()
    
    # Ищем все строки с расписанием
    schedule_pattern = r'\d{2}\.\d{2}\.\d{4}\s+\d{2}\.\d{2}\s*\([^)]+\)\s*-\s*[^-]+[^-]*-\s*[^-]+'
    schedule_matches = re.findall(schedule_pattern, schedule_text)
    
    pullup_games = []
    
    for match in schedule_matches:
        print(f"DEBUG: Проверяем запись: {match.strip()}")
        
        # Проверяем, содержит ли запись PullUP
        pullup_patterns = [
            r'pull\s*up',
            r'PullUP',
            r'Pull\s*Up'
        ]
        
        is_pullup_game = any(re.search(pattern, match, re.IGNORECASE) for pattern in pullup_patterns)
        print(f"DEBUG: is_pullup_game = {is_pullup_game}")
        
        if is_pullup_game:
            print(f"   DEBUG: Найдена игра PullUP!")
            
            # Парсим дату и время
            date_time_match = re.search(r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2})', match)
            if date_time_match:
                date_str = date_time_match.group(1)
                time_str = date_time_match.group(2)
                print(f"   DEBUG: Дата: {date_str}, Время: {time_str}")
                
                # Конвертируем дату для получения дня недели
                try:
                    date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                    weekday_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
                    weekday = weekday_names[date_obj.weekday()]
                    print(f"   DEBUG: День недели: {weekday}")
                except:
                    weekday = "Неизвестно"
            else:
                print(f"   DEBUG: Не удалось извлечь дату и время")
                date_str = None
                time_str = None
                weekday = "Неизвестно"
            
            # Парсим адрес зала
            venue_match = re.search(r'\(([^)]+)\)', match)
            venue = venue_match.group(1) if venue_match else "Не указан"
            print(f"   DEBUG: Адрес зала: {venue}")
            
            # Парсим команды - исправленное регулярное выражение
            # Ищем команды в формате "Команда1 - Команда2"
            teams_match = re.search(r'-\s*([^-]+?)\s*-\s*([^-]+?)(?:\s|$)', match)
            if not teams_match:
                # Альтернативный поиск для случаев, когда команды не разделены дефисами
                teams_match = re.search(r'-\s*([^-]+?)\s*([^-]+?)(?:\s|$)', match)
            
            # Если не удалось найти команды, попробуем другой подход
            if not teams_match:
                # Ищем "Pull Up" в тексте и определяем соперника
                pullup_match = re.search(r'Pull\s*Up', match, re.IGNORECASE)
                if pullup_match:
                    # Ищем команду перед Pull Up
                    before_pullup = match[:pullup_match.start()].strip()
                    opponent_match = re.search(r'-\s*([^-]+?)(?:\s*-\s*Pull\s*Up)', match, re.IGNORECASE)
                    if opponent_match:
                        team1 = opponent_match.group(1).strip()
                        team2 = "Pull Up"
                        teams_match = type('MockMatch', (), {'group': lambda self, i: [team1, team2][i-1]})()
            
            print(f"   DEBUG: teams_match = {teams_match}")
            
            if teams_match:
                team1 = teams_match.group(1).strip()
                team2 = teams_match.group(2).strip()
                print(f"   DEBUG: team1 = '{team1}', team2 = '{team2}'")
                
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
                    print(f"   DEBUG: PullUP команда: '{pullup_team}'")
                    print(f"   DEBUG: Соперник: '{opponent_team}'")
                    
                    pullup_games.append({
                        'date': date_str if date_time_match else None,
                        'time': time_str if date_time_match else None,
                        'weekday': weekday,
                        'venue': venue,
                        'pullup_team': pullup_team,
                        'opponent_team': opponent_team,
                        'full_text': match.strip()
                    })
    
    return pullup_games

def create_poll_title(game):
    """Создает название голосования"""
    # Определяем тип команды
    if "Pull Up-Фарм" in game['pullup_team']:
        team_type = "развитие"
    else:
        team_type = "первый состав"
    
    # Формируем название
    title = f"Летняя лига, {team_type}, {game['opponent_team']}: {game['weekday']} ({game['date'][:8]}) {game['time']}, {game['venue']}"
    
    return title

async def create_schedule_polls():
    """Создает голосования по расписанию"""
    print("🏀 СОЗДАНИЕ ГОЛОСОВАНИЙ ПО РАСПИСАНИЮ")
    print("=" * 60)
    
    try:
        # Получаем настройки
        bot_token = os.getenv('BOT_TOKEN')
        chat_id = os.getenv('CHAT_ID')
        topic_id = "1282"  # Топик для голосований
        
        if not bot_token:
            print("❌ BOT_TOKEN не настроен")
            return
        
        if not chat_id:
            print("❌ CHAT_ID не настроен")
            return
        
        print(f"✅ BOT_TOKEN: {'*' * 10}{bot_token[-4:]}")
        print(f"✅ CHAT_ID: {chat_id}")
        print(f"✅ TOPIC_ID: {topic_id}")
        print()
        
        # Получаем расписание
        print("📡 Получаем расписание с сайта...")
        html_content = await get_fresh_page_content()
        
        # Парсим расписание
        pullup_games = parse_schedule(html_content)
        
        print(f"📅 Найдено игр PullUP в расписании: {len(pullup_games)}")
        
        if not pullup_games:
            print("❌ Игры PullUP в расписании не найдены")
            return
        
        # Создаем бота
        bot = Bot(token=bot_token)
        
        # Создаем голосования для каждой игры
        for i, game in enumerate(pullup_games, 1):
            print(f"\n🏀 Игра {i}: {game['pullup_team']} vs {game['opponent_team']}")
            print(f"   Дата: {game['date']} ({game['weekday']})")
            print(f"   Время: {game['time']}")
            print(f"   Зал: {game['venue']}")
            
            # Создаем название голосования
            poll_title = create_poll_title(game)
            print(f"   Название голосования: {poll_title}")
            
            # Варианты ответов
            poll_options = [
                "✅ Готов",
                "❌ Нет", 
                "👨‍🏫 Тренер"
            ]
            
            try:
                # Создаем голосование
                poll = await bot.send_poll(
                    chat_id=chat_id,
                    question=poll_title,
                    options=poll_options,
                    allows_multiple_answers=False,  # Единственный выбор
                    is_anonymous=False,  # Открытое голосование
                    message_thread_id=int(topic_id)
                )
                
                print(f"   ✅ Голосование создано! ID: {poll.message_id}")
                
            except Exception as e:
                print(f"   ❌ Ошибка создания голосования: {e}")
        
        print(f"\n🎯 СОЗДАНО ГОЛОСОВАНИЙ: {len(pullup_games)}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_schedule_polls())
