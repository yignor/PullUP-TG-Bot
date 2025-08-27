#!/usr/bin/env python3
"""
Тестовый скрипт для проверки новой логики обработки анонсов
"""

import asyncio
import re
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

async def test_new_logic():
    """Тестирует новую логику обработки анонсов"""
    
    print("🔍 ТЕСТИРОВАНИЕ НОВОЙ ЛОГИКИ")
    print("=" * 50)
    
    # Получаем текущую дату
    moscow_tz = timezone(timedelta(hours=3))
    current_date = datetime.now(moscow_tz).strftime('%d.%m.%Y')
    print(f"📅 Текущая дата: {current_date}")
    
    async with aiohttp.ClientSession() as session:
        url = "http://letobasket.ru/"
        
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Получаем весь текст страницы
                full_text = soup.get_text()
                
                # Паттерн для игр
                game_pattern = r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2})\s+\(([^)]+)\)\s*-\s*([^-]+)\s*-\s*([^-]+)'
                matches = re.findall(game_pattern, full_text, re.IGNORECASE)
                
                # Функция поиска команд
                def find_target_teams_in_text(text: str):
                    found_teams = []
                    search_teams = [
                        'Pull Up-Фарм',
                        'Pull Up Фарм',
                        'PullUP-Фарм',
                        'PullUP Фарм',
                        'Pull Up',
                        'PullUP'
                    ]
                    
                    for team in search_teams:
                        if team in text:
                            found_teams.append(team)
                    
                    return found_teams
                
                # Находим игры с PullUP
                games = []
                for match in matches:
                    date, time, venue, team1, team2 = match
                    team1 = team1.strip()
                    team2 = team2.strip()
                    venue = venue.strip()
                    
                    game_text = f"{team1} {team2}"
                    target_teams = find_target_teams_in_text(game_text)
                    
                    if target_teams:
                        games.append({
                            'date': date,
                            'time': time,
                            'team1': team1,
                            'team2': team2,
                            'venue': venue,
                            'is_today': date == current_date
                        })
                
                # Сортируем игры по дате
                games.sort(key=lambda x: datetime.strptime(x['date'], '%d.%m.%Y'))
                
                print(f"📋 Найдено игр с PullUP: {len(games)}")
                for i, game in enumerate(games, 1):
                    today_marker = " (СЕГОДНЯ!)" if game['is_today'] else ""
                    print(f"{i}. {game['date']} {game['time']} - {game['team1']} vs {game['team2']} ({game['venue']}){today_marker}")
                
                # Проверяем сегодняшние игры
                today_games = [game for game in games if game['is_today']]
                print(f"\n🎯 ИГР НА СЕГОДНЯ: {len(today_games)}")
                
                for game in today_games:
                    print(f"\n🏀 Анализ игры: {game['team1']} vs {game['team2']}")
                    
                    # Определяем нашу команду
                    our_team = None
                    opponent = None
                    
                    if any(target_team in game['team1'] for target_team in ['Pull Up', 'PullUP']):
                        our_team = game['team1']
                        opponent = game['team2']
                    elif any(target_team in game['team2'] for target_team in ['Pull Up', 'PullUP']):
                        our_team = game['team2']
                        opponent = game['team1']
                    
                    if our_team:
                        print(f"   ✅ Наша команда: {our_team}")
                        print(f"   🏀 Соперник: {opponent}")
                        
                        # Определяем категорию команды
                        if 'Фарм' in our_team:
                            category = "Состав Развития"
                        else:
                            category = "Первый состав"
                        
                        print(f"   🏷️ Категория: {category}")
                        
                        # Проверяем, есть ли игра в табло
                        print(f"   🔍 Проверяем наличие в табло...")
                        
                        # Ищем ссылки на игры
                        game_links = []
                        for link in soup.find_all('a', href=True):
                            if "СТРАНИЦА ИГРЫ" in link.get_text():
                                game_links.append(link['href'])
                        
                        print(f"   🔗 Найдено ссылок в табло: {len(game_links)}")
                        
                        # Ищем нашу игру в табло
                        game_found_in_scoreboard = False
                        for game_link in game_links:
                            if 'gameId=' in game_link:
                                game_id = game_link.split('gameId=')[1].split('&')[0]
                                
                                # Формируем URL iframe
                                iframe_url = f"http://ig.russiabasket.ru/online/?id={game_id}&compId=62953&db=reg&tab=0&tv=0&color=5&logo=0&foul=0&white=1&timer24=0&blank=6&short=1&teamA=&teamB="
                                
                                try:
                                    async with session.get(iframe_url) as iframe_response:
                                        if iframe_response.status == 200:
                                            iframe_content = await iframe_response.text()
                                            iframe_text = iframe_content.upper()
                                            
                                            # Проверяем наличие команд
                                            team1_found = game['team1'].upper() in iframe_text
                                            team2_found = game['team2'].upper() in iframe_text
                                            
                                            if team1_found and team2_found:
                                                game_found_in_scoreboard = True
                                                print(f"   ✅ Игра найдена в табло (GameId: {game_id})")
                                                break
                                except:
                                    continue
                        
                        if not game_found_in_scoreboard:
                            print(f"   ⚠️ Игра НЕ найдена в табло")
                        
                        # Формируем анонс
                        normalized_time = game['time'].replace('.', ':')
                        announcement = f"🏀 Сегодня игра {category} против {opponent} в {game['venue']}.\n"
                        announcement += f"🕐 Время игры: {normalized_time}."
                        
                        if game_found_in_scoreboard:
                            announcement += f"\n🔗 Ссылка на игру будет доступна"
                            print(f"   📢 Анонс с ссылкой: {announcement}")
                        else:
                            print(f"   📢 Анонс без ссылки: {announcement}")
                    else:
                        print(f"   ❌ Не удалось определить нашу команду")
                
            else:
                print(f"❌ Ошибка получения страницы: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_new_logic())
