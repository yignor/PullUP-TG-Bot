#!/usr/bin/env python3
"""
Финальный парсер игр PullUP с правильным форматированием
"""

import asyncio
import re
import aiohttp
from datetime import datetime, timezone, timedelta

LETOBASKET_URL = "http://letobasket.ru/"

async def parse_pullup_games():
    """Парсит игры PullUP с сайта letobasket.ru"""
    
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
                    
                    print(f"🎯 ИГРЫ НА СЕГОДНЯ ({current_date})")
                    print("=" * 50)
                    
                    # Ищем игры в формате "дата время (место) - команда1 - команда2"
                    general_pattern = r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2})\s+\(([^)]+)\)\s*-\s*([^-]+?)\s*-\s*([^-]+?)(?:\s|$)'
                    general_matches = re.findall(general_pattern, content, re.IGNORECASE)
                    
                    found_games = []
                    for match in general_matches:
                        date, time, venue, team1, team2 = match
                        team1 = team1.strip()
                        team2 = team2.strip()
                        
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
                                'venue': venue.strip(),
                                'team1': team1,
                                'team2': team2
                            }
                            found_games.append(game_info)
                    
                    if found_games:
                        print(f"📋 Найдено игр: {len(found_games)}")
                        print()
                        
                        for i, game in enumerate(found_games, 1):
                            # Форматируем время (заменяем точку на двоеточие)
                            time_formatted = game['time'].replace('.', ':')
                            print(f"{i}. ⏰ {time_formatted} - {game['team1']} vs {game['team2']} ({game['venue']})")
                    else:
                        print("📅 Сегодня игр нет")
                    
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
                                
                                game_info = f"{result} {pullup_team} {pullup_score}:{opponent_score} {opponent_team} ({date})"
                                finished_games.append(game_info)
                    
                    if finished_games:
                        print(f"📈 Найдено завершенных игр: {len(finished_games)}")
                        print()
                        
                        for i, game in enumerate(finished_games, 1):
                            print(f"{i}. {game}")
                    else:
                        print("📊 Нет данных о недавних играх")
                    
                else:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(parse_pullup_games())
