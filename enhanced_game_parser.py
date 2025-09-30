#!/usr/bin/env python3
"""
Улучшенный парсер игр, который работает с API напрямую
"""

import asyncio
import aiohttp
import json
import re
import ssl
from typing import Dict, List, Optional, Any
from datetime import datetime
from datetime_utils import get_moscow_time

class EnhancedGameParser:
    """Улучшенный парсер игр, работающий с API"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        # Создаем SSL context с отключенной проверкой сертификатов
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)
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
            
            # URL для получения данных игры (только GetOnline, содержит все данные)
            online_api_url = f"{api_url}/Widget/GetOnline/{game_id}?format=json&lang=ru"
            
            print(f"🔍 Запрашиваем данные игры через API:")
            print(f"   Online API: {online_api_url}")
            
            # Запрашиваем данные игры
            async with self.session.get(online_api_url) as online_response:
                
                if online_response.status == 200:
                    online_data = await online_response.json()
                    
                    print(f"✅ Данные получены успешно")
                    print(f"   Online data keys: {list(online_data.keys())[:15]}")
                    
                    # GetOnline содержит все данные, включая Protocol с игроками
                    return {
                        'game': online_data,  # Используем online_data как game
                        'online': online_data
                    }
                else:
                    print(f"❌ Ошибка API: Online={online_response.status}")
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
                # Используем московское время вместо системного
                dt = datetime.fromtimestamp(timestamp, tz=get_moscow_time().tzinfo)
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
                # Используем московское время вместо системного
                dt = datetime.fromtimestamp(timestamp, tz=get_moscow_time().tzinfo)
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
            # Приоритет 1: OnlineTeams (более детальные данные)
            if 'OnlineTeams' in online_data and len(online_data['OnlineTeams']) >= 2:
                teams_data = online_data['OnlineTeams']
            # Приоритет 2: GameTeams
            elif 'GameTeams' in online_data and len(online_data['GameTeams']) >= 2:
                teams_data = online_data['GameTeams']
            elif 'GameTeams' in game_data and len(game_data['GameTeams']) >= 2:
                teams_data = game_data['GameTeams']
            
            if teams_data:
                # Фильтруем команды с TeamNumber 1 и 2
                team1 = None
                team2 = None
                
                for team in teams_data:
                    if team.get('TeamNumber') == 1:
                        team1 = team
                    elif team.get('TeamNumber') == 2:
                        team2 = team
                
                if not team1:
                    team1 = teams_data[0] if len(teams_data) > 0 else {}
                if not team2:
                    team2 = teams_data[1] if len(teams_data) > 1 else {}
                
                # Извлекаем названия команд
                team1_name = 'Команда 1'
                team2_name = 'Команда 2'
                
                # Для OnlineTeams структура проще
                if 'TeamName2' in team1:
                    team1_name = team1.get('TeamName2', team1.get('TeamName1', 'Команда 1'))
                elif 'TeamName' in team1:
                    team1_name = team1['TeamName'].get('CompTeamNameRu', team1['TeamName'].get('CompTeamNameEn', 'Команда 1'))
                elif 'CompTeamNameRu' in team1:
                    team1_name = team1['CompTeamNameRu']
                
                if 'TeamName2' in team2:
                    team2_name = team2.get('TeamName2', team2.get('TeamName1', 'Команда 2'))
                elif 'TeamName' in team2:
                    team2_name = team2['TeamName'].get('CompTeamNameRu', team2['TeamName'].get('CompTeamNameEn', 'Команда 2'))
                elif 'CompTeamNameRu' in team2:
                    team2_name = team2['CompTeamNameRu']
                
                # Получаем счет из GameTeams, если OnlineTeams не содержит Score
                score1 = team1.get('Score', 0)
                score2 = team2.get('Score', 0)
                
                # Если счет нулевой, пробуем взять из GameTeams
                if score1 == 0 and score2 == 0 and 'GameTeams' in online_data:
                    game_teams = online_data['GameTeams']
                    if len(game_teams) >= 2:
                        score1 = game_teams[0].get('Score', 0)
                        score2 = game_teams[1].get('Score', 0)
                
                game_info['teams'] = [
                    {
                        'id': team1.get('TeamID'),
                        'name': team1_name,
                        'short_name': team1.get('TeamName', {}).get('CompTeamShortNameRu', 'К1') if isinstance(team1.get('TeamName'), dict) else 'К1',
                        'score': score1
                    },
                    {
                        'id': team2.get('TeamID'),
                        'name': team2_name,
                        'short_name': team2.get('TeamName', {}).get('CompTeamShortNameRu', 'К2') if isinstance(team2.get('TeamName'), dict) else 'К2',
                        'score': score2
                    }
                ]
                
                # Формируем счет
                game_info['score'] = {
                    'team1': score1,
                    'team2': score2,
                    'total': f"{score1}:{score2}"
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
                
                # Извлекаем лидеров нашей команды
                our_team_leaders = self.find_our_team_leaders(player_stats.get('players', []))
                if our_team_leaders:
                    game_info['our_team_leaders'] = our_team_leaders
                    print(f"🏆 Лидеры нашей команды извлечены: {len(our_team_leaders)} категорий")
            else:
                # Если не удалось получить статистику через API, пробуем через protocol
                print("🔍 Статистика через API не найдена, пробуем через protocol...")
                protocol_stats = await self.parse_game_statistics_from_protocol(game_url)
                if protocol_stats:
                    game_info['player_stats'] = protocol_stats
                    print(f"📊 Статистика игроков извлечена через protocol: {len(protocol_stats.get('players', []))} игроков")
                    
                    # Извлекаем лидеров нашей команды
                    our_team_leaders = self.find_our_team_leaders(protocol_stats.get('players', []))
                    if our_team_leaders:
                        game_info['our_team_leaders'] = our_team_leaders
                        print(f"🏆 Лидеры нашей команды извлечены: {len(our_team_leaders)} категорий")
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
            
            # Ищем статистику игроков в Protocol (приоритет 1)
            if 'Protocol' in online_data and len(online_data['Protocol']) > 0:
                protocol = online_data['Protocol'][0]
                if 'Players' in protocol:
                    players_data = protocol['Players']
                    print(f"🔍 Найдены игроки в Protocol: {len(players_data)} игроков")
                    for player in players_data:
                        # Определяем название команды по номеру
                        team_number = player.get('TeamNumber')
                        team_name = f"Team {team_number}"
                        if team_number and 'OnlineTeams' in online_data:
                            for team in online_data['OnlineTeams']:
                                if team.get('TeamNumber') == team_number:
                                    team_name = team.get('TeamName2', team.get('TeamName1', team_name))
                                    break
                        
                        stats = self.parse_player_statistics_from_api(player, team_name)
                        if (stats and stats.get('name') and 
                            stats.get('name').strip() != '' and 
                            'None' not in stats.get('name', '')):
                            players_stats.append(stats)
            
            # Ищем статистику игроков в GameTeams (приоритет 2)
            elif 'GameTeams' in online_data:
                game_teams = online_data['GameTeams']
                if isinstance(game_teams, list):
                    for team in game_teams:
                        team_name = team.get('TeamName', {})
                        team_name_ru = team_name.get('CompTeamNameRu', 'Неизвестная команда')
                        
                        if 'Players' in team:
                            players_data = team['Players']
                            if isinstance(players_data, list):
                                print(f"🔍 Найдены игроки команды {team_name_ru}: {len(players_data)} игроков")
                                for player in players_data:
                                    stats = self.parse_player_statistics_from_api(player, team_name_ru)
                                    if (stats and stats.get('name') and 
                                        stats.get('name').strip() != '' and 
                                        'None' not in stats.get('name', '')):
                                        players_stats.append(stats)
            
            # Проверяем различные возможные места для статистики
            elif 'Players' in game_data:
                players_data = game_data['Players']
                print(f"🔍 Найдены данные игроков в game.Players: {len(players_data)} игроков")
                
                for player in players_data:
                    player_stat = self.parse_player_statistics(player)
                    if (player_stat and player_stat.get('name') and 
                        player_stat.get('name').strip() != '' and 
                        'None' not in player_stat.get('name', '')):
                        players_stats.append(player_stat)
            
            elif 'TeamPlayers' in game_data:
                # Если статистика по командам
                for team_key in ['Team1', 'Team2']:
                    if team_key in game_data['TeamPlayers']:
                        team_players = game_data['TeamPlayers'][team_key]
                        print(f"🔍 Найдены игроки команды {team_key}: {len(team_players)} игроков")
                        
                        for player in team_players:
                            player_stat = self.parse_player_statistics(player)
                            if (player_stat and player_stat.get('name') and 
                                player_stat.get('name').strip() != '' and 
                                'None' not in player_stat.get('name', '')):
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
                                if (player_stat and player_stat.get('name') and 
                                    player_stat.get('name').strip() != '' and 
                                    'None' not in player_stat.get('name', '')):
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
    
    def parse_player_statistics_from_api(self, player_data: Dict, team_name: str) -> Optional[Dict]:
        """Парсит статистику игрока из API данных"""
        try:
            # Извлекаем основные данные игрока
            first_name = player_data.get('FirstNameRu', '')
            last_name = player_data.get('LastNameRu', '')
            player_name = f"{first_name} {last_name}".strip()
            
            if not player_name or player_name == ' ':
                return None
            
            # Извлекаем статистику из API (используем правильные названия полей)
            stats = {
                'name': player_name,
                'team': team_name,
                'jersey_number': player_data.get('DisplayNumber', ''),
                'person_id': player_data.get('PersonID', 0),
                'player_number': player_data.get('PlayerNumber', 0),
                'points': player_data.get('Points', 0) or 0,
                'rebounds': player_data.get('Rebound', 0) or 0,
                'assists': player_data.get('Assist', 0) or 0,
                'steals': player_data.get('Steal', 0) or 0,
                'blocks': player_data.get('Blocks', 0) or 0,
                'turnovers': player_data.get('Turnover', 0) or 0,
                'fouls': player_data.get('Foul', 0) or 0,
                'field_goals_made': player_data.get('Goal2', 0) or 0,
                'field_goals_attempted': player_data.get('Shot2', 0) or 0,
                'three_pointers_made': player_data.get('Goal3', 0) or 0,
                'three_pointers_attempted': player_data.get('Shot3', 0) or 0,
                'free_throws_made': player_data.get('Goal1', 0) or 0,
                'free_throws_attempted': player_data.get('Shot1', 0) or 0,
                'minutes': player_data.get('PlayedTime', '0:00'),
                'plus_minus': player_data.get('PlusMinus', 0) or 0,
                'opponent_fouls': player_data.get('OpponentFoul', 0) or 0,  # Фолы соперника
                'defensive_rebounds': player_data.get('DefRebound', 0) or 0,
                'offensive_rebounds': player_data.get('OffRebound', 0) or 0,
                'height': player_data.get('Height', 0) or 0,
                'weight': player_data.get('Weight', 0) or 0,
                'position': player_data.get('PosID', 0) or 0,
                'is_captain': player_data.get('Capitan', 0) == 1
            }
            
            # Вычисляем проценты попаданий
            # Общий процент попаданий = (все попадания) / (все попытки) * 100
            total_made = (stats['free_throws_made'] + stats['field_goals_made'] + stats['three_pointers_made'])
            total_attempted = (stats['free_throws_attempted'] + stats['field_goals_attempted'] + stats['three_pointers_attempted'])
            
            if total_attempted > 0:
                stats['field_goal_percentage'] = round((total_made / total_attempted) * 100, 1)
            else:
                stats['field_goal_percentage'] = 0.0
            
            if stats['three_pointers_attempted'] > 0:
                stats['three_point_percentage'] = round((stats['three_pointers_made'] / stats['three_pointers_attempted']) * 100, 1)
            else:
                stats['three_point_percentage'] = 0.0
            
            # Двухочковые отдельно
            if stats['field_goals_attempted'] > 0:
                stats['two_point_percentage'] = round((stats['field_goals_made'] / stats['field_goals_attempted']) * 100, 1)
            else:
                stats['two_point_percentage'] = 0.0

            if stats['free_throws_attempted'] > 0:
                stats['free_throw_percentage'] = round((stats['free_throws_made'] / stats['free_throws_attempted']) * 100, 1)
            else:
                stats['free_throw_percentage'] = 0.0
            
            # Вычисляем КПИ по формуле:
            # КПИ = (Очки + Подборы + Передачи + Перехваты + Блоки + Фолы соперника - Промахи - Потери - Фолы)
            # Промахи = (попытки бросков - попадания)
            misses = total_attempted - total_made
            # Фолы соперника = берем из API, если есть
            opponent_fouls = player_data.get('OpponentFoul', 0) or 0
            
            kpi = (stats['points'] + stats['rebounds'] + stats['assists'] + 
                   stats['steals'] + stats['blocks'] + opponent_fouls - 
                   misses - stats['turnovers'] - stats['fouls'])
            
            stats['plus_minus'] = kpi  # Заменяем plus_minus на КПИ
            stats['kpi'] = kpi  # Добавляем отдельное поле КПИ
            stats['opponent_fouls'] = opponent_fouls  # Сохраняем фолы соперника
            
            return stats
            
        except Exception as e:
            print(f"❌ Ошибка парсинга статистики игрока из API: {e}")
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
            # Общий процент попаданий = (все попадания) / (все попытки) * 100
            total_made = (stats['free_throws_made'] + stats['field_goals_made'] + stats['three_pointers_made'])
            total_attempted = (stats['free_throws_attempted'] + stats['field_goals_attempted'] + stats['three_pointers_attempted'])
            
            if total_attempted and total_attempted > 0:
                stats['field_goal_percentage'] = round((total_made / total_attempted) * 100, 1)
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
            
            # Вычисляем КПИ по формуле:
            # КПИ = (Очки + Подборы + Передачи + Перехваты + Блоки + Фолы соперника - Промахи - Потери - Фолы)
            misses = total_attempted - total_made
            opponent_fouls = stats.get('opponent_fouls', 0) or 0  # Берем из stats, если есть
            
            kpi = (stats['points'] + stats['rebounds'] + stats['assists'] + 
                   stats['steals'] + stats['blocks'] + opponent_fouls - 
                   misses - stats['turnovers'] - stats['fouls'])
            
            stats['plus_minus'] = kpi  # Заменяем plus_minus на КПИ
            stats['kpi'] = kpi  # Добавляем отдельное поле КПИ
            
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
                'field_goal_percentage': mvp.get('field_goal_percentage', 0),
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

            # Лучший плюс/минус
            best_plus_minus = max(players_stats, key=lambda p: p['plus_minus'])
            best_players['best_plus_minus'] = {
                'name': best_plus_minus['name'],
                'plus_minus': best_plus_minus['plus_minus'],
                'team': best_plus_minus['team']
            }

            # Самый играющий игрок (по времени)
            most_playing = max(players_stats, key=lambda p: p.get('minutes', '0:00'))
            best_players['most_playing'] = {
                'name': most_playing['name'],
                'minutes': most_playing.get('minutes', '0:00'),
                'team': most_playing['team']
            }

            print(f"🏆 Лучшие игроки найдены:")
            print(f"   MVP: {best_players['mvp']['name']} ({best_players['mvp']['points']} очков, {best_players['mvp']['field_goal_percentage']}%)")
            print(f"   Подборы: {best_players['best_rebounder']['name']} ({best_players['best_rebounder']['rebounds']})")
            print(f"   Перехваты: {best_players['best_stealer']['name']} ({best_players['best_stealer']['steals']})")
            print(f"   Передачи: {best_players['best_assister']['name']} ({best_players['best_assister']['assists']})")
            print(f"   Блокшоты: {best_players['best_blocker']['name']} ({best_players['best_blocker']['blocks']})")
            print(f"   Плюс/минус: {best_players['best_plus_minus']['name']} ({best_players['best_plus_minus']['plus_minus']})")

            return best_players

        except Exception as e:
            print(f"❌ Ошибка поиска лучших игроков: {e}")
            return {}

    def find_our_team_leaders(self, players_stats: List[Dict], our_team_names: List[str] = None) -> Dict:
        """Находит лидеров и анти-лидеров нашей команды по различным показателям"""
        try:
            if not players_stats:
                return {}

            # Названия наших команд для поиска
            if our_team_names is None:
                our_team_names = ["PULL UP", "Pull Up", "PullUP", "PULL UP фарм", "Pull Up-Фарм"]

            # Фильтруем игроков нашей команды
            our_team_players = []
            for player in players_stats:
                # Проверяем, что игрок валидный (не None и имеет имя)
                if (not player or not player.get('name') or 
                    player.get('name').strip() == '' or 
                    'None' in player.get('name', '')):
                    continue
                    
                team_name = player.get('team', '')
                if any(our_name in team_name for our_name in our_team_names):
                    our_team_players.append(player)

            if not our_team_players:
                print("⚠️ Игроки нашей команды не найдены в статистике")
                return {}

            print(f"🏀 Найдено игроков нашей команды: {len(our_team_players)}")

            leaders = {}

            # Лидер по очкам
            points_leader = max(our_team_players, key=lambda p: p['points'])
            leaders['points'] = {
                'name': points_leader['name'],
                'value': points_leader['points'],
                'percentage': points_leader.get('field_goal_percentage', 0)
            }

            # Лидер по подборам
            rebounds_leader = max(our_team_players, key=lambda p: p['rebounds'])
            leaders['rebounds'] = {
                'name': rebounds_leader['name'],
                'value': rebounds_leader['rebounds']
            }

            # Лидер по передачам
            assists_leader = max(our_team_players, key=lambda p: p['assists'])
            leaders['assists'] = {
                'name': assists_leader['name'],
                'value': assists_leader['assists']
            }

            # Лидер по перехватам
            steals_leader = max(our_team_players, key=lambda p: p['steals'])
            leaders['steals'] = {
                'name': steals_leader['name'],
                'value': steals_leader['steals']
            }

            # Лидер по блокшотам
            blocks_leader = max(our_team_players, key=lambda p: p['blocks'])
            leaders['blocks'] = {
                'name': blocks_leader['name'],
                'value': blocks_leader['blocks']
            }

            # Лидер по КПИ (лучший плюс/минус)
            best_plus_minus = max(our_team_players, key=lambda p: p['plus_minus'])
            leaders['best_plus_minus'] = {
                'name': best_plus_minus['name'],
                'value': best_plus_minus['plus_minus']
            }

            # Анти-лидеры (худшие показатели)
            anti_leaders = {}

            # Анти-лидер по проценту попаданий (самый низкий процент)
            # Фильтруем игроков с валидными именами для анти-лидеров
            valid_players = [p for p in our_team_players if p.get('name') and p.get('name').strip() != '' and 'None' not in p.get('name', '')]
            
            
            if valid_players:
                # Лучшие проценты среди бросавших
                ft_players_best = [p for p in valid_players if p.get('free_throws_attempted', 0) > 0]
                if ft_players_best:
                    best_ft = max(ft_players_best, key=lambda p: p.get('free_throw_percentage', 0))
                    leaders['best_free_throw'] = {
                        'name': best_ft['name'],
                        'value': best_ft.get('free_throw_percentage', 0)
                    }

                two_pt_players_best = [p for p in valid_players if p.get('field_goals_attempted', 0) > 0]
                if two_pt_players_best:
                    best_2p = max(two_pt_players_best, key=lambda p: p.get('two_point_percentage', p.get('field_goal_percentage', 0)))
                    leaders['best_two_point'] = {
                        'name': best_2p['name'],
                        'value': best_2p.get('two_point_percentage', best_2p.get('field_goal_percentage', 0))
                    }

                three_pt_players_best = [p for p in valid_players if p.get('three_pointers_attempted', 0) > 0]
                if three_pt_players_best:
                    best_3p = max(three_pt_players_best, key=lambda p: p.get('three_point_percentage', 0))
                    leaders['best_three_point'] = {
                        'name': best_3p['name'],
                        'value': best_3p.get('three_point_percentage', 0)
                    }

                worst_shooting_leader = min(valid_players, key=lambda p: p.get('field_goal_percentage', 100))
                anti_leaders['worst_shooting'] = {
                    'name': worst_shooting_leader['name'],
                    'value': worst_shooting_leader.get('field_goal_percentage', 0)
                }

                # Анти-лидер по потерям
                turnovers_leader = max(valid_players, key=lambda p: p.get('turnovers', 0))
                anti_leaders['turnovers'] = {
                    'name': turnovers_leader['name'],
                    'value': turnovers_leader.get('turnovers', 0)
                }

                # Анти-лидер по фолам
                fouls_leader = max(valid_players, key=lambda p: p.get('fouls', 0))
                anti_leaders['fouls'] = {
                    'name': fouls_leader['name'],
                    'value': fouls_leader.get('fouls', 0)
                }

                # Анти-лидер по КПИ (самый низкий плюс/минус)
                worst_plus_minus = min(valid_players, key=lambda p: p.get('plus_minus', 0))
                anti_leaders['worst_plus_minus'] = {
                    'name': worst_plus_minus['name'],
                    'value': worst_plus_minus.get('plus_minus', 0)
                }
                
                # Анти-лидер по штрафным броскам (самый низкий процент среди бросавших)
                ft_players = [p for p in valid_players if p.get('free_throws_attempted', 0) > 0]
                if ft_players:
                    worst_free_throw_leader = min(ft_players, key=lambda p: p.get('free_throw_percentage', 100))
                    anti_leaders['worst_free_throw'] = {
                        'name': worst_free_throw_leader['name'],
                        'value': worst_free_throw_leader.get('free_throw_percentage', 0)
                    }
                
                # Анти-лидер по двухочковым броскам (самый низкий процент среди бросавших)
                two_pt_players = [p for p in valid_players if p.get('field_goals_attempted', 0) > 0]
                if two_pt_players:
                    worst_two_point_leader = min(two_pt_players, key=lambda p: p.get('two_point_percentage', p.get('field_goal_percentage', 100)))
                    anti_leaders['worst_two_point'] = {
                        'name': worst_two_point_leader['name'],
                        'value': worst_two_point_leader.get('two_point_percentage', worst_two_point_leader.get('field_goal_percentage', 0))
                    }
                
                # Анти-лидер по трехочковым броскам (самый низкий процент среди бросавших)
                three_pt_players = [p for p in valid_players if p.get('three_pointers_attempted', 0) > 0]
                if three_pt_players:
                    worst_three_point_leader = min(three_pt_players, key=lambda p: p.get('three_point_percentage', 100))
                    anti_leaders['worst_three_point'] = {
                        'name': worst_three_point_leader['name'],
                        'value': worst_three_point_leader.get('three_point_percentage', 0)
                    }
            else:
                print("⚠️ Нет игроков с валидными именами для анти-лидеров")

            leaders['anti_leaders'] = anti_leaders

            print(f"🏆 Лидеры нашей команды:")
            print(f"   Очки: {leaders['points']['name']} ({leaders['points']['value']} очков, {leaders['points']['percentage']}%)")
            print(f"   Подборы: {leaders['rebounds']['name']} ({leaders['rebounds']['value']})")
            print(f"   Передачи: {leaders['assists']['name']} ({leaders['assists']['value']})")
            print(f"   Перехваты: {leaders['steals']['name']} ({leaders['steals']['value']})")
            print(f"   Блокшоты: {leaders['blocks']['name']} ({leaders['blocks']['value']})")

            print(f"😅 Анти-лидеры нашей команды:")
            print(f"   Процент попаданий: {anti_leaders['worst_shooting']['name']} ({anti_leaders['worst_shooting']['value']}%)")
            print(f"   Потери: {anti_leaders['turnovers']['name']} ({anti_leaders['turnovers']['value']})")
            print(f"   Фолы: {anti_leaders['fouls']['name']} ({anti_leaders['fouls']['value']})")
            print(f"   КПИ: {anti_leaders['worst_plus_minus']['name']} ({anti_leaders['worst_plus_minus']['value']})")

            return leaders

        except Exception as e:
            print(f"❌ Ошибка поиска лидеров нашей команды: {e}")
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
                # Общий процент попаданий = (все попадания) / (все попытки) * 100
                total_made = (player_stats['free_throws_made'] + player_stats['field_goals_made'] + player_stats['three_pointers_made'])
                total_attempted = (player_stats['free_throws_attempted'] + player_stats['field_goals_attempted'] + player_stats['three_pointers_attempted'])
                
                if total_attempted > 0:
                    player_stats['field_goal_percentage'] = round((total_made / total_attempted) * 100, 1)
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
                
                # Вычисляем КПИ по формуле:
                # КПИ = (Очки + Подборы + Передачи + Перехваты + Блоки + Фолы соперника - Промахи - Потери - Фолы)
                misses = total_attempted - total_made
                opponent_fouls = player_stats.get('opponent_fouls', 0) or 0  # Берем из данных, если есть
                
                kpi = (player_stats['points'] + player_stats['rebounds'] + player_stats['assists'] + 
                       player_stats['steals'] + player_stats['blocks'] + opponent_fouls - 
                       misses - player_stats['turnovers'] - player_stats['fouls'])
                
                player_stats['plus_minus'] = kpi  # Заменяем plus_minus на КПИ
                player_stats['kpi'] = kpi  # Добавляем отдельное поле КПИ
                
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
                # Общий процент попаданий = (все попадания) / (все попытки) * 100
                total_made = (player_data['free_throws_made'] + player_data['field_goals_made'] + player_data['three_pointers_made'])
                total_attempted = (player_data['free_throws_attempted'] + player_data['field_goals_attempted'] + player_data['three_pointers_attempted'])
                
                if total_attempted > 0:
                    player_data['field_goal_percentage'] = round((total_made / total_attempted) * 100, 1)
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
                
                # Вычисляем КПИ по формуле:
                # КПИ = (Очки + Подборы + Передачи + Перехваты + Блоки + Фолы соперника - Промахи - Потери - Фолы)
                misses = total_attempted - total_made
                opponent_fouls = player_data.get('opponent_fouls', 0) or 0  # Берем из данных, если есть
                
                kpi = (player_data['points'] + player_data['rebounds'] + player_data['assists'] + 
                       player_data['steals'] + player_data['blocks'] + opponent_fouls - 
                       misses - player_data['turnovers'] - player_data['fouls'])
                
                player_data['plus_minus'] = kpi  # Заменяем plus_minus на КПИ
                player_data['kpi'] = kpi  # Добавляем отдельное поле КПИ
                
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
