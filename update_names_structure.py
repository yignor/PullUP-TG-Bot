#!/usr/bin/env python3
"""
Обновление структуры имен в Google Sheets
Разделение столбца "ИМЯ" на "ФАМИЛИЯ" и "ИМЯ"
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def update_names_structure():
    """Обновляет структуру имен в Google Sheets"""
    print("🔄 ОБНОВЛЕНИЕ СТРУКТУРЫ ИМЕН В GOOGLE SHEETS")
    print("=" * 60)
    
    try:
        from players_manager import PlayersManager
        
        # Создаем менеджер
        manager = PlayersManager()
        print("✅ PlayersManager инициализирован")
        
        # Получаем всех игроков
        all_players = manager.get_all_players()
        print(f"📊 Всего игроков в таблице: {len(all_players)}")
        
        # Показываем первые несколько игроков для анализа
        print(f"\n📋 ПЕРВЫЕ 5 ИГРОКОВ (текущая структура):")
        for i, player in enumerate(all_players[:5], 1):
            name = player.get('name', '')
            surname = player.get('surname', '')  # Новый столбец
            print(f"   {i}. ИМЯ: '{name}' | ФАМИЛИЯ: '{surname}'")
        
        # Анализируем структуру имен
        print(f"\n🔍 АНАЛИЗ СТРУКТУРЫ ИМЕН:")
        names_to_split = []
        already_split = []
        
        for player in all_players:
            name = player.get('name', '')
            surname = player.get('surname', '')
            
            if surname:  # Если фамилия уже заполнена
                already_split.append(player)
                print(f"   ✅ {name} - уже разделено")
            else:  # Если нужно разделить
                names_to_split.append(player)
                print(f"   🔄 {name} - нужно разделить")
        
        print(f"\n📊 СТАТИСТИКА:")
        print(f"   Уже разделено: {len(already_split)}")
        print(f"   Нужно разделить: {len(names_to_split)}")
        
        if not names_to_split:
            print("✅ Все имена уже разделены!")
            return True
        
        # Разделяем имена
        print(f"\n📝 РАЗДЕЛЯЕМ ИМЕНА:")
        updated_count = 0
        
        for i, player in enumerate(names_to_split, 1):
            full_name = player.get('name', '')
            
            if ' ' in full_name:
                # Разделяем по первому пробелу
                parts = full_name.split(' ', 1)
                surname = parts[0].strip()
                first_name = parts[1].strip()
                
                print(f"   {i}. '{full_name}' → Фамилия: '{surname}', Имя: '{first_name}'")
                
                # Обновляем данные игрока
                success = manager.update_player_name(
                    player_id=player.get('id'),  # Нужен ID для обновления
                    new_name=first_name,
                    new_surname=surname
                )
                
                if success:
                    print(f"      ✅ Обновлено")
                    updated_count += 1
                else:
                    print(f"      ❌ Ошибка обновления")
            else:
                print(f"   {i}. '{full_name}' → Нельзя разделить (нет пробела)")
        
        # Проверяем результат
        print(f"\n📊 РЕЗУЛЬТАТ ОБНОВЛЕНИЯ:")
        print(f"   Обработано: {len(names_to_split)}")
        print(f"   Обновлено: {updated_count}")
        
        # Показываем обновленную структуру
        updated_players = manager.get_all_players()
        print(f"\n📋 ПЕРВЫЕ 5 ИГРОКОВ (после обновления):")
        for i, player in enumerate(updated_players[:5], 1):
            name = player.get('name', '')
            surname = player.get('surname', '')
            print(f"   {i}. ИМЯ: '{name}' | ФАМИЛИЯ: '{surname}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обновления: {e}")
        return False

def show_table_structure():
    """Показывает структуру таблицы"""
    print("\n📋 СТРУКТУРА ТАБЛИЦЫ")
    print("=" * 60)
    print("Текущие столбцы:")
    print("   - name (ИМЯ)")
    print("   - surname (ФАМИЛИЯ) - новый столбец")
    print("   - nickname")
    print("   - telegram_id")
    print("   - birthday")
    print("   - status")
    print("   - team")
    print("   - added_date")
    print("   - notes")
    print()
    print("🔧 Логика разделения:")
    print("   - Первое слово → ФАМИЛИЯ")
    print("   - Остальные слова → ИМЯ")
    print("   - Пример: 'Шахманов Максим' → Фамилия: 'Шахманов', Имя: 'Максим'")

if __name__ == "__main__":
    # Показываем структуру таблицы
    show_table_structure()
    
    # Выполняем обновление
    success = update_names_structure()
    
    if success:
        print("\n🎉 Обновление структуры имен завершено!")
    else:
        print("\n❌ Ошибка при обновлении структуры имен")
