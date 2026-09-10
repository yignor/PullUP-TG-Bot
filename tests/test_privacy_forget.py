#!/usr/bin/env python3
"""«Забыть меня»: что уходит, что обезличивается, что остаётся.

    python3 tests/test_privacy_forget.py

Главное, за чем следим: своё удаляется, чужие таблицы не ломаются (история
фэнтези и голоса остаются, но без id), чужое не трогается вовсе (платежи,
лист команды). И в журнал не попадает сам id.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fake_tg import FakeBot, FakeContext, FakeQuery, FakeUpdate, FakeUser, buttons_of

TMP = Path(tempfile.mkdtemp(prefix="forget-test-")) / "bot.db"
ME = FakeUser(uid=930100, username="leaving")
OTHER = "930200"
BOT = FakeBot()
bad: List[str] = []


def check(cond: bool, what: str) -> None:
    print(("  ✅ " if cond else "  ❌ ") + what)
    if not cond:
        bad.append(what)


def setup() -> Any:
    os.environ.setdefault("BOT_TOKEN", "0:test")
    os.environ["ADMIN_USER_IDS"] = "1"
    os.environ.setdefault("DAEMON_LOG_PATH", str(ROOT / "tests" / "test.log"))
    os.environ["GOOGLE_SHEETS_CREDENTIALS"] = ""
    os.environ["SPREADSHEET_ID"] = ""
    import sheets_cache
    sheets_cache.DB_PATH = TMP
    sheets_cache.init_db()
    import achievements
    achievements.init()
    now = sheets_cache.now_iso()
    uid = str(ME.id)
    with sheets_cache.get_connection() as conn:
        conn.execute("INSERT INTO players (row_index, surname, name, tg_user_id, "
                     "synced_at) VALUES (5, 'Уходящий', 'Игрок', ?, ?)", (uid, now))
        conn.execute("INSERT INTO player_links (tg_user_id, username, player_row, "
                     "linked_at) VALUES (?, 'leaving', 5, ?)", (uid, now))
        conn.execute("INSERT INTO player_identities (tg_user_id, source, player_id, "
                     "linked_at) VALUES (?, 'slpro', '77', ?)", (uid, now))
        conn.execute("INSERT INTO bot_users (telegram_id, username, first_name, "
                     "first_seen_at) VALUES (?, 'leaving', 'Игрок', ?)", (uid, now))
        # Голоса: мой и чужой.
        for who in (uid, OTHER):
            conn.execute(
                "INSERT INTO game_votes (tg_poll_id, user_id, username, first_name, "
                "last_name, vote_text, vote_type, game_id, game_date, updated_at, "
                "synced_at) VALUES ('p1', ?, 'nick', 'Имя', 'Фам', '✅', "
                "'PRESENT', 'g1', '2026-09-01', ?, ?)", (who, now, now))
        # Фэнтези: мои очки и чужие.
        for who, pts in ((uid, 50), (OTHER, 40)):
            conn.execute(
                "INSERT INTO fantasy_game_scores (user_id, season_id, source, "
                "game_id, game_date, points, mode, refs_json, computed_at) VALUES "
                "(?, 1, 'slpro', 'g1', '2026-09-01', ?, 'free', '[]', ?)",
                (who, pts, now))
        # Платёж — учёт тренера, трогать нельзя.
        conn.execute(
            "INSERT INTO payments (player_row, amount, kind, games, paid_at, "
            "created_at, fingerprint) VALUES (5, 900, 'game', 1, '2026-09-01', ?, 'fp1')",
            (now,))
        conn.commit()
    ach_id, _ = achievements.create("Значок")
    achievements.award(ach_id, uid)
    import bot_daemon as bd
    bd._get_spreadsheet = lambda: None
    return bd


def rows(table: str, col: str, value: str) -> int:
    import sheets_cache
    with sheets_cache.get_connection() as conn:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} = ?",
                                (value,)).fetchone()[0])


async def press(bd, data: str):
    q = FakeQuery(data, ME, BOT)
    await bd.handle_menu_callback(FakeUpdate(query=q, user=ME), FakeContext(BOT))
    last = (q.screens or [{"text": "", "markup": None}])[-1]
    return last["text"], last["markup"]


async def run() -> None:
    bd = setup()
    import privacy
    uid = str(ME.id)

    print("\n=== где почитать ===")
    text, markup = await press(bd, "menu:main")
    cbs = [b.callback_data for b in buttons_of(markup)]
    check("menu:privacy" in cbs, "в меню есть «Мои данные»")
    text, markup = await press(bd, "menu:privacy")
    check("хранит бот" in text, "текст о данных открывается")
    check("menu:forget" in [b.callback_data for b in buttons_of(markup)],
          "и под ним кнопка «Забыть меня»")

    print("\n=== сначала спрашиваем ===")
    text, markup = await press(bd, "menu:forget")
    check("Удалю совсем" in text and "без имени" in text,
          "показано, что уйдёт и что обезличим")
    check("платежи" in text and "тренер" in text, "и что не трогаем")
    check(rows("player_links", "tg_user_id", uid) == 1,
          "пока не подтвердил — ничего не удалено")

    print("\n=== забываем ===")
    logs: List[str] = []

    class Catch(logging.Handler):
        def emit(self, record):
            logs.append(record.getMessage())

    catcher = Catch()
    logging.getLogger("privacy").addHandler(catcher)
    text, _ = await press(bd, "menu:forget2")
    logging.getLogger("privacy").removeHandler(catcher)
    check("Готово" in text, f"человеку отчитались: {text.splitlines()[0]}")

    for table, col in (("player_links", "tg_user_id"),
                       ("player_identities", "tg_user_id"),
                       ("bot_users", "telegram_id"),
                       ("achievement_awards", "user_id")):
        check(rows(table, col, uid) == 0, f"удалено: {table}")

    check(rows("game_votes", "user_id", uid) == 0, "в голосах моего id больше нет")
    check(rows("game_votes", "user_id", OTHER) == 1, "чужой голос на месте")
    import sheets_cache
    with sheets_cache.get_connection() as conn:
        masked = conn.execute(
            "SELECT user_id, username, first_name FROM game_votes "
            "WHERE user_id LIKE 'forgotten-%'").fetchall()
        score = conn.execute(
            "SELECT points FROM fantasy_game_scores WHERE user_id LIKE 'forgotten-%'"
        ).fetchall()
    check(len(masked) == 1 and not masked[0]["username"] and not masked[0]["first_name"],
          "мой голос остался строкой, но без имени и ника")
    check(len(score) == 1 and int(score[0]["points"]) == 50,
          "очки фэнтези остались — зачёт у остальных не поехал")
    check(rows("fantasy_game_scores", "user_id", OTHER) == 1, "чужие очки не тронуты")

    check(rows("payments", "player_row", "5") == 1, "платёж тренера не тронут")
    check(rows("players", "row_index", "5") == 1, "строка в списке команды на месте")

    check(logs and all(uid not in m for m in logs),
          f"в журнал id не попал: {logs}")

    print("\n=== повторно ===")
    again = privacy.forget(uid)
    check(again == {"deleted": 0, "masked": 0}, f"второй раз стирать нечего: {again}")


def main() -> int:
    print(f"База: {TMP}")
    asyncio.run(run())
    print("\n" + "=" * 60)
    if bad:
        print(f"НЕ ПРОШЛО ({len(bad)}):")
        for b in bad:
            print("  • " + b)
        return 1
    print("ЗАБЫТЬ МЕНЯ: ВСЁ ЗЕЛЁНОЕ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
