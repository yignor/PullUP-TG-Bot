#!/usr/bin/env python3
"""
Система уведомлений на основе Infobasket API
Использует параметры IsToday, GameStatus и другие для мониторинга игр
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class InfobasketNotifications:
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
        
        for game in games:
            team_a = game.get('ShortTeamNameAru', '')
            team_b = game.get('ShortTeamNameBru', '')
            team_a_full = game.get('TeamNameAru', '')
            team_b_full = game.get('TeamNameBru', '')
            
            for target_team in self.target_teams:
                if (target_team.upper() in team_a.upper() or 
                    target_team.upper() in team_b.upper() or
                    target_team.upper() in team_a_full.upper() or
                    target_team.upper() in team_b_full.upper()):
                    filtered_games.append(game)
                    break
        
        return filtered_games
    
    def get_today_games(self, games: List[Dict]) -> List[Dict]:
        """Получает игры на сегодня (IsToday = true)"""
        today_games = []
        
        for game in games:
            if game.get('IsToday', False):
                today_games.append(game)
                print(f"📅 Игра сегодня: {game.get('ShortTeamNameAru')} vs {game.get('ShortTeamNameBru')} в {game.get('GameTimeMsk')}")
        
        return today_games
    
    def get_upcoming_games(self, games: List[Dict], days_ahead: int = 7) -> List[Dict]:
        """Получает предстоящие игры на N дней вперед"""
        upcoming_games = []
        
        for game in games:
            days_from_today = game.get('DaysFromToday', 999)
            if 0 <= days_from_today <= days_ahead:
                upcoming_games.append(game)
                print(f"🔮 Игра через {days_from_today} дней: {game.get('ShortTeamNameAru')} vs {game.get('ShortTeamNameBru')} ({game.get('GameDate')})")
        
        return upcoming_games
    
    def get_finished_games(self, games: List[Dict]) -> List[Dict]:
        """Получает завершенные игры (GameStatus = 1)"""
        finished_games = []
        
        for game in games:
            if game.get('GameStatus') == 1:  # Завершенная игра
                finished_games.append(game)
                print(f"✅ Завершенная игра: {game.get('ShortTeamNameAru')} vs {game.get('ShortTeamNameBru')} ({game.get('ScoreA')}-{game.get('ScoreB')})")
        
        return finished_games
    
    def get_scheduled_games(self, games: List[Dict]) -> List[Dict]:
        """Получает запланированные игры (GameStatus = 0)"""
        scheduled_games = []
        
        for game in games:
            if game.get('GameStatus') == 0:  # Запланированная игра
                scheduled_games.append(game)
                print(f"⏰ Запланированная игра: {game.get('ShortTeamNameAru')} vs {game.get('ShortTeamNameBru')} ({game.get('GameDate')} {game.get('GameTimeMsk')})")
        
        return scheduled_games
    
    def get_games_by_status(self, games: List[Dict]) -> Dict[str, List[Dict]]:
        """Группирует игры по статусам"""
        return {
            'today': self.get_today_games(games),
            'upcoming': self.get_upcoming_games(games),
            'finished': self.get_finished_games(games),
            'scheduled': self.get_scheduled_games(games)
        }
    
    async def get_team_games(self, team_type: str) -> List[Dict]:
        """Получает игры для конкретного состава"""
        if team_type not in self.tags:
            return []
            
        tag = self.tags[team_type]
        
        # Получаем сезоны
        seasons = await self.get_seasons_for_tag(tag)
        if not seasons:
            return []
        
        # Находим активный сезон
        active_season = self.get_active_season(seasons)
        if not active_season:
            return []
        
        comp_id = active_season.get('CompID')
        if not comp_id:
            return []
        
        # Получаем календарь игр
        games = await self.get_calendar_for_comp(comp_id)
        if not games:
            return []
        
        # Фильтруем по нашим командам
        filtered_games = self.filter_games_by_teams(games)
        
        return filtered_games
    
    async def get_all_team_games(self) -> Dict[str, List[Dict]]:
        """Получает игры для всех составов"""
        all_games = {}
        
        for team_type in self.tags.keys():
            print(f"\\n🔍 Получение игр для {team_type}...")
            games = await self.get_team_games(team_type)
            all_games[team_type] = games
            print(f"✅ Найдено {len(games)} игр для {team_type}")
        
        return all_games
    
    def format_game_notification(self, game: Dict, notification_type: str) -> str:
        """Форматирует уведомление об игре"""
        team_a = game.get('ShortTeamNameAru', '')
        team_b = game.get('ShortTeamNameBru', '')
        date = game.get('GameDate', '')
        time = game.get('GameTimeMsk', '')
        venue = game.get('ArenaRu', '')
        comp_name = game.get('CompNameRu', '')
        
        if notification_type == 'today':
            return f"🏀 ИГРА СЕГОДНЯ\\n{team_a} vs {team_b}\\n⏰ {time}\\n📍 {venue}\\n🏆 {comp_name}"
        
        elif notification_type == 'upcoming':
            days = game.get('DaysFromToday', 0)
            return f"🔮 ИГРА ЧЕРЕЗ {days} ДНЕЙ\\n{team_a} vs {team_b}\\n📅 {date} {time}\\n📍 {venue}\\n🏆 {comp_name}"
        
        elif notification_type == 'finished':
            score_a = game.get('ScoreA', 0)
            score_b = game.get('ScoreB', 0)
            return f"✅ ИГРА ЗАВЕРШЕНА\\n{team_a} vs {team_b}\\n🏆 {comp_name}\\n📊 {score_a} - {score_b}"
        
        elif notification_type == 'scheduled':
            return f"⏰ ЗАПЛАНИРОВАНА ИГРА\\n{team_a} vs {team_b}\\n📅 {date} {time}\\n📍 {venue}\\n🏆 {comp_name}"
        
        return f"🏀 {team_a} vs {team_b} - {date} {time}"

async def main():
    """Тестирование системы уведомлений"""
    notifications = InfobasketNotifications()
    
    try:
        print("🔍 Получение игр для всех составов...")
        all_games = await notifications.get_all_team_games()
        
        print(f"\\n{'='*60}")
        print("АНАЛИЗ ИГР ПО СТАТУСАМ")
        print(f"{'='*60}")
        
        for team_type, games in all_games.items():
            print(f"\\n🎮 {team_type.upper()}: {len(games)} игр")
            
            if games:
                # Анализируем игры по статусам
                status_games = notifications.get_games_by_status(games)
                
                print(f"  📅 Игр сегодня: {len(status_games['today'])}")
                print(f"  🔮 Предстоящих (7 дней): {len(status_games['upcoming'])}")
                print(f"  ✅ Завершенных: {len(status_games['finished'])}")
                print(f"  ⏰ Запланированных: {len(status_games['scheduled'])}")
                
                # Показываем уведомления
                if status_games['today']:
                    print(f"\\n  📅 ИГРЫ СЕГОДНЯ:")
                    for game in status_games['today']:
                        notification = notifications.format_game_notification(game, 'today')
                        print(f"    {notification}")
                
                if status_games['upcoming']:
                    print(f"\\n  🔮 ПРЕДСТОЯЩИЕ ИГРЫ:")
                    for game in status_games['upcoming'][:3]:  # Показываем первые 3
                        notification = notifications.format_game_notification(game, 'upcoming')
                        print(f"    {notification}")
                
                if status_games['scheduled']:
                    print(f"\\n  ⏰ ЗАПЛАНИРОВАННЫЕ ИГРЫ:")
                    for game in status_games['scheduled'][:3]:  # Показываем первые 3
                        notification = notifications.format_game_notification(game, 'scheduled')
                        print(f"    {notification}")
            else:
                print("  ❌ Игры не найдены")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
