#!/usr/bin/env python3
"""
Отладочный скрипт для проверки конкретных игр и поиска PullUP
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from letobasket_monitor import extract_game_links_from_soup, parse_game_info, team_matches_targets, get_target_team_names

async def debug_specific_games():
    """Проверяет конкретные игры на наличие PullUP"""
    url = "http://letobasket.ru/"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    print("🔍 ОТЛАДКА КОНКРЕТНЫХ ИГР")
                    print("=" * 50)
                    
                    # Получаем ссылки на игры
                    game_links = extract_game_links_from_soup(soup, url, max_links=50)
                    print(f"🔗 Найдено {len(game_links)} ссылок на игры")
                    
                    # Получаем целевые команды
                    targets = get_target_team_names()
                    print(f"🎯 Целевые команды: {targets}")
                    
                    # Проверяем первые 10 игр
                    checked_games = 0
                    found_pullup_games = []
                    
                    for i, game_url in enumerate(game_links[:10], 1):
                        print(f"\n🎮 Проверяю игру {i}: {game_url}")
                        
                        try:
                            game_info = await parse_game_info(game_url)
                            if game_info:
                                team1 = game_info.get('team1', '')
                                team2 = game_info.get('team2', '')
                                game_time = game_info.get('time', '')
                                
                                print(f"   Команда 1: {team1}")
                                print(f"   Команда 2: {team2}")
                                print(f"   Время: {game_time}")
                                
                                # Проверяем, есть ли PullUP
                                if team_matches_targets(team1, targets) or team_matches_targets(team2, targets):
                                    print(f"   ✅ НАЙДЕНА ИГРА PULLUP!")
                                    found_pullup_games.append((game_url, game_info))
                                else:
                                    print(f"   ❌ PullUP не найден")
                                
                                checked_games += 1
                            else:
                                print(f"   ⚠️ Не удалось получить информацию об игре")
                                
                        except Exception as e:
                            print(f"   ❌ Ошибка при проверке игры: {e}")
                    
                    print(f"\n📊 РЕЗУЛЬТАТЫ:")
                    print(f"   Проверено игр: {checked_games}")
                    print(f"   Найдено игр с PullUP: {len(found_pullup_games)}")
                    
                    if found_pullup_games:
                        print(f"\n🏀 НАЙДЕННЫЕ ИГРЫ PULLUP:")
                        for i, (game_url, game_info) in enumerate(found_pullup_games, 1):
                            team1 = game_info.get('team1', 'Команда 1')
                            team2 = game_info.get('team2', 'Команда 2')
                            game_time = game_info.get('time', 'Время не указано')
                            print(f"   {i}. {team1} vs {team2} - {game_time}")
                            print(f"      Ссылка: {game_url}")
                    else:
                        print(f"\n❌ Игры с PullUP не найдены")
                        
                        # Дополнительная диагностика
                        print(f"\n🔍 ДОПОЛНИТЕЛЬНАЯ ДИАГНОСТИКА:")
                        
                        # Проверяем все команды в первых 5 играх
                        for i, game_url in enumerate(game_links[:5], 1):
                            try:
                                game_info = await parse_game_info(game_url)
                                if game_info:
                                    team1 = game_info.get('team1', '')
                                    team2 = game_info.get('team2', '')
                                    print(f"   Игра {i}: '{team1}' vs '{team2}'")
                                    
                                    # Проверяем каждую команду отдельно
                                    for target in targets:
                                        if team_matches_targets(team1, [target]):
                                            print(f"      ✅ {team1} соответствует {target}")
                                        if team_matches_targets(team2, [target]):
                                            print(f"      ✅ {team2} соответствует {target}")
                            except:
                                pass
                    
                else:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_specific_games())
