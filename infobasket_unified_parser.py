#!/usr/bin/env python3
"""
Универсальный парсер для Infobasket API - работает с обоими составами:
1. Первый состав (reg-78-ll-pl)
2. Фарм состав (reg-78-ll-lr)
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import List, Dict, Optional

class InfobasketUnifiedParser:
    def __init__(self):
        self.org_api_url = "https://org.infobasket.su"
        self.reg_api_url = "https://reg.infobasket.su"
        self.target_teams = ["PULL UP", "PULLUP", "Атлант", "АТЛАНТ", "Атлант 40"]
        
        # Теги для разных составов
        self.tags = {
            'first_team': 'reg-78-ll-pl',
            'farm_team': 'reg-78-ll-lr'
        }
        
    async def get_seasons_for_tag(self, tag: str) -> List[Dict]:
        """Получает сезоны по тегу"""
        url = f"{self.org_api_url}/Comp/GetSeasonsForTag?tag={tag}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Получены сезоны для тега {tag}: {len(data)} сезонов")
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
            
        # Сортируем по году (самый новый первый)
        sorted_seasons = sorted(seasons, key=lambda x: x.get('SeasonYear', 0), reverse=True)
        active_season = sorted_seasons[0]
        
        print(f"🎯 Активный сезон: {active_season.get('NameRu', 'Без названия')} (ID: {active_season.get('CompID', 'Нет ID')}, Год: {active_season.get('SeasonYear', 'Нет года')})")
        return active_season
    
    async def get_calendar_for_comp(self, comp_id: int) -> List[Dict]:
        """Получает календарь игр для соревнования"""
        url = f"{self.reg_api_url}/Comp/GetCalendar/?comps={comp_id}&format=json"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Получен календарь для соревнования {comp_id}: {len(data)} игр")
                        return data
                    else:
                        print(f"❌ Ошибка получения календаря: {response.status}")
                        return []
            except Exception as e:
                print(f"❌ Исключение при получении календаря: {e}")
                return []
    
    def filter_games_by_teams(self, games: List[Dict], team_type: str = "first") -> List[Dict]:
        """Фильтрует игры по нашим командам"""
        filtered_games = []
        
        for game in games:
            # Проверяем названия команд
            team_a = game.get('ShortTeamNameAru', '')
            team_b = game.get('ShortTeamNameBru', '')
            team_a_full = game.get('TeamNameAru', '')
            team_b_full = game.get('TeamNameBru', '')
            
            # Ищем наши команды
            for target_team in self.target_teams:
                if (target_team.upper() in team_a.upper() or 
                    target_team.upper() in team_b.upper() or
                    target_team.upper() in team_a_full.upper() or
                    target_team.upper() in team_b_full.upper()):
                    filtered_games.append(game)
                    print(f"🏀 Найдена игра {team_type}: {team_a} vs {team_b} ({game.get('GameDate', 'Нет даты')})")
                    break
        
        return filtered_games
    
    def normalize_game_data(self, game: Dict, team_type: str = "first") -> Dict:
        """Нормализует данные игры в стандартный формат"""
        return {
            'game_id': game.get('GameID'),
            'date': game.get('GameDate'),
            'time': game.get('GameTime'),
            'time_msk': game.get('GameTimeMsk'),
            'team_a': game.get('ShortTeamNameAru'),
            'team_b': game.get('ShortTeamNameBru'),
            'team_a_full': game.get('TeamNameAru'),
            'team_b_full': game.get('TeamNameBru'),
            'score_a': game.get('ScoreA'),
            'score_b': game.get('ScoreB'),
            'status': game.get('GameStatus'),
            'venue': game.get('ArenaRu'),
            'venue_en': game.get('ArenaEn'),
            'comp_name': game.get('CompNameRu'),
            'league_name': game.get('LeagueNameRu'),
            'display_date': game.get('DisplayDateTimeMsk'),
            'team_type': team_type,
            'game_link': f"http://letobasket.ru/game.html?gameId={game.get('GameID')}&apiUrl=https://reg.infobasket.su&lang=ru"
        }
    
    async def get_schedule_for_team(self, team_type: str) -> List[Dict]:
        """Получает расписание игр для конкретного состава"""
        if team_type not in self.tags:
            print(f"❌ Неизвестный тип команды: {team_type}")
            return []
            
        tag = self.tags[team_type]
        print(f"🔍 Получение расписания для {team_type} (тег: {tag})")
        
        # 1. Получаем сезоны
        seasons = await self.get_seasons_for_tag(tag)
        if not seasons:
            print("❌ Сезоны не найдены")
            return []
        
        # 2. Находим активный сезон
        active_season = self.get_active_season(seasons)
        if not active_season:
            print("❌ Активный сезон не найден")
            return []
        
        comp_id = active_season.get('CompID')
        if not comp_id:
            print("❌ ID соревнования не найден")
            return []
        
        # 3. Получаем календарь игр
        games = await self.get_calendar_for_comp(comp_id)
        if not games:
            print("❌ Игры не найдены")
            return []
        
        # 4. Фильтруем по нашим командам
        filtered_games = self.filter_games_by_teams(games, team_type)
        print(f"🏀 Найдено игр {team_type}: {len(filtered_games)}")
        
        # 5. Нормализуем данные
        normalized_games = []
        for game in filtered_games:
            normalized = self.normalize_game_data(game, team_type)
            normalized_games.append(normalized)
        
        return normalized_games
    
    async def get_all_schedules(self) -> Dict[str, List[Dict]]:
        """Получает расписание для всех составов"""
        all_schedules = {}
        
        for team_type in self.tags.keys():
            print(f"\\n{'='*50}")
            print(f"ОБРАБОТКА {team_type.upper()}")
            print(f"{'='*50}")
            
            schedule = await self.get_schedule_for_team(team_type)
            all_schedules[team_type] = schedule
        
        return all_schedules

async def main():
    """Тестирование универсального парсера"""
    parser = InfobasketUnifiedParser()
    
    try:
        all_schedules = await parser.get_all_schedules()
        
        print(f"\\n{'='*60}")
        print("ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
        print(f"{'='*60}")
        
        for team_type, games in all_schedules.items():
            print(f"\\n🎮 {team_type.upper()}: {len(games)} игр")
            
            if games:
                # Показываем последние 3 игры
                for i, game in enumerate(games[-3:], 1):
                    print(f"  {i}. {game['date']} {game['time_msk']} - {game['team_a']} vs {game['team_b']} ({game['score_a']}-{game['score_b']})")
                    if game['status'] == 0:
                        print(f"     🔮 БУДУЩАЯ ИГРА: {game['game_link']}")
            else:
                print("  ❌ Игры не найдены")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
