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

    async def parse_game_info(self, api_data: Dict, game_url: str = None) -> Optional[Dict]:
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
            
            # Извлекаем статистику игроков
            player_stats = self.extract_player_statistics(api_data)
            if player_stats:
                game_info['player_stats'] = player_stats
                print(f"📊 Статистика игроков извлечена через API: {len(player_stats.get('players', []))} игроков")
            else:
                # Если не удалось получить статистику через API, пробуем через protocol
                print("🔍 Статистика через API не найдена, пробуем через protocol...")
                protocol_stats = await self.parse_game_statistics_from_protocol(game_url)
                if protocol_stats:
                    game_info['player_stats'] = protocol_stats
                    print(f"📊 Статистика игроков извлечена через protocol: {len(protocol_stats.get('players', []))} игроков")
                else:
                    print("⚠️ Статистика игроков не найдена ни через API, ни через protocol")
            
            return game_info
            
        except Exception as e:
            print(f"❌ Ошибка парсинга данных игры: {e}")
            return None
    
    def extract_player_statistics(self, api_data: Dict) -> Optional[Dict]:
        """Извлекает статистику игроков из API данных"""
        try:
            game_data = api_data.get('game', {})
            online_data = api_data.get('online', {})
            
            # Ищем статистику игроков в данных
            players_stats = []
            
            # Проверяем различные возможные места для статистики
            if 'Players' in game_data:
                players_data = game_data['Players']
                print(f"🔍 Найдены данные игроков в game.Players: {len(players_data)} игроков")
                
                for player in players_data:
                    player_stat = self.parse_player_statistics(player)
                    if player_stat:
                        players_stats.append(player_stat)
            
            elif 'TeamPlayers' in game_data:
                # Если статистика по командам
                for team_key in ['Team1', 'Team2']:
                    if team_key in game_data['TeamPlayers']:
                        team_players = game_data['TeamPlayers'][team_key]
                        print(f"🔍 Найдены игроки команды {team_key}: {len(team_players)} игроков")
                        
                        for player in team_players:
                            player_stat = self.parse_player_statistics(player)
                            if player_stat:
                                players_stats.append(player_stat)
            
            elif 'Statistics' in online_data:
                # Проверяем онлайн статистику
                stats_data = online_data['Statistics']
                print(f"🔍 Найдена онлайн статистика: {list(stats_data.keys())}")
                
                # Ищем статистику игроков в онлайн данных
                for key, value in stats_data.items():
                    if isinstance(value, list) and len(value) > 0:
                        for item in value:
                            if isinstance(item, dict) and 'PlayerName' in item:
                                player_stat = self.parse_player_statistics(item)
                                if player_stat:
                                    players_stats.append(player_stat)
            
            if players_stats:
                # Находим лучших игроков
                best_players = self.find_best_players(players_stats)
                
                return {
                    'players': players_stats,
                    'best_players': best_players,
                    'total_players': len(players_stats)
                }
            
            print("⚠️ Статистика игроков не найдена в API данных")
            return None
            
        except Exception as e:
            print(f"❌ Ошибка извлечения статистики игроков: {e}")
            return None
    
    def parse_player_statistics(self, player_data: Dict) -> Optional[Dict]:
        """Парсит статистику отдельного игрока"""
        try:
            # Извлекаем основные данные игрока
            player_name = player_data.get('PlayerName') or player_data.get('Name') or player_data.get('player_name')
            if not player_name:
                return None
            
            # Извлекаем статистику (различные возможные названия полей)
            stats = {
                'name': player_name.strip(),
                'points': self.extract_stat_value(player_data, ['Points', 'PTS', 'points', 'Очки']),
                'rebounds': self.extract_stat_value(player_data, ['Rebounds', 'REB', 'rebounds', 'Подборы', 'TRB']),
                'assists': self.extract_stat_value(player_data, ['Assists', 'AST', 'assists', 'Передачи', 'ПАС']),
                'steals': self.extract_stat_value(player_data, ['Steals', 'STL', 'steals', 'Перехваты', 'ПЕРЕХ']),
                'blocks': self.extract_stat_value(player_data, ['Blocks', 'BLK', 'blocks', 'Блокшоты', 'БЛОК']),
                'turnovers': self.extract_stat_value(player_data, ['Turnovers', 'TOV', 'turnovers', 'Потери', 'ПОТ']),
                'fouls': self.extract_stat_value(player_data, ['Fouls', 'PF', 'fouls', 'Фолы', 'ФОЛ']),
                'field_goals_made': self.extract_stat_value(player_data, ['FGM', 'field_goals_made', 'Попадания']),
                'field_goals_attempted': self.extract_stat_value(player_data, ['FGA', 'field_goals_attempted', 'Попытки']),
                'three_pointers_made': self.extract_stat_value(player_data, ['3PM', 'three_pointers_made', '3-очковые']),
                'three_pointers_attempted': self.extract_stat_value(player_data, ['3PA', 'three_pointers_attempted', '3-очковые попытки']),
                'free_throws_made': self.extract_stat_value(player_data, ['FTM', 'free_throws_made', 'Штрафные']),
                'free_throws_attempted': self.extract_stat_value(player_data, ['FTA', 'free_throws_attempted', 'Штрафные попытки']),
                'minutes': self.extract_stat_value(player_data, ['Minutes', 'MIN', 'minutes', 'Минуты', 'Время']),
                'team': player_data.get('TeamName') or player_data.get('team_name', ''),
                'position': player_data.get('Position') or player_data.get('position', ''),
                'jersey_number': player_data.get('JerseyNumber') or player_data.get('jersey_number', '')
            }
            
            # Вычисляем проценты попаданий
            if stats['field_goals_attempted'] and stats['field_goals_attempted'] > 0:
                stats['field_goal_percentage'] = round((stats['field_goals_made'] / stats['field_goals_attempted']) * 100, 1)
            else:
                stats['field_goal_percentage'] = 0.0
            
            if stats['three_pointers_attempted'] and stats['three_pointers_attempted'] > 0:
                stats['three_point_percentage'] = round((stats['three_pointers_made'] / stats['three_pointers_attempted']) * 100, 1)
            else:
                stats['three_point_percentage'] = 0.0
            
            if stats['free_throws_attempted'] and stats['free_throws_attempted'] > 0:
                stats['free_throw_percentage'] = round((stats['free_throws_made'] / stats['free_throws_attempted']) * 100, 1)
            else:
                stats['free_throw_percentage'] = 0.0
            
            return stats
            
        except Exception as e:
            print(f"❌ Ошибка парсинга статистики игрока: {e}")
            return None
    
    def extract_stat_value(self, data: Dict, possible_keys: List[str]) -> int:
        """Извлекает значение статистики по возможным ключам"""
        for key in possible_keys:
            if key in data:
                value = data[key]
                if isinstance(value, (int, float)):
                    return int(value)
                elif isinstance(value, str) and value.isdigit():
                    return int(value)
        return 0
    
    def find_best_players(self, players_stats: List[Dict]) -> Dict:
        """Находит лучших игроков по различным показателям"""
        try:
            if not players_stats:
                return {}
            
            best_players = {}
            
            # MVP (игрок с наибольшим количеством очков)
            mvp = max(players_stats, key=lambda p: p['points'])
            best_players['mvp'] = {
                'name': mvp['name'],
                'points': mvp['points'],
                'field_goal_percentage': mvp['field_goal_percentage'],
                'team': mvp['team']
            }
            
            # Лучший по подборам
            best_rebounder = max(players_stats, key=lambda p: p['rebounds'])
            best_players['best_rebounder'] = {
                'name': best_rebounder['name'],
                'rebounds': best_rebounder['rebounds'],
                'team': best_rebounder['team']
            }
            
            # Лучший по перехватам
            best_stealer = max(players_stats, key=lambda p: p['steals'])
            best_players['best_stealer'] = {
                'name': best_stealer['name'],
                'steals': best_stealer['steals'],
                'team': best_stealer['team']
            }
            
            # Лучший по передачам
            best_assister = max(players_stats, key=lambda p: p['assists'])
            best_players['best_assister'] = {
                'name': best_assister['name'],
                'assists': best_assister['assists'],
                'team': best_assister['team']
            }
            
            # Лучший по блокшотам
            best_blocker = max(players_stats, key=lambda p: p['blocks'])
            best_players['best_blocker'] = {
                'name': best_blocker['name'],
                'blocks': best_blocker['blocks'],
                'team': best_blocker['team']
            }
            
            print(f"🏆 Лучшие игроки найдены:")
            print(f"   MVP: {best_players['mvp']['name']} ({best_players['mvp']['points']} очков, {best_players['mvp']['field_goal_percentage']}%)")
            print(f"   Подборы: {best_players['best_rebounder']['name']} ({best_players['best_rebounder']['rebounds']})")
            print(f"   Перехваты: {best_players['best_stealer']['name']} ({best_players['best_stealer']['steals']})")
            
            return best_players
            
        except Exception as e:
            print(f"❌ Ошибка поиска лучших игроков: {e}")
            return {}
    
    async def parse_game_statistics_from_protocol(self, game_url: str) -> Optional[Dict]:
        """Парсит статистику игры через protocol на странице"""
        try:
            if not self.session:
                return None
            
            print(f"🔍 Парсинг статистики через protocol: {game_url}")
            
            # Загружаем страницу с protocol
            async with self.session.get(game_url) as response:
                if response.status == 200:
                    content = await response.text()
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Сначала пробуем парсить HTML таблицу статистики
                    player_stats = self.parse_html_statistics_table(soup)
                    
                    if player_stats:
                        # Находим лучших игроков
                        best_players = self.find_best_players(player_stats)
                        
                        return {
                            'players': player_stats,
                            'best_players': best_players,
                            'total_players': len(player_stats),
                            'source': 'html_table'
                        }
                    
                    # Если HTML таблица не найдена, пробуем protocol
                    print("🔍 HTML таблица не найдена, пробуем protocol...")
                    page_text = soup.get_text()
                    player_stats = self.parse_protocol_statistics(page_text)
                    
                    if player_stats:
                        # Находим лучших игроков
                        best_players = self.find_best_players(player_stats)
                        
                        return {
                            'players': player_stats,
                            'best_players': best_players,
                            'total_players': len(player_stats),
                            'source': 'protocol'
                        }
                    
                    print("⚠️ Статистика игроков не найдена ни в HTML таблице, ни в protocol")
                    return None
                else:
                    print(f"❌ Ошибка загрузки страницы protocol: {response.status}")
                    return None
                    
        except Exception as e:
            print(f"❌ Ошибка парсинга protocol: {e}")
            return None
    
    def parse_protocol_statistics(self, page_text: str) -> List[Dict]:
        """Парсит статистику игроков из текста protocol"""
        try:
            players_stats = []
            
            # Ищем паттерны статистики игроков в protocol
            # Пример: protocol.player1.Points = 15
            # Или: protocol.team1.player1.Points = 15
            
            # Паттерны для поиска статистики
            stat_patterns = {
                'points': r'protocol\.(?:team\d+\.)?player\d+\.Points[:\s]*(\d+)',
                'rebounds': r'protocol\.(?:team\d+\.)?player\d+\.Rebounds[:\s]*(\d+)',
                'assists': r'protocol\.(?:team\d+\.)?player\d+\.Assists[:\s]*(\d+)',
                'steals': r'protocol\.(?:team\d+\.)?player\d+\.Steals[:\s]*(\d+)',
                'blocks': r'protocol\.(?:team\d+\.)?player\d+\.Blocks[:\s]*(\d+)',
                'turnovers': r'protocol\.(?:team\d+\.)?player\d+\.Turnovers[:\s]*(\d+)',
                'fouls': r'protocol\.(?:team\d+\.)?player\d+\.Fouls[:\s]*(\d+)',
                'field_goals_made': r'protocol\.(?:team\d+\.)?player\d+\.FieldGoalsMade[:\s]*(\d+)',
                'field_goals_attempted': r'protocol\.(?:team\d+\.)?player\d+\.FieldGoalsAttempted[:\s]*(\d+)',
                'three_pointers_made': r'protocol\.(?:team\d+\.)?player\d+\.ThreePointersMade[:\s]*(\d+)',
                'three_pointers_attempted': r'protocol\.(?:team\d+\.)?player\d+\.ThreePointersAttempted[:\s]*(\d+)',
                'free_throws_made': r'protocol\.(?:team\d+\.)?player\d+\.FreeThrowsMade[:\s]*(\d+)',
                'free_throws_attempted': r'protocol\.(?:team\d+\.)?player\d+\.FreeThrowsAttempted[:\s]*(\d+)',
                'minutes': r'protocol\.(?:team\d+\.)?player\d+\.Minutes[:\s]*(\d+(?:\.\d+)?)'
            }
            
            # Ищем имена игроков
            name_pattern = r'protocol\.(?:team\d+\.)?player(\d+)\.Name[:\s]*([^\n\r]+)'
            name_matches = re.findall(name_pattern, page_text)
            
            print(f"🔍 Найдено {len(name_matches)} игроков в protocol")
            
            # Для каждого игрока собираем статистику
            for player_num, player_name in name_matches:
                player_name = player_name.strip()
                if not player_name:
                    continue
                
                player_stats = {
                    'name': player_name,
                    'player_number': player_num,
                    'points': 0,
                    'rebounds': 0,
                    'assists': 0,
                    'steals': 0,
                    'blocks': 0,
                    'turnovers': 0,
                    'fouls': 0,
                    'field_goals_made': 0,
                    'field_goals_attempted': 0,
                    'three_pointers_made': 0,
                    'three_pointers_attempted': 0,
                    'free_throws_made': 0,
                    'free_throws_attempted': 0,
                    'minutes': 0,
                    'team': '',
                    'position': '',
                    'jersey_number': ''
                }
                
                # Извлекаем статистику для каждого игрока
                for stat_name, pattern in stat_patterns.items():
                    # Заменяем player\d+ на конкретный номер игрока
                    specific_pattern = pattern.replace(r'player\d+', f'player{player_num}')
                    matches = re.findall(specific_pattern, page_text)
                    
                    if matches:
                        try:
                            value = float(matches[0]) if '.' in matches[0] else int(matches[0])
                            player_stats[stat_name] = value
                        except (ValueError, IndexError):
                            pass
                
                # Вычисляем проценты попаданий
                if player_stats['field_goals_attempted'] > 0:
                    player_stats['field_goal_percentage'] = round((player_stats['field_goals_made'] / player_stats['field_goals_attempted']) * 100, 1)
                else:
                    player_stats['field_goal_percentage'] = 0.0
                
                if player_stats['three_pointers_attempted'] > 0:
                    player_stats['three_point_percentage'] = round((player_stats['three_pointers_made'] / player_stats['three_pointers_attempted']) * 100, 1)
                else:
                    player_stats['three_point_percentage'] = 0.0
                
                if player_stats['free_throws_attempted'] > 0:
                    player_stats['free_throw_percentage'] = round((player_stats['free_throws_made'] / player_stats['free_throws_attempted']) * 100, 1)
                else:
                    player_stats['free_throw_percentage'] = 0.0
                
                # Определяем команду игрока
                team_pattern = r'protocol\.team(\d+)\.player' + player_num
                team_matches = re.findall(team_pattern, page_text)
                if team_matches:
                    player_stats['team'] = f"Team{team_matches[0]}"
                
                players_stats.append(player_stats)
                print(f"   📊 {player_name}: {player_stats['points']} очков, {player_stats['rebounds']} подборов, {player_stats['steals']} перехватов")
            
            return players_stats
            
        except Exception as e:
            print(f"❌ Ошибка парсинга protocol статистики: {e}")
            return []
    
    def parse_html_statistics_table(self, soup) -> List[Dict]:
        """Парсит статистику игроков из HTML таблицы"""
        try:
            players_stats = []
            
            # Ищем таблицу со статистикой
            stats_table = soup.find('table', class_='statistics__table')
            if not stats_table:
                print("⚠️ Таблица статистики не найдена")
                return []
            
            print("✅ Найдена таблица статистики")
            
            # Получаем заголовки таблицы
            headers = []
            header_row = stats_table.find('thead')
            if header_row:
                header_cells = header_row.find_all('th')
                headers = [cell.get_text().strip() for cell in header_cells]
                print(f"📋 Заголовки таблицы: {headers}")
            
            # Получаем строки с данными игроков
            tbody = stats_table.find('tbody')
            if not tbody:
                print("⚠️ Тело таблицы не найдено")
                return []
            
            rows = tbody.find_all('tr')
            print(f"🔍 Найдено {len(rows)} строк с данными игроков")
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 3:  # Минимум: имя, команда, очки
                    continue
                
                # Извлекаем данные игрока
                player_data = {}
                
                # Имя игрока (обычно в первой колонке)
                player_name_cell = cells[0]
                player_name = player_name_cell.get_text().strip()
                if not player_name:
                    continue
                
                player_data['name'] = player_name
                
                # Извлекаем статистику по колонкам
                for i, cell in enumerate(cells[1:], 1):  # Пропускаем первую колонку с именем
                    if i >= len(headers):
                        continue
                    
                    header = headers[i].lower()
                    value_text = cell.get_text().strip()
                    
                    # Пытаемся извлечь числовое значение
                    try:
                        # Убираем проценты и другие символы
                        clean_value = re.sub(r'[^\d.,]', '', value_text)
                        if clean_value:
                            # Заменяем запятую на точку для десятичных чисел
                            clean_value = clean_value.replace(',', '.')
                            if '.' in clean_value:
                                value = float(clean_value)
                            else:
                                value = int(clean_value)
                        else:
                            value = 0
                    except (ValueError, TypeError):
                        value = 0
                    
                    # Маппинг заголовков на поля статистики
                    if 'очк' in header or 'point' in header or 'pts' in header:
                        player_data['points'] = value
                    elif 'подбор' in header or 'rebound' in header or 'reb' in header:
                        player_data['rebounds'] = value
                    elif 'передач' in header or 'assist' in header or 'ast' in header:
                        player_data['assists'] = value
                    elif 'перехват' in header or 'steal' in header or 'stl' in header:
                        player_data['steals'] = value
                    elif 'блок' in header or 'block' in header or 'blk' in header:
                        player_data['blocks'] = value
                    elif 'потер' in header or 'turnover' in header or 'tov' in header:
                        player_data['turnovers'] = value
                    elif 'фол' in header or 'foul' in header or 'pf' in header:
                        player_data['fouls'] = value
                    elif 'попад' in header and 'попыт' in header:
                        # Это может быть процент попаданий
                        player_data['field_goal_percentage'] = value
                    elif 'попад' in header:
                        player_data['field_goals_made'] = value
                    elif 'попыт' in header:
                        player_data['field_goals_attempted'] = value
                    elif '3-очк' in header and 'попад' in header:
                        player_data['three_pointers_made'] = value
                    elif '3-очк' in header and 'попыт' in header:
                        player_data['three_pointers_attempted'] = value
                    elif 'штраф' in header and 'попад' in header:
                        player_data['free_throws_made'] = value
                    elif 'штраф' in header and 'попыт' in header:
                        player_data['free_throws_attempted'] = value
                    elif 'минут' in header or 'minute' in header or 'min' in header:
                        player_data['minutes'] = value
                
                # Устанавливаем значения по умолчанию для отсутствующих полей
                default_stats = {
                    'points': 0, 'rebounds': 0, 'assists': 0, 'steals': 0, 'blocks': 0,
                    'turnovers': 0, 'fouls': 0, 'field_goals_made': 0, 'field_goals_attempted': 0,
                    'three_pointers_made': 0, 'three_pointers_attempted': 0,
                    'free_throws_made': 0, 'free_throws_attempted': 0, 'minutes': 0,
                    'team': '', 'position': '', 'jersey_number': ''
                }
                
                for key, default_value in default_stats.items():
                    if key not in player_data:
                        player_data[key] = default_value
                
                # Вычисляем проценты попаданий
                if player_data['field_goals_attempted'] > 0:
                    player_data['field_goal_percentage'] = round((player_data['field_goals_made'] / player_data['field_goals_attempted']) * 100, 1)
                else:
                    player_data['field_goal_percentage'] = 0.0
                
                if player_data['three_pointers_attempted'] > 0:
                    player_data['three_point_percentage'] = round((player_data['three_pointers_made'] / player_data['three_pointers_attempted']) * 100, 1)
                else:
                    player_data['three_point_percentage'] = 0.0
                
                if player_data['free_throws_attempted'] > 0:
                    player_data['free_throw_percentage'] = round((player_data['free_throws_made'] / player_data['free_throws_attempted']) * 100, 1)
                else:
                    player_data['free_throw_percentage'] = 0.0
                
                players_stats.append(player_data)
                print(f"   📊 {player_name}: {player_data['points']} очков, {player_data['rebounds']} подборов, {player_data['steals']} перехватов")
            
            return players_stats
            
        except Exception as e:
            print(f"❌ Ошибка парсинга HTML таблицы статистики: {e}")
            return []
    
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
            game_info = await self.parse_game_info(api_data, game_url)
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
            quarters = result.get('quarters', [])
            if quarters and isinstance(quarters[0], dict):
                print(f"   📈 Четверти: {[q['total'] for q in quarters]}")
            else:
                print(f"   📈 Четверти: {quarters}")
            print(f"   📅 Дата: {result.get('date', 'Неизвестно')}")
            print(f"   🕐 Время: {result.get('time', 'Неизвестно')}")
            print(f"   📍 Место: {result.get('venue', 'Неизвестно')}")
            print(f"   🏆 Статус: {'Завершена' if result.get('is_finished') else 'В процессе'}")
            
            # Показываем статистику игроков
            player_stats = result.get('player_stats')
            if player_stats:
                print(f"\n🏆 СТАТИСТИКА ИГРОКОВ:")
                print(f"   📊 Всего игроков: {player_stats.get('total_players', 0)}")
                print(f"   🔍 Источник: {player_stats.get('source', 'API')}")
                
                best_players = player_stats.get('best_players', {})
                if best_players:
                    print(f"\n   🏆 ЛУЧШИЕ ИГРОКИ:")
                    if 'mvp' in best_players:
                        mvp = best_players['mvp']
                        print(f"      🥇 MVP: {mvp['name']} - {mvp['points']} очков ({mvp['field_goal_percentage']}%)")
                    if 'best_rebounder' in best_players:
                        reb = best_players['best_rebounder']
                        print(f"      🏀 Подборы: {reb['name']} - {reb['rebounds']}")
                    if 'best_stealer' in best_players:
                        stl = best_players['best_stealer']
                        print(f"      🥷 Перехваты: {stl['name']} - {stl['steals']}")
                    if 'best_assister' in best_players:
                        ast = best_players['best_assister']
                        print(f"      🎯 Передачи: {ast['name']} - {ast['assists']}")
                    if 'best_blocker' in best_players:
                        blk = best_players['best_blocker']
                        print(f"      🚫 Блокшоты: {blk['name']} - {blk['blocks']}")
            else:
                print(f"\n⚠️ Статистика игроков недоступна")
        else:
            print(f"❌ Парсинг не удался")

if __name__ == "__main__":
    asyncio.run(test_parser())
