#!/usr/bin/env python3
"""
Скрипт для миграции данных игроков из кода в Google Sheets
"""

from players_manager import players_manager

# Существующие данные игроков из birthday_bot.py
EXISTING_PLAYERS = [
    {"name": "Шахманов Максим", "birthday": "2006-08-17", "team": "Pull Up"},
    # Добавьте других игроков здесь
]

def migrate_players():
    """Мигрирует существующих игроков в Google Sheets"""
    print("🔄 МИГРАЦИЯ ИГРОКОВ В GOOGLE SHEETS")
    print("=" * 50)
    
    # Проверяем подключение
    if not players_manager.players_sheet:
        print("❌ Google Sheets не подключен")
        print("   Убедитесь, что настроены GOOGLE_SHEETS_CREDENTIALS и SPREADSHEET_ID")
        return
    
    print("✅ Google Sheets подключен")
    
    # Получаем существующих игроков из таблицы
    existing_in_sheets = players_manager.get_all_players()
    existing_names = [p['name'] for p in existing_in_sheets]
    
    print(f"📊 Игроков в таблице: {len(existing_in_sheets)}")
    
    # Мигрируем игроков
    migrated_count = 0
    for player in EXISTING_PLAYERS:
        name = player['name']
        
        if name in existing_names:
            print(f"⏭️  Игрок {name} уже существует в таблице")
            continue
        
        # Добавляем игрока
        success = players_manager.add_player(
            name=name,
            birthday=player['birthday'],
            team=player.get('team', ''),
            notes="Мигрирован из кода"
        )
        
        if success:
            migrated_count += 1
            print(f"✅ Игрок {name} добавлен")
        else:
            print(f"❌ Ошибка добавления игрока {name}")
    
    print(f"\n📈 МИГРАЦИЯ ЗАВЕРШЕНА")
    print(f"   Добавлено игроков: {migrated_count}")
    print(f"   Всего в таблице: {len(players_manager.get_all_players())}")
    
    # Показываем всех игроков
    print(f"\n📋 СПИСОК ВСЕХ ИГРОКОВ:")
    all_players = players_manager.get_all_players()
    for i, player in enumerate(all_players, 1):
        print(f"   {i}. {player['name']} - {player['birthday']} - {player.get('team', '')}")

if __name__ == "__main__":
    migrate_players()
