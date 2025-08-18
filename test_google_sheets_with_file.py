#!/usr/bin/env python3
"""
Тест Google Sheets с credentials из JSON файла
"""

import os
import json
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_google_sheets_with_file():
    """Тестирует Google Sheets с credentials из файла"""
    print("🧪 ТЕСТ GOOGLE SHEETS С JSON ФАЙЛОМ")
    print("=" * 50)
    
    # Получаем Spreadsheet ID
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    print(f"📊 Spreadsheet ID: {spreadsheet_id}")
    
    # Читаем credentials из JSON файла
    credentials_file = "google_credentials.json"
    if not os.path.exists(credentials_file):
        print(f"❌ Файл {credentials_file} не найден")
        return False
    
    try:
        with open(credentials_file, 'r', encoding='utf-8') as f:
            credentials = json.load(f)
        
        print(f"✅ JSON файл прочитан")
        print(f"   Project ID: {credentials.get('project_id')}")
        print(f"   Client Email: {credentials.get('client_email')}")
        
        # Пытаемся подключиться к Google Sheets
        import gspread
        from google.oauth2.service_account import Credentials
        
        # Создаем credentials объект
        creds = Credentials.from_service_account_info(
            credentials,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        # Подключаемся к Google Sheets
        client = gspread.authorize(creds)
        
        # Пытаемся открыть таблицу
        spreadsheet = client.open_by_key(spreadsheet_id)
        print(f"✅ Подключение к Google Sheets успешно!")
        print(f"   Название таблицы: {spreadsheet.title}")
        
        # Показываем листы
        worksheets = spreadsheet.worksheets()
        print(f"   Количество листов: {len(worksheets)}")
        for i, worksheet in enumerate(worksheets, 1):
            print(f"   {i}. {worksheet.title}")
        
        # Пытаемся прочитать данные из первого листа
        if worksheets:
            first_sheet = worksheets[0]
            print(f"\n📊 Тестируем чтение данных из листа '{first_sheet.title}':")
            
            # Получаем все значения
            all_values = first_sheet.get_all_values()
            print(f"   Строк в таблице: {len(all_values)}")
            
            if all_values:
                print(f"   Колонок в первой строке: {len(all_values[0])}")
                print(f"   Заголовки: {all_values[0][:5]}...")  # Показываем первые 5 колонок
                
                # Показываем первые несколько строк
                print(f"\n📋 Первые 3 строки данных:")
                for i, row in enumerate(all_values[:3], 1):
                    print(f"   {i}. {row[:5]}...")  # Показываем первые 5 колонок
            else:
                print("   Таблица пуста")
        
        return True
        
    except ImportError:
        print("❌ Библиотеки не установлены!")
        print("   Установите: pip install gspread google-auth")
        return False
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_players_manager_with_file():
    """Тестирует players_manager с credentials из файла"""
    print("\n🧪 ТЕСТ PLAYERS MANAGER С JSON ФАЙЛОМ")
    print("=" * 50)
    
    try:
        # Временно устанавливаем переменную окружения
        os.environ['GOOGLE_SHEETS_CREDENTIALS_FILE'] = 'google_credentials.json'
        
        # Импортируем и тестируем players_manager
        from players_manager import PlayersManager
        
        manager = PlayersManager()
        print("✅ PlayersManager инициализирован")
        
        # Получаем всех игроков
        all_players = manager.get_all_players()
        print(f"📊 Всего игроков: {len(all_players)}")
        
        # Получаем активных игроков
        active_players = manager.get_active_players()
        print(f"✅ Активных игроков: {len(active_players)}")
        
        # Проверяем дни рождения сегодня
        birthday_players = manager.get_players_with_birthdays_today()
        print(f"🎂 Дней рождения сегодня: {len(birthday_players)}")
        
        if birthday_players:
            print("🎉 Именинники:")
            for player in birthday_players:
                age = player.get('age', 0)
                print(f"   - {player['name']} ({age} лет)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования PlayersManager: {e}")
        return False

if __name__ == "__main__":
    # Тестируем подключение к Google Sheets
    sheets_success = test_google_sheets_with_file()
    
    if sheets_success:
        # Тестируем PlayersManager
        manager_success = test_players_manager_with_file()
        
        if manager_success:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
            print("Google Sheets полностью настроен и работает")
        else:
            print("\n⚠️ Google Sheets работает, но PlayersManager требует доработки")
    else:
        print("\n❌ Проблемы с подключением к Google Sheets")
