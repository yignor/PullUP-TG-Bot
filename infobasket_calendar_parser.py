#!/usr/bin/env python3
"""
Парсер для Infobasket API - получает расписание игр через правильную схему:
1. Получаем сезоны по тегу
2. Находим активный сезон
3. Получаем календарь игр
4. Извлекаем данные об играх
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import List, Dict, Optional

class InfobasketCalendarParser:
    def __init__(self):
        self.org_api_url = "https://org.infobasket.su"
        self.reg_api_url = "https://reg.infobasket.su"
        self.target_teams = ["PULL UP", "PULLUP", "Атлант", "АТЛАНТ", "Атлант 40"]
        
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
        
        print(f"🎯 Активный сезон: {active_season.get('NameRu', 'Без названия')} (ID: {active_season.get('CompID', 'Нет ID')})")
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
    
    def filter_games_by_teams(self, games: List[Dict]) -> List[Dict]:
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
                    print(f"🏀 Найдена игра с командой {target_team}: {team_a} vs {team_b}")
                    break
        
        return filtered_games
    
    def normalize_game_data(self, game: Dict) -> Dict:
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
            'game_link': f"http://letobasket.ru/game.html?gameId={game.get('GameID')}&apiUrl=https://reg.infobasket.su&lang=ru"
        }
    
    async def get_schedule(self, tag: str = "reg-78-ll-pl") -> List[Dict]:
        """Получает расписание игр для тега"""
        print(f"🔍 Получение расписания для тега: {tag}")
        
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
        filtered_games = self.filter_games_by_teams(games)
        print(f"🏀 Найдено игр с нашими командами: {len(filtered_games)}")
        
        # 5. Нормализуем данные
        normalized_games = []
        for game in filtered_games:
            normalized = self.normalize_game_data(game)
            normalized_games.append(normalized)
        
        return normalized_games

async def main():
    """Тестирование парсера"""
    parser = InfobasketCalendarParser()
    
    try:
        games = await parser.get_schedule("reg-78-ll-pl")
        
        if games:
            print(f"\\n🎮 НАЙДЕННЫЕ ИГРЫ ({len(games)}):")
            for i, game in enumerate(games, 1):
                print(f"\\n--- Игра {i} ---")
                print(f"ID: {game['game_id']}")
                print(f"Дата: {game['date']}")
                print(f"Время: {game['time_msk']}")
                print(f"Команды: {game['team_a']} vs {game['team_b']}")
                print(f"Счет: {game['score_a']} - {game['score_b']}")
                print(f"Статус: {game['status']}")
                print(f"Место: {game['venue']}")
                print(f"Соревнование: {game['comp_name']}")
                print(f"Ссылка: {game['game_link']}")
        else:
            print("\\n❌ Игры не найдены")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
