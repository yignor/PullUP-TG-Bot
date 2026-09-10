#!/usr/bin/env python3
"""Группа, привязанная к лиге, решает, как в этой лиге платят её люди.

    python3 tests/test_group_league_pay.py

За игру — её сумма вместо цены из карточки, за лигу целиком — один взнос и
ни копейки с каждой игры. Своя сумма у человека не съезжает за общей. Люди вне
группы и другие лиги живут по-старому.
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

TMP = Path(tempfile.mkdtemp(prefix="glp-test-")) / "bot.db"
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
    now = sheets_cache.now_iso()
    with sheets_cache.get_connection() as conn:
        for row, sur in ((2, "Первый"), (3, "Второй"), (4, "Чужой")):
            conn.execute(
                "INSERT INTO players (row_index, surname, name, pay_game, "
                "pay_season, synced_at) VALUES (?, ?, 'Игрок', 900, 5500, ?)",
                (row, sur, now))
        conn.execute(
            "INSERT INTO league_teams (source, team_id, name, league, ours, "
            "fetched_at) VALUES ('slpro','707','Farm','Кубок',1,?)", (now,))
        conn.commit()
    import player_groups as pg
    gid, _ = pg.create("Второй состав")
    pg.bind(gid, "slpro", "707")
    pg.add(gid, 2)
    pg.add(gid, 3)
    return gid


def run() -> None:
    gid = setup()
    import game_roster
    import player_groups as pg
    import season_fees

    print("\n=== без правил — как раньше ===")
    check(pg.game_price_for(2, "slpro") is None, "группа ничего не решала — правила нет")
    check(game_roster.price_for(2, "slpro") == 900, "цена из карточки игрока")

    print("\n=== за игру ===")
    pg.set_payment(gid, pg.PAY_GAME, 600)
    check(game_roster.price_for(2, "slpro") == 600, "в лиге группы — сумма группы")
    check(game_roster.price_for(2, "infobasket") == 900,
          "в другой лиге — своя цена, группа её не касается")
    check(game_roster.price_for(4, "slpro") == 900,
          "человек вне группы платит по карточке")

    pg.set_member_amount(gid, 3, 400)
    check(game_roster.price_for(3, "slpro") == 400, "своя сумма у человека")
    pg.set_payment(gid, pg.PAY_GAME, 700)
    check(game_roster.price_for(3, "slpro") == 400,
          "общую поменяли — своя не съехала")
    check(game_roster.price_for(2, "slpro") == 700, "а остальных подвинуло")
    pg.set_member_amount(gid, 3, 0)
    check(game_roster.price_for(3, "slpro") == 700, "ноль возвращает общую")

    print("\n=== за лигу целиком ===")
    pg.set_payment(gid, pg.PAY_LEAGUE, 7000)
    check(game_roster.price_for(2, "slpro") == 0,
          "с каждой игры этой лиги больше не берём")
    check(game_roster.price_for(2, "infobasket") == 900,
          "а в другой лиге — по-прежнему за игру")

    fee_id = season_fees.fee_for_group(gid)
    check(season_fees.fee_for_group(gid) == fee_id, "сбор у группы один, не плодится")
    rows = season_fees.status(fee_id)
    check(sorted(int(r["row"]) for r in rows) == [2, 3], "состав сбора — это группа")
    check(all(r["need"] == 7000 for r in rows), "по 7000 с каждого")

    pg.set_member_amount(gid, 2, 5000)
    rows = {int(r["row"]): r for r in season_fees.status(fee_id)}
    check(rows[2]["need"] == 5000 and rows[3]["need"] == 7000,
          "своя сумма работает и для взноса за лигу")

    pg.add(gid, 4)
    check(4 in {int(r["row"]) for r in season_fees.status(fee_id)},
          "добавил в группу — появился и в сборе, отдельно вести не надо")
    season_fees.toggle(fee_id, 4)
    check(4 not in pg.member_rows(gid),
          "правка состава из сбора ушла в группу, а не в пустоту")

    print("\n=== снять правило ===")
    pg.set_payment(gid, "")
    check(game_roster.price_for(2, "slpro") == 900, "группа не решает — снова по карточке")


def test_fantasy_pool() -> None:
    """Пока состав не объявлен, пул на игру — группа этой лиги.

    Ориентир всё равно состав: он главный. Но до него предлагать ставить на
    всю команду значит предлагать людей, которые на эту игру не выйдут."""
    print("\n=== пул фэнтези на игру ===")
    import fantasy_api
    pool = [{"name": "Первый Игрок", "ref": "slpro:707:1"},
            {"name": "Второй Игрок", "ref": "slpro:707:2"},
            {"name": "Чужой Игрок", "ref": "slpro:707:4"}]
    fantasy_api._declared_names = lambda source, game_id: []

    got = asyncio.run(fantasy_api.game_pool("slpro", "g1", pool=pool))
    names = sorted(e["name"] for e in got)
    check(names == ["Второй Игрок", "Первый Игрок"],
          f"без состава — только группа лиги: {names}")

    other = asyncio.run(fantasy_api.game_pool("infobasket", "g2", pool=pool))
    check(len(other) == 3, "в лиге без группы — вся команда, как раньше")

    # Объявленный состав главнее группы.
    fantasy_api._declared_names = lambda source, game_id: [
        {"title": "Чужой Игрок", "row": 4}]
    declared = asyncio.run(fantasy_api.game_pool("slpro", "g1", pool=pool))
    check([e["name"] for e in declared] == ["Чужой Игрок"],
          "состав объявлен — берём его, а не группу")


def main() -> int:
    print(f"База: {TMP}")
    run()
    test_fantasy_pool()
    print("\n" + "=" * 60)
    if bad:
        print(f"НЕ ПРОШЛО ({len(bad)}):")
        for b in bad:
            print("  • " + b)
        return 1
    print("ОПЛАТА ГРУППЫ В ЛИГЕ: ВСЁ ЗЕЛЁНОЕ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
