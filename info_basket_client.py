#!/usr/bin/env python3
"""
Клиент для API Infobasket (asb/reg/org.infobasket.su)
Позволяет получать расписание/матчи по competition-id или competition-tag
и извлекать игры с участием целевых команд.
"""

import os
import asyncio
from typing import Any, Dict, List, Optional

import aiohttp
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

INFOBASKET_API_BASE = os.getenv("INFOBASKET_API_BASE", "https://asb.infobasket.su").rstrip("/")
INFOBASKET_COMPETITION_ID = os.getenv("INFOBASKET_COMPETITION_ID")
INFOBASKET_COMPETITION_TAG = os.getenv("INFOBASKET_COMPETITION_TAG")


class InfoBasketClient:
    """Легкий клиент для работы с Infobasket Widget/Comp API."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or INFOBASKET_API_BASE).rstrip("/")

    async def _get_json(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.json(content_type=None)
                    return None
        except Exception as e:
            print(f"⚠️ Ошибка запросa {url}: {e}")
            return None

    async def get_issue_by_id(self, issue_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/Widget/CompIssue/{issue_id}?format=json"
        return await self._get_json(url)

    async def get_latest_issue_by_tag(self, tag: str) -> Optional[str]:
        url = f"{self.base_url.replace('asb.', 'org.').replace('reg.', 'org.')}/Comp/GetSeasonsForTag?tag={tag}"
        data = await self._get_json(url)
        # Формат ответа может отличаться; пытаемся найти последний issueId
        if not data:
            return None
        # Ищем поля, похожие на сезоны/выпуски с id
        candidates: List[str] = []
        def walk(obj: Any) -> None:
            if isinstance(obj, dict):
                if "issueId" in obj and isinstance(obj["issueId"], (str, int)):
                    candidates.append(str(obj["issueId"]))
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)
        walk(data)
        if candidates:
            # Берем последний по списку
            return candidates[-1]
        return None

    @staticmethod
    def _collect_games_from_issue(issue_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        games: List[Dict[str, Any]] = []

        def walk(obj: Any) -> None:
            if isinstance(obj, dict):
                # Находим структуры, похожие на матч
                if any(k in obj for k in ("GameID", "GameId", "gameId")) and (
                    "Team1" in obj or "TeamA" in obj or "Team1Name" in obj or "TeamAName" in obj
                ):
                    games.append(obj)
                # Также ищем в полях Games, Matches, Schedule
                for key in ["Games", "Matches", "Schedule", "Calendar"]:
                    if key in obj and isinstance(obj[key], list):
                        for item in obj[key]:
                            if isinstance(item, dict) and any(k in item for k in ("GameID", "GameId", "gameId")):
                                games.append(item)
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)

        walk(issue_json)
        return games

    @staticmethod
    def _normalize_game(obj: Dict[str, Any]) -> Dict[str, Any]:
        # Пробуем унифицировать поля
        game_id = obj.get("GameID") or obj.get("GameId") or obj.get("gameId")
        team1 = obj.get("Team1Name") or obj.get("TeamAName") or obj.get("Team1") or obj.get("TeamA") or ""
        team2 = obj.get("Team2Name") or obj.get("TeamBName") or obj.get("Team2") or obj.get("TeamB") or ""
        date = obj.get("GameDate") or obj.get("Date") or obj.get("date") or ""
        time = obj.get("GameTime") or obj.get("Time") or obj.get("time") or ""
        venue = obj.get("GymName") or obj.get("Place") or obj.get("Gym") or obj.get("venue") or ""
        status = obj.get("State") or obj.get("Status") or obj.get("state") or ""

        return {
            "game_id": str(game_id) if game_id is not None else "",
            "team1": str(team1).strip(),
            "team2": str(team2).strip(),
            "date": str(date).strip(),
            "time": str(time).strip(),
            "venue": str(venue).strip(),
            "status": str(status).strip(),
        }

    async def get_schedule(self, issue_id: Optional[str] = None) -> List[Dict[str, Any]]:
        # Определяем issue_id
        iid = issue_id or INFOBASKET_COMPETITION_ID
        if not iid and INFOBASKET_COMPETITION_TAG:
            iid = await self.get_latest_issue_by_tag(INFOBASKET_COMPETITION_TAG)
        if not iid:
            print("⚠️ Не удалось определить issue_id для расписания Infobasket")
            return []

        print(f"🔍 Запрашиваем данные для issue_id: {iid}")
        data = await self.get_issue_by_id(str(iid))
        if not data:
            print("❌ API не вернул данные")
            return []

        print(f"📊 Получены данные, ключи: {list(data.keys())}")
        
        # Ищем активные соревнования и запрашиваем их данные
        all_games = []
        if "Comps" in data:
            for comp in data["Comps"]:
                comp_id = comp.get("CompID")
                if comp_id:
                    print(f"🔍 Запрашиваем данные для CompID: {comp_id}")
                    comp_data = await self.get_issue_by_id(str(comp_id))
                    if comp_data:
                        comp_games = self._collect_games_from_issue(comp_data)
                        all_games.extend(comp_games)
                        print(f"🎮 Найдено игр в CompID {comp_id}: {len(comp_games)}")
        
        print(f"🎮 Всего найдено сырых игр: {len(all_games)}")
        
        if all_games:
            print(f"📝 Первая игра: {all_games[0]}")
        
        normalized = [self._normalize_game(g) for g in all_games]
        # Убираем дубликаты по game_id
        seen = set()
        deduped: List[Dict[str, Any]] = []
        for g in normalized:
            if g["game_id"] and g["game_id"] not in seen:
                seen.add(g["game_id"])
                deduped.append(g)
        return deduped


# Быстрый тест
if __name__ == "__main__":
    async def _main():
        client = InfoBasketClient()
        games = await client.get_schedule()
        print(f"📊 Найдено игр: {len(games)}")
        for g in games[:5]:
            print(f" - {g['date']} {g['time']}: {g['team1']} vs {g['team2']} @ {g['venue']} (id={g['game_id']})")
    asyncio.run(_main())


