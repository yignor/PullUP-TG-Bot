#!/usr/bin/env python3
# pyright: reportGeneralTypeIssues=false, reportMissingModuleSource=false, reportReturnType=false
"""
Умный парсер для Infobasket API с правильной логикой дат
Сравнивает даты игр с текущей датой по Москве для определения будущих/прошедших игр
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Any, List, Dict, Optional
import pytz

class InfobasketSmartParser:
    def __init__(
        self,
        comp_ids: Optional[List[int]] = None,
        team_ids: Optional[List[int]] = None,
        team_name_keywords: Optional[List[str]] = None
    ):
        self.org_api_url = "https://org.infobasket.su"
        self.reg_api_url = "https://reg.infobasket.su"
        
        sanitized_keywords = []
        if team_name_keywords:
            for name in team_name_keywords:
                if isinstance(name, str) and name.strip():
                    sanitized_keywords.append(name.strip())
        self.target_teams = sanitized_keywords
        
        self.custom_comp_ids = self._normalize_id_list(comp_ids)
        self.team_ids = self._normalize_id_list(team_ids)
        self.config_mode = bool(self.custom_comp_ids)
        self.team_ids_set = set(self.team_ids)
        
        # Теги для разных составов (fallback)
        self.tags = {
            'first_team': 'reg-78-ll-pl',
            'farm_team': 'reg-78-ll-lr'
        }
        
        # Московское время
        self.moscow_tz = pytz.timezone('Europe/Moscow')
        
    def get_moscow_date(self) -> datetime:
        """Получает текущую дату по Москве"""
        return datetime.now(self.moscow_tz)
    
    @staticmethod
    def _normalize_id_list(values: Optional[List[int]]) -> List[int]:
        """Преобразует входной список в список уникальных целых чисел"""
        if not values:
            return []
        normalized: List[int] = []
        for value in values:
            try:
                normalized.append(int(str(value).strip()))
            except (TypeError, ValueError):
                continue
        return sorted(set(normalized))
    
    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
        """Безопасно преобразует значение в int"""
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return None
    
    def parse_game_date(self, date_str: str) -> datetime:
        """Парсит дату игры из строки формата DD.MM.YYYY"""
        try:
            # Парсим дату в формате DD.MM.YYYY
            game_date = datetime.strptime(date_str, '%d.%m.%Y')
            # Устанавливаем московский часовой пояс
            game_date = self.moscow_tz.localize(game_date)
            return game_date
        except ValueError:
            return None
    
    def is_future_game(self, game_date: datetime) -> bool:
        """Проверяет, является ли игра будущей"""
        today = self.get_moscow_date().date()
        return game_date.date() > today
    
    def is_today_game(self, game_date: datetime) -> bool:
        """Проверяет, является ли игра сегодняшней"""
        today = self.get_moscow_date().date()
        return game_date.date() == today
    
    def is_past_game(self, game_date: datetime) -> bool:
        """Проверяет, является ли игра прошедшей"""
        today = self.get_moscow_date().date()
        return game_date.date() < today
    
    async def get_seasons_for_tag(self, tag: str) -> List[Dict]:
        """Получает сезоны по тегу"""
        url = f"{self.org_api_url}/Comp/GetSeasonsForTag?tag={tag}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        print(f"❌ Ошибка получения сезонов: {response.status}")
                        return []
            except Exception as e:
                print(f"❌ Исключение при получении сезонов: {e}")
                return []
    
    def get_active_season(self, seasons: List[Dict]) -> Optional[Dict]:
        """Находит активный сезон (самый новый)"""
        if not seasons:
            return None
            
        sorted_seasons = sorted(seasons, key=lambda x: x.get('SeasonYear', 0), reverse=True)
        return sorted_seasons[0]
    
    async def get_calendar_for_comp(self, comp_id: int) -> List[Dict]:
        """Получает календарь игр для соревнования"""
        url = f"{self.reg_api_url}/Comp/GetCalendar/?comps={comp_id}&format=json"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        print(f"❌ Ошибка получения календаря: {response.status}")
                        return []
            except Exception as e:
                print(f"❌ Исключение при получении календаря: {e}")
                return []
    
    def filter_games_by_teams(self, games: List[Dict]) -> List[Dict]:
        """Фильтрует игры по нашим командам"""
        filtered_games = []
        
        if not games:
            return filtered_games
        
        if not self.team_ids_set and not self.target_teams:
            return games
        
        for game in games:
            # 1) Предпочитаем фильтрацию по ID
            team1_raw = game.get('Team1ID', game.get('TeamAid'))
            team2_raw = game.get('Team2ID', game.get('TeamBid'))
            team1_id = self._to_int(team1_raw)
            team2_id = self._to_int(team2_raw)
            if self.team_ids_set and (
                (team1_id is not None and team1_id in self.team_ids_set) or
                (team2_id is not None and team2_id in self.team_ids_set)
            ):
                if team1_id is not None:
                    game['Team1ID'] = team1_id
                if team2_id is not None:
                    game['Team2ID'] = team2_id
                filtered_games.append(game)
                continue

            # 2) Fallback по названиям, если ID отсутствуют
            team_a = game.get('ShortTeamNameAru', '')
            team_b = game.get('ShortTeamNameBru', '')
            team_a_full = game.get('TeamNameAru', '')
            team_b_full = game.get('TeamNameBru', '')
            for target_team in self.target_teams:
                target_upper = target_team.upper()
                if (target_upper in team_a.upper() or 
                    target_upper in team_b.upper() or
                    target_upper in team_a_full.upper() or
                    target_upper in team_b_full.upper()):
                    filtered_games.append(game)
                    break
        
        return filtered_games
    
    def categorize_games(self, games: List[Dict]) -> Dict[str, List[Dict]]:
        """Категоризирует игры по датам"""
        today = self.get_moscow_date()
        
        future_games = []
        today_games = []
        past_games = []
        
        for game in games:
            date_str = game.get('GameDate', '')
            if not date_str:
                continue
                
            game_date = self.parse_game_date(date_str)
            if not game_date:
                continue
            
            if self.is_future_game(game_date):
                future_games.append(game)
                print(f"🔮 БУДУЩАЯ ИГРА: {game.get('ShortTeamNameAru')} vs {game.get('ShortTeamNameBru')} ({date_str})")
            elif self.is_today_game(game_date):
                today_games.append(game)
                print(f"📅 ИГРА СЕГОДНЯ: {game.get('ShortTeamNameAru')} vs {game.get('ShortTeamNameBru')} ({date_str})")
            else:
                past_games.append(game)
                print(f"✅ ПРОШЕДШАЯ ИГРА: {game.get('ShortTeamNameAru')} vs {game.get('ShortTeamNameBru')} ({date_str})")
        
        return {
            'future': future_games,
            'today': today_games,
            'past': past_games
        }
    
    def format_poll_data(self, game: Dict) -> Dict:
        """Форматирует данные для создания опроса"""
        return {
            'game_id': game.get('GameID'),
            'date': game.get('GameDate'),
            'time': game.get('GameTimeMsk'),
            'team_a': game.get('ShortTeamNameAru'),
            'team_b': game.get('ShortTeamNameBru'),
            'venue': game.get('ArenaRu'),
            'comp_name': game.get('CompNameRu'),
            'comp_id': game.get('CompID'),
            'game_link': f"https://www.fbp.ru/game.html?gameId={game.get('GameID')}&apiUrl=https://reg.infobasket.su&lang=ru"
        }
    
    def format_announcement_data(self, game: Dict) -> Dict:
        """Форматирует данные для создания анонса"""
        return {
            'game_id': game.get('GameID'),
            'date': game.get('GameDate'),
            'time': game.get('GameTimeMsk'),
            'team_a': game.get('ShortTeamNameAru'),
            'team_b': game.get('ShortTeamNameBru'),
            'venue': game.get('ArenaRu'),
            'comp_name': game.get('CompNameRu'),
            'comp_id': game.get('CompID'),
            'display_date': game.get('DisplayDateTimeMsk'),
            'game_link': f"https://www.fbp.ru/game.html?gameId={game.get('GameID')}&apiUrl=https://reg.infobasket.su&lang=ru"
        }
    
    async def get_team_games(self, team_type: str) -> Dict[str, List[Dict]]:
        """Получает игры для конкретного состава с правильной категоризацией"""
        if team_type not in self.tags:
            return {'future': [], 'today': [], 'past': []}
            
        tag = self.tags[team_type]
        
        # Получаем сезоны
        seasons = await self.get_seasons_for_tag(tag)
        if not seasons:
            return {'future': [], 'today': [], 'past': []}
        
        # Находим активный сезон
        active_season = self.get_active_season(seasons)
        if not active_season:
            return {'future': [], 'today': [], 'past': []}
        
        comp_id = active_season.get('CompID')
        if not comp_id:
            return {'future': [], 'today': [], 'past': []}
        
        # Получаем календарь игр
        games = await self.get_calendar_for_comp(comp_id)
        if not games:
            return {'future': [], 'today': [], 'past': []}
        
        # Фильтруем по нашим командам
        filtered_games = self.filter_games_by_teams(games)
        
        # Категоризируем по датам
        categorized = self.categorize_games(filtered_games)
        
        return categorized
    
    async def get_all_team_games(self) -> Dict[str, Dict[str, List[Dict]]]:
        """Получает игры с учетом конфигурации или по тегам"""
        if self.config_mode:
            return await self._get_games_for_config_ids()
        
        all_games = {}
        
        for team_type in self.tags.keys():
            games = await self.get_team_games(team_type)
            all_games[team_type] = games
            
        return all_games
    
    async def _get_games_for_config_ids(self) -> Dict[str, Dict[str, List[Dict]]]:
        """Получает игры на основе конфигурации ID соревнований"""
        aggregated_games: List[Dict] = []
        
        if not self.custom_comp_ids:
            print("⚠️ Конфигурация соревнований пуста, возвращаем пустой список игр")
            return {'configured': {'future': [], 'today': [], 'past': []}}
        
        for comp_id in self.custom_comp_ids:
            print(f"\n🔍 Получаем календарь для соревнования {comp_id}")
            games = await self.get_calendar_for_comp(comp_id)
            if not games:
                print(f"⚠️ Игры не найдены для соревнования {comp_id}")
                continue
            
            for game in games:
                game.setdefault('CompID', comp_id)
            
            filtered = self.filter_games_by_teams(games)
            
            if self.team_ids_set:
                for game in filtered:
                    team1_id = self._to_int(game.get('Team1ID'))
                    team2_id = self._to_int(game.get('Team2ID'))
                    configured_team_id = None
                    opponent_team_id = None
                    
                    if team1_id in self.team_ids_set:
                        configured_team_id = team1_id
                        opponent_team_id = team2_id
                    elif team2_id in self.team_ids_set:
                        configured_team_id = team2_id
                        opponent_team_id = team1_id
                    
                    if configured_team_id is not None:
                        game['ConfiguredTeamID'] = configured_team_id
                    if opponent_team_id is not None:
                        game['OpponentTeamID'] = opponent_team_id
            
            aggregated_games.extend(filtered)
        
        categorized = self.categorize_games(aggregated_games)
        return {'configured': categorized}
    
    def get_polls_to_create(self, all_games: Dict[str, Dict[str, List[Dict]]]) -> List[Dict]:
        """Определяет, какие опросы нужно создать"""
        polls_to_create = []
        
        for team_type, games in all_games.items():
            for game in games['future']:
                poll_data = self.format_poll_data(game)
                poll_data['team_type'] = team_type
                polls_to_create.append(poll_data)
        
        return polls_to_create
    
    def get_announcements_to_send(self, all_games: Dict[str, Dict[str, List[Dict]]]) -> List[Dict]:
        """Определяет, какие анонсы нужно отправить"""
        announcements_to_send = []
        
        for team_type, games in all_games.items():
            for game in games['today']:
                announcement_data = self.format_announcement_data(game)
                announcement_data['team_type'] = team_type
                announcements_to_send.append(announcement_data)
        
        return announcements_to_send

async def main():
    """Тестирование умного парсера"""
    parser = InfobasketSmartParser()
    
    try:
        print("🔍 Получение игр для всех составов...")
        all_games = await parser.get_all_team_games()
        
        print(f"\n{'='*60}")
        print("АНАЛИЗ ИГР ПО ДАТАМ")
        print(f"{'='*60}")
        
        # Определяем опросы для создания
        polls_to_create = parser.get_polls_to_create(all_games)
        print(f"\n📊 ОПРОСЫ ДЛЯ СОЗДАНИЯ: {len(polls_to_create)}")
        for poll in polls_to_create:
            print(f"  🔮 {poll['team_type']}: {poll['team_a']} vs {poll['team_b']} ({poll['date']} {poll['time']})")
            print(f"     Ссылка: {poll['game_link']}")
        
        # Определяем анонсы для отправки
        announcements_to_send = parser.get_announcements_to_send(all_games)
        print(f"\n📊 АНОНСЫ ДЛЯ ОТПРАВКИ: {len(announcements_to_send)}")
        for announcement in announcements_to_send:
            print(f"  📅 {announcement['team_type']}: {announcement['team_a']} vs {announcement['team_b']} ({announcement['date']} {announcement['time']})")
            print(f"     Ссылка: {announcement['game_link']}")
        
        # Показываем статистику
        print(f"\n📈 СТАТИСТИКА:")
        for team_type, games in all_games.items():
            print(f"  {team_type}: {len(games['future'])} будущих, {len(games['today'])} сегодня, {len(games['past'])} прошедших")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
