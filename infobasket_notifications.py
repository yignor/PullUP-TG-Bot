#!/usr/bin/env python3
"""Configurable notification helper for Infobasket competitions."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp
import json

from enhanced_duplicate_protection import duplicate_protection


class InfobasketNotifications:
    """Fetches, filters and groups Infobasket games for configured competitions."""

    def __init__(self) -> None:
        self.reg_api_url = "https://reg.infobasket.su"
        self.comp_ids: List[int] = []
        self.team_ids: List[int] = []
        self.team_name_variants: List[str] = []
        self._load_config()

    def _load_config(self) -> None:
        config = duplicate_protection.get_config_ids()
        self.comp_ids = config.get("comp_ids", []) or []
        self.team_ids = config.get("team_ids", []) or []

        name_variants: List[str] = []
        teams_meta = config.get("teams", {}) or {}
        for team_info in teams_meta.values():
            alt_name = team_info.get("alt_name")
            if isinstance(alt_name, str) and alt_name.strip():
                name_variants.append(alt_name.strip())
            metadata = team_info.get("metadata") or {}
            aliases = metadata.get("aliases") if isinstance(metadata, dict) else []
            if isinstance(aliases, list):
                for alias in aliases:
                    if isinstance(alias, str) and alias.strip():
                        name_variants.append(alias.strip())

        self.team_name_variants = list({name.lower() for name in name_variants if name})

    async def get_calendar_for_comp(self, comp_id: int) -> List[Dict]:
        """Fetches the calendar for the given competition ID."""
        url = f"{self.reg_api_url}/Comp/GetCalendar/?comps={comp_id}&format=json"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    print(f"❌ Не удалось получить календарь для {comp_id}: HTTP {response.status}")
            except Exception as error:
                print(f"❌ Ошибка получения календаря для {comp_id}: {error}")
        return []

    def filter_games_by_config(self, games: List[Dict]) -> List[Dict]:
        """Filters games that involve configured team IDs or name variants."""
        filtered: List[Dict] = []
        for game in games:
            team1_id = game.get("Team1ID")
            team2_id = game.get("Team2ID")
            if (
                isinstance(team1_id, int)
                and team1_id in self.team_ids
                or isinstance(team2_id, int)
                and team2_id in self.team_ids
            ):
                filtered.append(game)
                continue

            combined_names = " ".join(
                str(value) for value in [
                    game.get("ShortTeamNameAru", ""),
                    game.get("ShortTeamNameBru", ""),
                    game.get("TeamNameAru", ""),
                    game.get("TeamNameBru", ""),
                ]
            ).lower()

            for variant in self.team_name_variants:
                if variant and variant in combined_names:
                    filtered.append(game)
                    break
        return filtered

    async def get_games_for_comp(self, comp_id: int) -> List[Dict]:
        games = await self.get_calendar_for_comp(comp_id)
        if not games:
            return []
        return self.filter_games_by_config(games)

    async def get_all_games(self) -> Dict[str, List[Dict]]:
        """Fetches games for every configured competition."""
        all_games: Dict[str, List[Dict]] = {}
        if not self.comp_ids:
            print("ℹ️ В конфигурации не заданы ID соревнований.")
            return all_games

        for comp_id in self.comp_ids:
            print(f"\n🔍 Получение игр для соревнования {comp_id}...")
            games = await self.get_games_for_comp(comp_id)
            all_games[str(comp_id)] = games
            print(f"✅ Найдено {len(games)} игр для соревнования {comp_id}")
        return all_games

    def get_today_games(self, games: List[Dict]) -> List[Dict]:
        return [game for game in games if game.get("IsToday")]

    def get_upcoming_games(self, games: List[Dict], days_ahead: int = 7) -> List[Dict]:
        return [
            game for game in games
            if 0 <= game.get("DaysFromToday", 999) <= days_ahead
        ]

    def get_finished_games(self, games: List[Dict]) -> List[Dict]:
        return [game for game in games if game.get("GameStatus") == 1]

    def get_scheduled_games(self, games: List[Dict]) -> List[Dict]:
        return [game for game in games if game.get("GameStatus") == 0]

    def get_games_by_status(self, games: List[Dict]) -> Dict[str, List[Dict]]:
        return {
            "today": self.get_today_games(games),
            "upcoming": self.get_upcoming_games(games),
            "finished": self.get_finished_games(games),
            "scheduled": self.get_scheduled_games(games),
        }

    def format_game_notification(self, game: Dict, notification_type: str) -> str:
        team_a = game.get("ShortTeamNameAru", "")
        team_b = game.get("ShortTeamNameBru", "")
        date = game.get("GameDate", "")
        time = game.get("GameTimeMsk", "")
        venue = game.get("ArenaRu", "")
        comp_name = game.get("CompNameRu", "")
        score_a = game.get("ScoreA")
        score_b = game.get("ScoreB")

        if notification_type == "today":
            return f"🏀 ИГРА СЕГОДНЯ\n{team_a} vs {team_b}\n⏰ {time}\n📍 {venue}\n🏆 {comp_name}"
        if notification_type == "upcoming":
            days = game.get("DaysFromToday", 0)
            return f"🔮 ИГРА ЧЕРЕЗ {days} ДНЕЙ\n{team_a} vs {team_b}\n📅 {date} {time}\n📍 {venue}\n🏆 {comp_name}"
        if notification_type == "finished" and score_a is not None and score_b is not None:
            return f"✅ ИГРА ЗАВЕРШЕНА\n{team_a} vs {team_b}\n📊 {score_a} - {score_b}\n🏆 {comp_name}"
        if notification_type == "scheduled":
            return f"⏰ ЗАПЛАНИРОВАННАЯ ИГРА\n{team_a} vs {team_b}\n📅 {date} {time}\n📍 {venue}\n🏆 {comp_name}"
        return f"🏀 {team_a} vs {team_b} — {date} {time}"


async def main() -> None:
    notifications = InfobasketNotifications()
    all_games = await notifications.get_all_games()

    print(f"\n{'='*60}")
    print("АНАЛИЗ ИГР ПО СТАТУСАМ")
    print(f"{'='*60}")

    for comp_id, games in all_games.items():
        print(f"\n🎮 Соревнование {comp_id}: {len(games)} игр")
        if not games:
            print("  ❌ Игры не найдены")
            continue

        grouped = notifications.get_games_by_status(games)
        print(f"  📅 Игр сегодня: {len(grouped['today'])}")
        print(f"  🔮 Предстоящих (7 дней): {len(grouped['upcoming'])}")
        print(f"  ✅ Завершенных: {len(grouped['finished'])}")
        print(f"  ⏰ Запланированных: {len(grouped['scheduled'])}")

        if grouped["today"]:
            print("\n  📅 ИГРЫ СЕГОДНЯ:")
            for game in grouped["today"]:
                print("    " + notifications.format_game_notification(game, "today"))

        if grouped["upcoming"]:
            print("\n  🔮 ПРЕДСТОЯЩИЕ ИГРЫ:")
            for game in grouped["upcoming"][:3]:
                print("    " + notifications.format_game_notification(game, "upcoming"))

        if grouped["scheduled"]:
            print("\n  ⏰ ЗАПЛАНИРОВАННЫЕ ИГРЫ:")
            for game in grouped["scheduled"][:3]:
                print("    " + notifications.format_game_notification(game, "scheduled"))


if __name__ == "__main__":
    asyncio.run(main())

