#!/usr/bin/env python3
"""
Отладочный скрипт для проверки большего количества игр с улучшенным паттерном
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def debug_more_games():
    """Проверяет больше игр на наличие PullUP"""
    base_url = "http://letobasket.ru/"
    
    # Проверим больше игр
    game_urls = []
    for i in range(220, 240):  # Проверим игры с id от 220 до 240
        game_urls.append(f"http://letobasket.ru/P2025/podrobno.php?id={i}&id1=S")
    
    try:
        async with aiohttp.ClientSession() as session:
            pullup_found = False
            
            for i, game_url in enumerate(game_urls, 1):
                print(f"\n🎮 ПРОВЕРЯЮ ИГРУ {i}: {game_url}")
                
                try:
                    async with session.get(game_url) as response:
                        if response.status == 200:
                            # Получаем контент с правильной кодировкой
                            html_content = await response.read()
                            
                            # Пытаемся декодировать с правильной кодировкой
                            try:
                                html_text = html_content.decode('utf-8')
                            except UnicodeDecodeError:
                                try:
                                    html_text = html_content.decode('windows-1251')
                                except UnicodeDecodeError:
                                    html_text = html_content.decode('cp1251')
                            
                            # Парсим HTML
                            soup = BeautifulSoup(html_text, 'html.parser')
                            page_text = soup.get_text()
                            
                            # Улучшенный поиск команд
                            # Ищем команды в формате "Команда1 - Команда2"
                            team_match = re.search(r'([А-Я][а-я\s]+)\s*[-—]\s*([А-Я][а-я\s]+)', page_text)
                            
                            if team_match:
                                team1 = team_match.group(1).strip()
                                team2 = team_match.group(2).strip()
                                
                                print(f"🏀 Найдены команды: {team1} vs {team2}")
                                
                                # Проверяем на PullUP
                                if ('pull' in team1.lower() and 'up' in team1.lower()) or ('pull' in team2.lower() and 'up' in team2.lower()):
                                    print(f"✅ PULLUP НАЙДЕН!")
                                    print(f"   Команда 1: {team1}")
                                    print(f"   Команда 2: {team2}")
                                    pullup_found = True
                                    
                                    # Ищем результат
                                    score_match = re.search(r'(\d+):(\d+)', page_text)
                                    if score_match:
                                        score1 = score_match.group(1)
                                        score2 = score_match.group(2)
                                        print(f"   Результат: {score1}:{score2}")
                                    
                                    # Ищем дату
                                    date_match = re.search(r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})', page_text)
                                    if date_match:
                                        print(f"   Дата: {date_match.group(1)}")
                                    
                                    break
                            else:
                                print("❌ Команды не найдены")
                            
                        else:
                            print(f"❌ Ошибка получения страницы: {response.status}")
                            
                except Exception as e:
                    print(f"❌ Ошибка при проверке игры: {e}")
            
            if not pullup_found:
                print(f"\n❌ PullUP не найден в проверенных играх")
                print(f"Проверено игр: {len(game_urls)}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_more_games())
