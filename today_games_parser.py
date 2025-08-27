#!/usr/bin/env python3
"""
Скрипт для парсинга табло и показа игр на сегодня
Показывает кто сегодня играет и результаты завершенных игр
"""

import os
import asyncio
import re
import json
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
import aiohttp
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

# URL для мониторинга
LETOBASKET_URL = "http://letobasket.ru/"

class TodayGamesParser:
    """Парсер для показа игр на сегодня"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def get_moscow_time(self) -> datetime:
        """Получает текущее московское время"""
        moscow_tz = timezone(timedelta(hours=3))  # UTC+3 для Москвы
        return datetime.now(moscow_tz)
    
    def get_current_date(self) -> str:
        """Возвращает текущую дату в формате dd.mm.yyyy"""
        return self.get_moscow_time().strftime('%d.%m.%Y')
    
    def get_day_of_week(self, date_str: str) -> str:
        """Возвращает день недели на русском языке"""
        try:
            date_obj = datetime.strptime(date_str, '%d.%m.%Y')
            days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
            return days[date_obj.weekday()]
        except:
            return ""
    
    def is_pullup_team(self, team_name: str) -> bool:
        """Проверяет, является ли команда командой PullUP"""
        pullup_patterns = [
            r'pull\s*up',
            r'PullUP',
            r'Pull\s*Up',
            r'Pull\s*Up-Фарм'
        ]
        return any(re.search(pattern, team_name, re.IGNORECASE) for pattern in pullup_patterns)
    
    async def get_fresh_page_content(self) -> Optional[str]:
        """Получает свежий контент страницы, избегая кеша"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        try:
            if self.session:
                async with self.session.get(LETOBASKET_URL, headers=headers) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        print(f"❌ Ошибка получения страницы: {response.status}")
                        return None
            else:
                print("❌ Сессия не инициализирована")
                return None
        except Exception as e:
            print(f"❌ Ошибка при получении страницы: {e}")
            return None
    
    def parse_today_games(self, html_content: str) -> List[Dict]:
        """Парсит игры на сегодня"""
        today_games = []
        current_date = self.get_current_date()
        
        try:
            # Ищем игры в формате "дата время (место) - команда1 - команда2"
            # Пример: 27.08.2025 20.30 (MarvelHall) - Кудрово - Pull Up-Фарм
            game_patterns = [
                r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})\s+\(([^)]+)\)\s*-\s*([^-]+?)\s*-\s*([^-]+?)(?:\s|$)',
                r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})\s+\(([^)]+)\)\s*-\s*([^-]+?)\s*против\s*([^-]+?)(?:\s|$)',
            ]
            
            for pattern in game_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                
                for match in matches:
                    date, time, venue, team1, team2 = match
                    team1 = team1.strip()
                    team2 = team2.strip()
                    venue = venue.strip()
                    
                    # Проверяем, что это сегодня и участвует PullUP
                    if date == current_date and (self.is_pullup_team(team1) or self.is_pullup_team(team2)):
                        # Проверяем, не добавлена ли уже эта игра
                        game_exists = any(
                            g['team1'] == team1 and g['team2'] == team2 and g['time'] == time
                            for g in today_games
                        )
                        
                        if not game_exists:
                            game_info = {
                                'date': date,
                                'time': time,
                                'venue': venue,
                                'team1': team1,
                                'team2': team2,
                                'status': 'Запланирована',
                                'score': None,
                                'day_of_week': self.get_day_of_week(date)
                            }
                            today_games.append(game_info)
            
            # Также ищем игры в формате "дата время - команда1 - команда2"
            simple_patterns = [
                r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})\s*-\s*([^-]+?)\s*-\s*([^-]+?)(?:\s|$)',
                r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})\s*-\s*([^-]+?)\s*против\s*([^-]+?)(?:\s|$)',
            ]
            
            for pattern in simple_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                
                for match in matches:
                    date, time, team1, team2 = match
                    team1 = team1.strip()
                    team2 = team2.strip()
                    
                    # Проверяем, что это сегодня и участвует PullUP
                    if date == current_date and (self.is_pullup_team(team1) or self.is_pullup_team(team2)):
                        # Проверяем, не добавлена ли уже эта игра
                        game_exists = any(
                            g['team1'] == team1 and g['team2'] == team2 and g['time'] == time
                            for g in today_games
                        )
                        
                        if not game_exists:
                            game_info = {
                                'date': date,
                                'time': time,
                                'venue': 'Место не указано',
                                'team1': team1,
                                'team2': team2,
                                'status': 'Запланирована',
                                'score': None,
                                'day_of_week': self.get_day_of_week(date)
                            }
                            today_games.append(game_info)
            
        except Exception as e:
            print(f"❌ Ошибка при парсинге игр: {e}")
        
        return today_games
    
    def parse_finished_games(self, html_content: str) -> List[Dict]:
        """Парсит завершенные игры"""
        finished_games = []
        current_date = self.get_current_date()
        
        try:
            # Ищем завершенные игры в формате "дата - команда1 - команда2 - счет"
            game_pattern = r'(\d{2}\.\d{2}\.\d{4})\s*-\s*([^-]+)\s*-\s*([^-]+)\s*(\d+:\d+)'
            matches = re.findall(game_pattern, html_content)
            
            for match in matches:
                game_date, team1, team2, score = match
                team1 = team1.strip()
                team2 = team2.strip()
                
                # Проверяем, участвует ли PullUP
                if self.is_pullup_team(team1) or self.is_pullup_team(team2):
                    # Проверяем, что игра недавняя (не старше недели)
                    if self.is_recent_game(game_date, current_date):
                        score_parts = score.split(':')
                        if len(score_parts) == 2:
                            score1 = int(score_parts[0])
                            score2 = int(score_parts[1])
                            
                            # Определяем, какая команда PullUP
                            if self.is_pullup_team(team1):
                                pullup_team = team1
                                opponent_team = team2
                                pullup_score = score1
                                opponent_score = score2
                            else:
                                pullup_team = team2
                                opponent_team = team1
                                pullup_score = score2
                                opponent_score = score1
                            
                            game_info = {
                                'date': game_date,
                                'pullup_team': pullup_team,
                                'opponent_team': opponent_team,
                                'pullup_score': pullup_score,
                                'opponent_score': opponent_score,
                                'result': 'Победа' if pullup_score > opponent_score else 'Поражение' if pullup_score < opponent_score else 'Ничья',
                                'day_of_week': self.get_day_of_week(game_date)
                            }
                            
                            finished_games.append(game_info)
            
        except Exception as e:
            print(f"❌ Ошибка при парсинге завершенных игр: {e}")
        
        return finished_games
    
    def is_recent_game(self, game_date: str, current_date: str) -> bool:
        """Проверяет, является ли игра недавней (не старше недели)"""
        try:
            game_dt = datetime.strptime(game_date, '%d.%m.%Y')
            current_dt = datetime.strptime(current_date, '%d.%m.%Y')
            
            # Проверяем, что игра не старше 7 дней
            return (current_dt - game_dt).days <= 7
        except:
            return False
    
    def format_game_info(self, game: Dict) -> str:
        """Форматирует информацию об игре для вывода"""
        if game.get('status') == 'Завершена':
            # Для завершенных игр
            result_emoji = "🏆" if game['result'] == 'Победа' else "😔" if game['result'] == 'Поражение' else "🤝"
            return f"{result_emoji} {game['pullup_team']} {game['pullup_score']}:{game['opponent_score']} {game['opponent_team']} ({game['result']})"
        else:
            # Для запланированных игр
            time_str = game['time'].replace('.', ':')  # Заменяем точку на двоеточие
            venue_info = f" ({game['venue']})" if game.get('venue') and game['venue'] != 'Место не указано' else ""
            return f"⏰ {game['time']} - {game['team1']} vs {game['team2']}{venue_info}"
    
    async def show_today_games(self):
        """Показывает игры на сегодня"""
        print(f"🎯 ИГРЫ НА СЕГОДНЯ ({self.get_current_date()})")
        print("=" * 50)
        
        # Получаем контент страницы
        html_content = await self.get_fresh_page_content()
        if not html_content:
            print("❌ Не удалось получить данные с сайта")
            return
        
        # Парсим игры на сегодня
        today_games = self.parse_today_games(html_content)
        
        if not today_games:
            print("📅 Сегодня игр нет")
        else:
            print(f"📋 Найдено игр: {len(today_games)}")
            print()
            
            for i, game in enumerate(today_games, 1):
                print(f"{i}. {self.format_game_info(game)}")
        
        print()
        print("🏀 НЕДАВНИЕ РЕЗУЛЬТАТЫ")
        print("=" * 50)
        
        # Парсим завершенные игры
        finished_games = self.parse_finished_games(html_content)
        
        if not finished_games:
            print("📊 Нет данных о недавних играх")
        else:
            print(f"📈 Найдено завершенных игр: {len(finished_games)}")
            print()
            
            for i, game in enumerate(finished_games, 1):
                print(f"{i}. {self.format_game_info(game)} ({game['date']} {game['day_of_week']})")

async def main():
    """Основная функция"""
    print("🏀 ПАРСЕР ИГР PULLUP")
    print("=" * 50)
    
    async with TodayGamesParser() as parser:
        await parser.show_today_games()

if __name__ == "__main__":
    asyncio.run(main())
