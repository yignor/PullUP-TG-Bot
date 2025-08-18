#!/usr/bin/env python3
"""
Исправление структуры имен в Google Sheets
Работает с текущей структурой таблицы
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def fix_names_structure():
    """Исправляет структуру имен в Google Sheets"""
    print("🔄 ИСПРАВЛЕНИЕ СТРУКТУРЫ ИМЕН В GOOGLE SHEETS")
    print("=" * 60)
    
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        import json
        
        # Подключаемся к Google Sheets
        creds_dict = json.loads(os.getenv("GOOGLE_SHEETS_CREDENTIALS"))
        creds = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        gc = gspread.authorize(creds)
        
        spreadsheet = gc.open_by_key(os.getenv("SPREADSHEET_ID"))
        players_sheet = spreadsheet.worksheet("Игроки")
        
        print("✅ Подключение к Google Sheets успешно")
        
        # Получаем все данные
        all_data = players_sheet.get_all_values()
        print(f"📊 Всего строк в таблице: {len(all_data)}")
        
        if len(all_data) < 2:
            print("❌ Недостаточно данных в таблице")
            return False
        
        # Показываем заголовки
        headers = all_data[0]
        print(f"\n📋 ЗАГОЛОВКИ ТАБЛИЦЫ:")
        for i, header in enumerate(headers):
            print(f"   {i+1}. {header}")
        
        # Находим индексы столбцов
        name_col_idx = None
        surname_col_idx = None
        
        for i, header in enumerate(headers):
            if 'имя' in header.lower():
                name_col_idx = i
            elif 'фамилия' in header.lower():
                surname_col_idx = i
        
        print(f"\n🔍 НАЙДЕННЫЕ СТОЛБЦЫ:")
        print(f"   ИМЯ: столбец {name_col_idx + 1 if name_col_idx is not None else 'не найден'}")
        print(f"   ФАМИЛИЯ: столбец {surname_col_idx + 1 if surname_col_idx is not None else 'не найден'}")
        
        if name_col_idx is None:
            print("❌ Столбец 'ИМЯ' не найден")
            return False
        
        # Показываем первые несколько строк
        print(f"\n📋 ПЕРВЫЕ 5 СТРОК (текущее состояние):")
        for i, row in enumerate(all_data[1:6], 1):
            name = row[name_col_idx] if name_col_idx < len(row) else ''
            surname = row[surname_col_idx] if surname_col_idx is not None and surname_col_idx < len(row) else ''
            print(f"   {i}. ИМЯ: '{name}' | ФАМИЛИЯ: '{surname}'")
        
        # Обрабатываем строки
        print(f"\n📝 ОБРАБОТКА СТРОК:")
        updated_count = 0
        
        for row_idx, row in enumerate(all_data[1:], 2):  # Начинаем со 2-й строки (после заголовков)
            if len(row) <= name_col_idx:
                continue
                
            current_name = row[name_col_idx]
            
            # Пропускаем пустые имена
            if not current_name or current_name.strip() == '':
                continue
            
            # Проверяем, нужно ли разделять
            if ' ' in current_name:
                # Разделяем по первому пробелу
                parts = current_name.split(' ', 1)
                surname_part = parts[0].strip()
                first_name_part = parts[1].strip()
                
                print(f"   Строка {row_idx}: '{current_name}' → Фамилия: '{surname_part}', Имя: '{first_name_part}'")
                
                # Обновляем имя (убираем фамилию)
                players_sheet.update_cell(row_idx, name_col_idx + 1, first_name_part)
                
                # Если есть столбец фамилии, заполняем его
                if surname_col_idx is not None:
                    # Убеждаемся, что строка достаточно длинная
                    while len(row) <= surname_col_idx:
                        row.append('')
                    
                    players_sheet.update_cell(row_idx, surname_col_idx + 1, surname_part)
                
                updated_count += 1
            else:
                print(f"   Строка {row_idx}: '{current_name}' → Нельзя разделить (нет пробела)")
        
        # Показываем результат
        print(f"\n📊 РЕЗУЛЬТАТ ОБРАБОТКИ:")
        print(f"   Обработано строк: {updated_count}")
        
        # Показываем обновленные данные
        updated_data = players_sheet.get_all_values()
        print(f"\n📋 ПЕРВЫЕ 5 СТРОК (после обновления):")
        for i, row in enumerate(updated_data[1:6], 1):
            name = row[name_col_idx] if name_col_idx < len(row) else ''
            surname = row[surname_col_idx] if surname_col_idx is not None and surname_col_idx < len(row) else ''
            print(f"   {i}. ИМЯ: '{name}' | ФАМИЛИЯ: '{surname}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")
        return False

def show_instructions():
    """Показывает инструкции по структуре таблицы"""
    print("\n📋 ИНСТРУКЦИИ ПО СТРУКТУРЕ ТАБЛИЦЫ")
    print("=" * 60)
    print("Ожидаемая структура столбцов:")
    print("   A. ИМЯ (только имя, без фамилии)")
    print("   B. ФАМИЛИЯ (только фамилия)")
    print("   C. Ник")
    print("   D. Telegram ID")
    print("   E. Дата рождения")
    print("   F. Статус")
    print("   G. Команда")
    print("   H. Дата добавления")
    print("   I. Примечания")
    print()
    print("🔧 Логика обработки:")
    print("   - Находит столбцы 'ИМЯ' и 'ФАМИЛИЯ'")
    print("   - Разделяет полные имена по первому пробелу")
    print("   - Первое слово → ФАМИЛИЯ")
    print("   - Остальные слова → ИМЯ")
    print("   - Пример: 'Шахманов Максим' → Фамилия: 'Шахманов', Имя: 'Максим'")

if __name__ == "__main__":
    # Показываем инструкции
    show_instructions()
    
    # Выполняем исправление
    success = fix_names_structure()
    
    if success:
        print("\n🎉 Структура имен исправлена!")
        print("Теперь имена и фамилии разделены правильно")
    else:
        print("\n❌ Ошибка при исправлении структуры имен")
