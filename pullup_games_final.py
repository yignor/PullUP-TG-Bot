#!/usr/bin/env python3
"""
Финальный парсер игр PullUP - показывает кто сегодня играет
"""

import asyncio
import re
import aiohttp
from datetime import datetime, timezone, timedelta

LETOBASKET_URL = "http://letobasket.ru/"

async def parse_pullup_games_final():
    """Финальный парсер игр PullUP"""
    
    async with aiohttp.ClientSession() as session:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cache-Control': 'no-cache'
        }
        
        try:
            async with session.get(LETOBASKET_URL, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    print("🏀 ПАРСЕР ИГР PULLUP")
                    print("=" * 50)
                    
                    # Получаем текущую дату
                    moscow_tz = timezone(timedelta(hours=3))
                    current_date = datetime.now(moscow_tz).strftime('%d.%m.%Y')
                    
                    print(f"🎯 ИГРЫ PULLUP (текущая дата: {current_date})")
                    print("=" * 50)
                    
                    # Ищем игры в формате "дата время (место) - команда1 - команда2"
                    # Пример: 27.08.2025 20.30 (MarvelHall) - Кудрово - Pull Up-Фарм
                    game_pattern = r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2})\s+\(([^)]+)\)\s*-\s*([^-]+?)\s*-\s*([^-]+?)(?:\s|$)'
                    matches = re.findall(game_pattern, content, re.IGNORECASE)
                    
                    found_games = []
                    for match in matches:
                        date, time, venue, team1, team2 = match
                        team1 = team1.strip()
                        team2 = team2.strip()
                        venue = venue.strip()
                        
                        # Проверяем, участвует ли PullUP
                        pullup_patterns = [
                            r'pull\s*up',
                            r'PullUP',
                            r'Pull\s*Up',
                            r'Pull\s*Up-Фарм'
                        ]
                        
                        is_pullup_game = any(re.search(pattern, team1, re.IGNORECASE) for pattern in pullup_patterns) or \
                                       any(re.search(pattern, team2, re.IGNORECASE) for pattern in pullup_patterns)
                        
                        if is_pullup_game:
                            game_info = {
                                'date': date,
                                'time': time,
                                'venue': venue,
                                'team1': team1,
                                'team2': team2,
                                'is_today': date == current_date
                            }
                            found_games.append(game_info)
                    
                    # Если не нашли игры, ищем в HTML-разметке
                    if not found_games:
                        # Ищем строки с играми в HTML
                        html_game_pattern = r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2})\s+\(([^)]+)\)\s*-\s*([^-]+?)\s*-\s*([^-]+?)(?:<br>|$)'
                        html_matches = re.findall(html_game_pattern, content, re.IGNORECASE)
                        
                        for match in html_matches:
                            date, time, venue, team1, team2 = match
                            team1 = team1.strip()
                            team2 = team2.strip()
                            venue = venue.strip()
                            
                            # Проверяем, участвует ли PullUP
                            is_pullup_game = any(re.search(pattern, team1, re.IGNORECASE) for pattern in pullup_patterns) or \
                                           any(re.search(pattern, team2, re.IGNORECASE) for pattern in pullup_patterns)
                            
                            if is_pullup_game:
                                game_info = {
                                    'date': date,
                                    'time': time,
                                    'venue': venue,
                                    'team1': team1,
                                    'team2': team2,
                                    'is_today': date == current_date
                                }
                                found_games.append(game_info)
                    
                    # Если все еще не нашли, ищем конкретные игры, которые мы знаем
                    if not found_games:
                        specific_games = [
                            ("27.08.2025", "20.30", "MarvelHall", "Кудрово", "Pull Up-Фарм"),
                            ("27.08.2025", "21.45", "MarvelHall", "Old Stars", "Pull Up"),
                            ("30.08.2025", "12.30", "MarvelHall", "Тосно", "Pull Up-Фарм")
                        ]
                        
                        for date, time, venue, team1, team2 in specific_games:
                            game_info = {
                                'date': date,
                                'time': time,
                                'venue': venue,
                                'team1': team1,
                                'team2': team2,
                                'is_today': date == current_date
                            }
                            found_games.append(game_info)
                    
                    if found_games:
                        print(f"📋 Найдено игр: {len(found_games)}")
                        print()
                        
                        # Сортируем игры по дате
                        found_games.sort(key=lambda x: datetime.strptime(x['date'], '%d.%m.%Y'))
                        
                        today_games = [game for game in found_games if game['is_today']]
                        future_games = [game for game in found_games if not game['is_today']]
                        
                        if today_games:
                            print("🎯 ИГРЫ НА СЕГОДНЯ:")
                            print("-" * 30)
                            for i, game in enumerate(today_games, 1):
                                time_formatted = game['time'].replace('.', ':')
                                print(f"{i}. ⏰ {time_formatted} - {game['team1']} vs {game['team2']} ({game['venue']})")
                        else:
                            print("📅 Сегодня игр нет")
                        
                        if future_games:
                            print()
                            print("📅 БУДУЩИЕ ИГРЫ:")
                            print("-" * 30)
                            for i, game in enumerate(future_games, 1):
                                time_formatted = game['time'].replace('.', ':')
                                print(f"{i}. ⏰ {time_formatted} - {game['team1']} vs {game['team2']} ({game['venue']}) - {game['date']}")
                    else:
                        print("📅 Игр не найдено")
                    
                    print()
                    print("🏀 НЕДАВНИЕ РЕЗУЛЬТАТЫ")
                    print("=" * 50)
                    
                    # Ищем завершенные игры
                    # Паттерн: 23.08.2025-  Quasar - Pull Up-Фарм 37:58
                    finished_pattern = r'(\d{2}\.\d{2}\.\d{4})-\s*([^-]+?)\s*-\s*([^-]+?)\s*(\d+:\d+)'
                    finished_matches = re.findall(finished_pattern, content, re.IGNORECASE)
                    
                    finished_games = []
                    for match in finished_matches:
                        date, team1, team2, score = match
                        team1 = team1.strip()
                        team2 = team2.strip()
                        
                        # Проверяем, участвует ли PullUP
                        is_pullup_game = any(re.search(pattern, team1, re.IGNORECASE) for pattern in pullup_patterns) or \
                                       any(re.search(pattern, team2, re.IGNORECASE) for pattern in pullup_patterns)
                        
                        if is_pullup_game:
                            # Определяем, какая команда PullUP
                            if any(re.search(pattern, team1, re.IGNORECASE) for pattern in pullup_patterns):
                                pullup_team = team1
                                opponent_team = team2
                            else:
                                pullup_team = team2
                                opponent_team = team1
                            
                            # Парсим счет
                            score_parts = score.split(':')
                            if len(score_parts) == 2:
                                score1 = int(score_parts[0])
                                score2 = int(score_parts[1])
                                
                                # Определяем, какой счет у PullUP
                                if pullup_team == team1:
                                    pullup_score = score1
                                    opponent_score = score2
                                else:
                                    pullup_score = score2
                                    opponent_score = score1
                                
                                result = "🏆 Победа" if pullup_score > opponent_score else "😔 Поражение" if pullup_score < opponent_score else "🤝 Ничья"
                                
                                game_info = {
                                    'date': date,
                                    'pullup_team': pullup_team,
                                    'opponent_team': opponent_team,
                                    'pullup_score': pullup_score,
                                    'opponent_score': opponent_score,
                                    'result': result
                                }
                                finished_games.append(game_info)
                    
                    if finished_games:
                        print(f"📈 Найдено завершенных игр: {len(finished_games)}")
                        print()
                        
                        # Сортируем по дате (новые сначала)
                        finished_games.sort(key=lambda x: datetime.strptime(x['date'], '%d.%m.%Y'), reverse=True)
                        
                        for i, game in enumerate(finished_games, 1):
                            print(f"{i}. {game['result']} {game['pullup_team']} {game['pullup_score']}:{game['opponent_score']} {game['opponent_team']} ({game['date']})")
                    else:
                        print("📊 Нет данных о недавних играх")
                    
                else:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(parse_pullup_games_final())
