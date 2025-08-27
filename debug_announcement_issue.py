#!/usr/bin/env python3
"""
Скрипт для отладки проблемы с анонсами
"""

import asyncio
import re
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

async def debug_announcement_issue():
    """Отлаживает проблему с анонсами"""
    
    print("🔍 ОТЛАДКА ПРОБЛЕМЫ С АНОНСАМИ")
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
                
                # Находим игры с PullUP
                games = []
                for match in matches:
                    date, time, venue, team1, team2 = match
                    team1 = team1.strip()
                    team2 = team2.strip()
                    venue = venue.strip()
                    
                    # Проверяем, есть ли Pull Up в командах
                    if 'Pull Up' in team1 or 'Pull Up' in team2:
                        games.append({
                            'date': date,
                            'time': time,
                            'team1': team1,
                            'team2': team2,
                            'venue': venue,
                            'is_today': date == current_date
                        })
                
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
                    
                    if 'Pull Up' in game['team1']:
                        our_team = game['team1']
                        opponent = game['team2']
                    elif 'Pull Up' in game['team2']:
                        our_team = game['team2']
                        opponent = game['team1']
                    
                    if our_team:
                        print(f"   ✅ Наша команда: {our_team}")
                        print(f"   🏀 Соперник: {opponent}")
                        
                        # Определяем категорию команды
                        def get_team_category(team_name: str, opponent: str = "", game_time: str = "") -> str:
                            # Нормализуем название команды для сравнения
                            team_upper = team_name.upper().replace(" ", "").replace("-", "").replace("_", "")
                            
                            # Варианты написания для состава развития
                            development_variants = [
                                "PULLUPФАРМ",
                                "PULLUP-ФАРМ", 
                                "PULLUP-ФАРМ",
                                "PULLUPФАРМ",
                                "PULL UPФАРМ",
                                "PULL UP-ФАРМ",
                                "PULL UP ФАРМ",
                                "PULLUP ФАРМ"
                            ]
                            
                            # Проверяем, является ли команда составом развития по названию
                            for variant in development_variants:
                                if variant in team_upper:
                                    return "Состав Развития"
                            
                            # Дополнительная логика: если команда называется "Pull Up", но соперник из списка развития
                            if "PULLUP" in team_upper and opponent:
                                development_opponents = ['Кудрово', 'Тосно', 'QUASAR', 'TAURUS']
                                if opponent in development_opponents:
                                    return "Состав Развития"
                            
                            # Если не найден ни один вариант состава развития, то это первый состав
                            return "Первый состав"
                        
                        category = get_team_category(our_team, opponent)
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
                        found_game_link = None
                        found_team = None
                        
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
                                                # Дополнительная проверка: убеждаемся, что это именно наша игра
                                                title_match = re.search(r'<TITLE>.*?([^-]+)\s*-\s*([^-]+)', iframe_content, re.IGNORECASE)
                                                if title_match:
                                                    iframe_team1 = title_match.group(1).strip()
                                                    iframe_team2 = title_match.group(2).strip()
                                                    print(f"   📋 Заголовок iframe: {iframe_team1} - {iframe_team2}")
                                                    
                                                    # Нормализуем названия команд для сравнения
                                                    def normalize_team_name(name):
                                                        return name.upper().replace(' ', '').replace('-', '').replace('_', '')
                                                    
                                                    team1_normalized = normalize_team_name(game['team1'])
                                                    team2_normalized = normalize_team_name(game['team2'])
                                                    iframe_team1_normalized = normalize_team_name(iframe_team1)
                                                    iframe_team2_normalized = normalize_team_name(iframe_team2)
                                                    
                                                    # Проверяем соответствие команд
                                                    teams_match = (
                                                        (team1_normalized in iframe_team1_normalized and team2_normalized in iframe_team2_normalized) or
                                                        (team1_normalized in iframe_team2_normalized and team2_normalized in iframe_team1_normalized)
                                                    )
                                                    
                                                    if teams_match:
                                                        game_found_in_scoreboard = True
                                                        found_game_link = game_link
                                                        
                                                        # Определяем найденную команду Pull Up
                                                        if 'PULL UP-ФАРМ' in iframe_text or 'PULL UP ФАРМ' in iframe_text:
                                                            found_team = 'Pull Up-Фарм'
                                                        elif 'PULL UP' in iframe_text:
                                                            found_team = 'Pull Up'
                                                        
                                                        print(f"   ✅ Игра найдена в табло (GameId: {game_id})")
                                                        print(f"   🏷️ Найдена команда: {found_team}")
                                                        break
                                                    else:
                                                        print(f"   ❌ Команды в заголовке не соответствуют: {game['team1']} vs {game['team2']} != {iframe_team1} vs {iframe_team2}")
                                                else:
                                                    print(f"   ⚠️ Заголовок не найден")
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
                        
                        print(f"   🔑 Ключ анонса: {game['date']}_{normalized_time}_{game['team1']}_{game['team2']}")
                    else:
                        print(f"   ❌ Не удалось определить нашу команду")
                
            else:
                print(f"❌ Ошибка получения страницы: {response.status}")

if __name__ == "__main__":
    asyncio.run(debug_announcement_issue())
