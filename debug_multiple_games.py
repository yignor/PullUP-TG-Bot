#!/usr/bin/env python3
"""
Отладочный скрипт для проверки нескольких игр и поиска PullUP
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def debug_multiple_games():
    """Проверяет несколько игр на наличие PullUP"""
    base_url = "http://letobasket.ru/"
    
    # Список игр для проверки
    game_urls = [
        "http://letobasket.ru/P2025/podrobno.php?id=228&id1=S",
        "http://letobasket.ru/P2025/podrobno.php?id=227&id1=S", 
        "http://letobasket.ru/P2025/podrobno.php?id=226&id1=S",
        "http://letobasket.ru/P2025/podrobno.php?id=225&id1=S",
        "http://letobasket.ru/P2025/podrobno.php?id=224&id1=S",
    ]
    
    try:
        async with aiohttp.ClientSession() as session:
            for i, game_url in enumerate(game_urls, 1):
                print(f"\n🎮 ПРОВЕРЯЮ ИГРУ {i}: {game_url}")
                print("-" * 60)
                
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
                            
                            print(f"Размер текста: {len(page_text)} символов")
                            
                            # Ищем команды в тексте
                            team_patterns = [
                                r'([А-Я][а-я\s]+)\s+[-—]\s+([А-Я][а-я\s]+)',
                                r'([А-Я][а-я\s]+)\s+vs\s+([А-Я][а-я\s]+)',
                                r'([А-Я][а-я\s]+)\s+против\s+([А-Я][а-я\s]+)',
                            ]
                            
                            found_teams = []
                            for pattern in team_patterns:
                                matches = re.findall(pattern, page_text)
                                if matches:
                                    for match in matches:
                                        team1 = match[0].strip()
                                        team2 = match[1].strip()
                                        found_teams.append((team1, team2))
                            
                            if found_teams:
                                print("🏀 НАЙДЕННЫЕ КОМАНДЫ:")
                                for team1, team2 in found_teams:
                                    print(f"   {team1} vs {team2}")
                                    
                                    # Проверяем на PullUP
                                    if 'pull' in team1.lower() and 'up' in team1.lower():
                                        print(f"   ✅ PULLUP НАЙДЕН В КОМАНДЕ 1: {team1}")
                                    if 'pull' in team2.lower() and 'up' in team2.lower():
                                        print(f"   ✅ PULLUP НАЙДЕН В КОМАНДЕ 2: {team2}")
                            else:
                                print("❌ Команды не найдены")
                            
                            # Ищем время
                            time_match = re.search(r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})', page_text)
                            if time_match:
                                print(f"📅 Дата: {time_match.group(1)}")
                            
                            # Показываем первые 200 символов
                            print(f"📄 Начало текста: {page_text[:200]}...")
                            
                        else:
                            print(f"❌ Ошибка получения страницы: {response.status}")
                            
                except Exception as e:
                    print(f"❌ Ошибка при проверке игры: {e}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_multiple_games())
