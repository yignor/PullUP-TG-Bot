#!/usr/bin/env python3
"""
Улучшенный парсер игр, который работает с API напрямую
"""

import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from datetime_utils import get_moscow_time

class EnhancedGameParser:
    """Улучшенный парсер игр, работающий с API"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def extract_game_id_from_url(self, game_url: str) -> Optional[str]:
        """Извлекает gameId из URL игры"""
        try:
            # Ищем gameId в URL
            match = re.search(r'gameId=(\d+)', game_url)
            if match:
                return match.group(1)
            
            # Альтернативный поиск
            match = re.search(r'/(\d+)/?$', game_url)
            if match:
                return match.group(1)
            
            return None
        except Exception as e:
            print(f"❌ Ошибка извлечения gameId: {e}")
            return None
    
    def extract_api_url_from_url(self, game_url: str) -> str:
        """Извлекает API URL из URL игры"""
        try:
            # Ищем apiUrl в URL
            match = re.search(r'apiUrl=([^&]+)', game_url)
            if match:
                return match.group(1)
            
            # По умолчанию используем reg.infobasket.su
            return "https://reg.infobasket.su"
        except Exception as e:
            print(f"❌ Ошибка извлечения API URL: {e}")
            return "https://reg.infobasket.su"
    
    async def get_game_data_from_api(self, game_id: str, api_url: str = "https://reg.infobasket.su") -> Optional[Dict]:
        """Получает данные игры через API"""
        try:
            if not self.session:
                return None
            
            # URL для получения данных игры
            game_api_url = f"{api_url}/Widget/GamePage/{game_id}"
            online_api_url = f"{api_url}/Widget/GetOnline/{game_id}"
            
            print(f"🔍 Запрашиваем данные игры через API:")
            print(f"   Game API: {game_api_url}")
            print(f"   Online API: {online_api_url}")
            
            # Параллельно запрашиваем данные игры и онлайн данные
            async with self.session.get(game_api_url, params={'format': 'json', 'lang': 'ru'}) as game_response, \
                     self.session.get(online_api_url, params={'format': 'json', 'lang': 'ru'}) as online_response:
                
                if game_response.status == 200 and online_response.status == 200:
                    game_data = await game_response.json()
                    online_data = await online_response.json()
                    
                    print(f"✅ Данные получены успешно")
                    print(f"   Game data keys: {list(game_data.keys())}")
                    print(f"   Online data keys: {list(online_data.keys())}")
                    
                    return {
                        'game': game_data,
                        'online': online_data
                    }
                else:
                    print(f"❌ Ошибка API: Game={game_response.status}, Online={online_response.status}")
                    return None
                    
        except Exception as e:
            print(f"❌ Ошибка получения данных через API: {e}")
            return None
    
    def parse_dotnet_date(self, date_str: str) -> Optional[str]:
        """Парсит .NET DateTime формат"""
        try:
            if not date_str or not isinstance(date_str, str):
                return None
            
            # Извлекаем timestamp из /Date(timestamp)/
            match = re.search(r'/Date\((\d+)\)/', date_str)
            if match:
                timestamp = int(match.group(1)) / 1000  # Конвертируем в секунды
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime('%d.%m.%Y')
            
            return None
        except Exception as e:
            print(f"❌ Ошибка парсинга даты: {e}")
            return None
    
    def parse_dotnet_time(self, time_str: str) -> Optional[str]:
        """Парсит .NET DateTime формат для времени"""
        try:
            if not time_str or not isinstance(time_str, str):
                return None
            
            # Извлекаем timestamp из /Date(timestamp)/
            match = re.search(r'/Date\((\d+)\)/', time_str)
            if match:
                timestamp = int(match.group(1)) / 1000  # Конвертируем в секунды
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime('%H:%M')
            
            return None
        except Exception as e:
            print(f"❌ Ошибка парсинга времени: {e}")
            return None

    def parse_game_info(self, api_data: Dict) -> Optional[Dict]:
        """Парсит информацию об игре из API данных"""
        try:
            if not api_data or 'game' not in api_data or 'online' not in api_data:
                return None
            
            game_data = api_data['game']
            online_data = api_data['online']
            
            # Парсим дату и время
            parsed_date = self.parse_dotnet_date(game_data.get('GameDate', ''))
            parsed_time = self.parse_dotnet_time(game_data.get('GameTime', ''))
            
            # Извлекаем основную информацию
            game_info = {
                'game_id': game_data.get('GameID'),
                'status': game_data.get('GameStatus', 0),
                'date': parsed_date or game_data.get('GameDate', ''),
                'time': parsed_time or game_data.get('GameTime', ''),
                'venue': game_data.get('Arena', {}).get('ArenaNameRu', 'Неизвестно'),
                'region': game_data.get('Region', {}).get('RegionNameRu', ''),
                'competition': game_data.get('CompNameRu', ''),
                'league': game_data.get('LeagueNameRu', ''),
                'is_finished': game_data.get('GameStatus', 0) == 1,  # 1 = завершена
                'is_online': online_data.get('IsOnline', False),
                'teams': [],
                'score': {},
                'quarters': [],
                'result': None
            }
            
            # Извлекаем информацию о командах
            teams_data = None
            
            # Пробуем разные источники данных о командах
            if 'GameTeams' in online_data and len(online_data['GameTeams']) >= 2:
                teams_data = online_data['GameTeams']
            elif 'GameTeams' in game_data and len(game_data['GameTeams']) >= 2:
                teams_data = game_data['GameTeams']
            
            if teams_data:
                team1 = teams_data[0]
                team2 = teams_data[1]
                
                # Извлекаем названия команд
                team1_name = 'Команда 1'
                team2_name = 'Команда 2'
                
                if 'TeamName' in team1:
                    team1_name = team1['TeamName'].get('CompTeamNameRu', team1['TeamName'].get('CompTeamNameEn', 'Команда 1'))
                elif 'CompTeamNameRu' in team1:
                    team1_name = team1['CompTeamNameRu']
                
                if 'TeamName' in team2:
                    team2_name = team2['TeamName'].get('CompTeamNameRu', team2['TeamName'].get('CompTeamNameEn', 'Команда 2'))
                elif 'CompTeamNameRu' in team2:
                    team2_name = team2['CompTeamNameRu']
                
                game_info['teams'] = [
                    {
                        'id': team1.get('TeamID'),
                        'name': team1_name,
                        'short_name': team1.get('TeamName', {}).get('CompTeamShortNameRu', 'К1'),
                        'score': team1.get('Score', 0)
                    },
                    {
                        'id': team2.get('TeamID'),
                        'name': team2_name,
                        'short_name': team2.get('TeamName', {}).get('CompTeamShortNameRu', 'К2'),
                        'score': team2.get('Score', 0)
                    }
                ]
                
                # Формируем счет
                game_info['score'] = {
                    'team1': team1.get('Score', 0),
                    'team2': team2.get('Score', 0),
                    'total': f"{team1.get('Score', 0)}:{team2.get('Score', 0)}"
                }
                
                print(f"🏀 Команды найдены: {team1_name} vs {team2_name}")
                print(f"📊 Счет: {team1.get('Score', 0)}:{team2.get('Score', 0)}")
            
            # Извлекаем информацию о четвертях
            quarters = []
            if 'OnlinePeriods' in online_data and online_data['OnlinePeriods']:
                for period in online_data['OnlinePeriods']:
                    # Проверяем, есть ли данные о счете в периоде
                    score_a = period.get('ScoreA', 0)
                    score_b = period.get('ScoreB', 0)
                    
                    # Если счет есть, добавляем период
                    if score_a > 0 or score_b > 0:
                        quarters.append({
                            'period': period.get('Period'),
                            'score1': score_a,
                            'score2': score_b,
                            'total': f"{score_a}:{score_b}"
                        })
            
            # Если данные о четвертях недоступны, создаем заглушку
            if not quarters:
                quarters = ['Данные недоступны']
            
            game_info['quarters'] = quarters
            
            # Определяем результат для команд Pull Up
            if game_info['teams'] and game_info['is_finished']:
                team1_name = game_info['teams'][0]['name']
                team2_name = game_info['teams'][1]['name']
                
                print(f"🔍 Анализируем команды: '{team1_name}' vs '{team2_name}'")
                
                # Проверяем, какая команда Pull Up (более гибкий поиск)
                pull_up_team = None
                opponent_team = None
                
                team1_lower = team1_name.lower()
                team2_lower = team2_name.lower()
                
                if 'pull' in team1_lower or 'фарм' in team1_lower:
                    pull_up_team = game_info['teams'][0]
                    opponent_team = game_info['teams'][1]
                    print(f"✅ Pull Up команда найдена в team1: {team1_name}")
                elif 'pull' in team2_lower or 'фарм' in team2_lower:
                    pull_up_team = game_info['teams'][1]
                    opponent_team = game_info['teams'][0]
                    print(f"✅ Pull Up команда найдена в team2: {team2_name}")
                
                if pull_up_team and opponent_team:
                    if pull_up_team['score'] > opponent_team['score']:
                        game_info['result'] = 'победа'
                    elif pull_up_team['score'] < opponent_team['score']:
                        game_info['result'] = 'поражение'
                    else:
                        game_info['result'] = 'ничья'
                    
                    game_info['our_team'] = pull_up_team['name']
                    game_info['opponent'] = opponent_team['name']
                    game_info['our_score'] = pull_up_team['score']
                    game_info['opponent_score'] = opponent_team['score']
                    
                    print(f"🎯 Результат определен: {game_info['result']}")
                    print(f"📊 Счет: {game_info['our_score']}:{game_info['opponent_score']}")
                else:
                    print(f"❌ Pull Up команда не найдена")
            
            return game_info
            
        except Exception as e:
            print(f"❌ Ошибка парсинга данных игры: {e}")
            return None
    
    async def parse_game_from_url(self, game_url: str) -> Optional[Dict]:
        """Парсит игру по URL"""
        try:
            print(f"🔍 Парсинг игры по URL: {game_url}")
            
            # Извлекаем gameId и API URL
            game_id = self.extract_game_id_from_url(game_url)
            api_url = self.extract_api_url_from_url(game_url)
            
            if not game_id:
                print(f"❌ Не удалось извлечь gameId из URL")
                return None
            
            print(f"📊 GameId: {game_id}")
            print(f"🌐 API URL: {api_url}")
            
            # Получаем данные через API
            api_data = await self.get_game_data_from_api(game_id, api_url)
            if not api_data:
                print(f"❌ Не удалось получить данные через API")
                return None
            
            # Парсим информацию об игре
            game_info = self.parse_game_info(api_data)
            if not game_info:
                print(f"❌ Не удалось распарсить данные игры")
                return None
            
            print(f"✅ Игра успешно распарсена:")
            print(f"   Команды: {game_info.get('our_team', 'Неизвестно')} vs {game_info.get('opponent', 'Неизвестно')}")
            print(f"   Счет: {game_info.get('our_score', 0)}:{game_info.get('opponent_score', 0)}")
            print(f"   Статус: {'Завершена' if game_info.get('is_finished') else 'В процессе'}")
            print(f"   Результат: {game_info.get('result', 'Неизвестно')}")
            
            return game_info
            
        except Exception as e:
            print(f"❌ Ошибка парсинга игры: {e}")
            return None

async def test_parser():
    """Тестирует парсер на реальной игре"""
    test_url = "http://letobasket.ru/game.html?gameId=934356&apiUrl=https://reg.infobasket.su&lang=ru"
    
    async with EnhancedGameParser() as parser:
        result = await parser.parse_game_from_url(test_url)
        
        if result:
            print(f"\n📊 РЕЗУЛЬТАТ ПАРСИНГА:")
            print(f"   🏀 Команды: {result.get('our_team', 'Неизвестно')} vs {result.get('opponent', 'Неизвестно')}")
            print(f"   📊 Счет: {result.get('our_score', 0)}:{result.get('opponent_score', 0)}")
            print(f"   🎯 Результат: {result.get('result', 'Неизвестно')}")
            print(f"   📈 Четверти: {[q['total'] for q in result.get('quarters', [])]}")
            print(f"   📅 Дата: {result.get('date', 'Неизвестно')}")
            print(f"   🕐 Время: {result.get('time', 'Неизвестно')}")
            print(f"   📍 Место: {result.get('venue', 'Неизвестно')}")
            print(f"   🏆 Статус: {'Завершена' if result.get('is_finished') else 'В процессе'}")
        else:
            print(f"❌ Парсинг не удался")

if __name__ == "__main__":
    asyncio.run(test_parser())
