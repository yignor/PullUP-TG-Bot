#!/usr/bin/env python3
"""
Перенос игроков из birthday_bot.py в Google Sheets
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Игроки из birthday_bot.py
BIRTHDAY_BOT_PLAYERS = [
    {"name": "Амбразас Никита",  "birthday": "2001-09-08"},
    # {"name": "Булатов Игорь",  "birthday": "2002-12-01"},  # Закомментирован
    {"name": "Валиев Равиль",  "birthday": "1998-05-21"},
    {"name": "Веселов Егор",  "birthday": "2006-12-25"},
    {"name": "Гайда Иван",     "birthday": "1984-03-28"},
    {"name": "Головченко Максим",  "birthday": "2002-06-29"},
    {"name": "Горбунов Никита",  "birthday": "2004-10-13"},
    {"name": "Гребнев Антон",  "birthday": "1990-12-24"},
    {"name": "Долгих Владислав",  "birthday": "2002-06-09"},
    {"name": "Долгих Денис",  "birthday": "1997-04-23"},
    {"name": "Дроздов Даниил",  "birthday": "1999-04-24"},
    {"name": "Дудкин Евгений",  "birthday": "2004-03-03"},
    {"name": "Звягинцев Олег",  "birthday": "1992-01-20"},
    {"name": "Касаткин Александр",     "birthday": "2006-04-19"},
    {"name": "Литус Дмитрий",  "birthday": "2005-08-04"},
    {"name": "Логинов Никита",  "birthday": "2007-10-24"},
    {"name": "Максимов Иван",  "birthday": "2001-07-24"},
    {"name": "Морецкий Игорь",  "birthday": "1986-04-30"},
    {"name": "Морозов Евгений",  "birthday": "2002-06-13"},
    {"name": "Мясников Юрий",  "birthday": "2003-05-28"},
    {"name": "Никитин Артем",  "birthday": "2000-06-30"},
    {"name": "Новиков Савва",  "birthday": "2007-01-14"},
    {"name": "Оболенский Григорий",  "birthday": "2004-11-06"},
    {"name": "Смирнов Александр",  "birthday": "2006-11-23"},
    {"name": "Сопп Эдуард",  "birthday": "2008-11-12"},
    {"name": "Федотов Дмитрий",  "birthday": "2003-09-04"},
    {"name": "Харитонов Эдуард",  "birthday": "2005-06-16"},
    {"name": "Чжан Тимофей",  "birthday": "2005-03-28"},
    {"name": "Шараев Юрий",  "birthday": "1987-09-20"},
    {"name": "Шахманов Максим",  "birthday": "2006-08-17"},
    {"name": "Ясинко Денис",  "birthday": "1987-06-18"},
    {"name": "Якупов Данил",  "birthday": "2005-06-02"},
    {"name": "Хан Александр",  "birthday": "1994-08-24"},
    # {"name": "НЕ ПИЗДАБОЛ МАКСИМ СЕРГЕЕВИЧ",  "birthday": "7777-77-77"}  # Закомментирован
]

def migrate_players():
    """Переносит игроков из birthday_bot.py в Google Sheets"""
    print("🔄 ПЕРЕНОС ИГРОКОВ ИЗ BIRTHDAY_BOT В GOOGLE SHEETS")
    print("=" * 60)
    
    try:
        from players_manager import PlayersManager
        
        # Создаем менеджер
        manager = PlayersManager()
        print("✅ PlayersManager инициализирован")
        
        # Получаем текущих игроков
        existing_players = manager.get_all_players()
        print(f"📊 Текущих игроков в таблице: {len(existing_players)}")
        
        # Создаем множество имен существующих игроков для проверки дубликатов
        existing_names = {player['name'] for player in existing_players}
        
        # Фильтруем игроков, которых еще нет в таблице
        new_players = []
        for player in BIRTHDAY_BOT_PLAYERS:
            if player['name'] not in existing_names:
                new_players.append(player)
            else:
                print(f"⚠️ Игрок {player['name']} уже существует в таблице")
        
        print(f"\n📝 Добавляем {len(new_players)} новых игроков...")
        
        # Добавляем новых игроков
        added_count = 0
        for i, player in enumerate(new_players, 1):
            success = manager.add_player(
                name=player['name'],
                birthday=player['birthday'],
                nickname='',  # Пока пустое
                telegram_id='',  # Пока пустое
                team='Pull Up',  # По умолчанию Pull Up
                notes='Перенесено из birthday_bot.py'
            )
            
            if success:
                print(f"   ✅ {i}. {player['name']} добавлен")
                added_count += 1
            else:
                print(f"   ❌ {i}. {player['name']} - ошибка добавления")
        
        # Проверяем результат
        print(f"\n📊 РЕЗУЛЬТАТ ПЕРЕНОСА:")
        print(f"   Всего игроков в birthday_bot: {len(BIRTHDAY_BOT_PLAYERS)}")
        print(f"   Уже было в таблице: {len(BIRTHDAY_BOT_PLAYERS) - len(new_players)}")
        print(f"   Добавлено новых: {added_count}")
        
        # Получаем обновленный список
        final_players = manager.get_all_players()
        print(f"   Всего игроков в таблице: {len(final_players)}")
        
        # Проверяем дни рождения сегодня
        birthday_players = manager.get_players_with_birthdays_today()
        print(f"\n🎂 Дней рождения сегодня: {len(birthday_players)}")
        
        if birthday_players:
            print("🎉 Именинники:")
            for player in birthday_players:
                age = player.get('age', 0)
                print(f"   - {player['name']} ({age} лет)")
        
        # Показываем статистику по командам
        teams = {}
        for player in final_players:
            team = player.get('team', 'Не указана')
            teams[team] = teams.get(team, 0) + 1
        
        print(f"\n📋 СТАТИСТИКА ПО КОМАНДАМ:")
        for team, count in teams.items():
            print(f"   {team}: {count} игроков")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка переноса: {e}")
        return False

def show_migration_summary():
    """Показывает сводку по миграции"""
    print("\n📋 СВОДКА ПО МИГРАЦИИ")
    print("=" * 60)
    print("✅ Игроки успешно перенесены из birthday_bot.py в Google Sheets")
    print()
    print("🔧 Что было сделано:")
    print("   - Извлечены все игроки из birthday_bot.py")
    print("   - Проверены дубликаты в Google Sheets")
    print("   - Добавлены только новые игроки")
    print("   - Установлены значения по умолчанию:")
    print("     * team: 'Pull Up'")
    print("     * status: 'Активный'")
    print("     * notes: 'Перенесено из birthday_bot.py'")
    print()
    print("📝 Что можно сделать дальше:")
    print("   - Добавить nicknames (@username)")
    print("   - Добавить telegram_id")
    print("   - Уточнить команды игроков")
    print("   - Обновить статусы (активный/неактивный)")
    print()
    print("🎯 Теперь можно использовать Google Sheets для управления игроками!")

if __name__ == "__main__":
    # Выполняем миграцию
    success = migrate_players()
    
    if success:
        show_migration_summary()
    else:
        print("\n❌ Ошибка при переносе игроков")
