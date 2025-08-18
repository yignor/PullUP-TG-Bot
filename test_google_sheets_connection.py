#!/usr/bin/env python3
"""
Тест подключения к Google Sheets
"""

import os
import json
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_google_sheets_setup():
    """Тестирует настройку Google Sheets"""
    print("🧪 ТЕСТ НАСТРОЙКИ GOOGLE SHEETS")
    print("=" * 50)
    
    # Проверяем переменные окружения
    credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    
    print(f"📋 GOOGLE_SHEETS_CREDENTIALS: {'✅ Настроен' if credentials else '❌ Не настроен'}")
    print(f"📊 SPREADSHEET_ID: {'✅ Настроен' if spreadsheet_id else '❌ Не настроен'}")
    
    if not credentials:
        print("\n❌ GOOGLE_SHEETS_CREDENTIALS не найден!")
        print("📝 Инструкции по получению:")
        print("1. Перейдите в https://console.cloud.google.com/")
        print("2. Создайте проект и включите Google Sheets API")
        print("3. Создайте Service Account")
        print("4. Скачайте JSON ключ")
        print("5. Добавьте содержимое JSON в .env файл:")
        print("   GOOGLE_SHEETS_CREDENTIALS='{\"type\":\"service_account\",...}'")
        return False
    
    if not spreadsheet_id:
        print("\n❌ SPREADSHEET_ID не найден!")
        print("📝 Инструкции:")
        print("1. Создайте Google таблицу")
        print("2. Скопируйте ID из URL")
        print("3. Добавьте в .env файл:")
        print("   SPREADSHEET_ID='your-spreadsheet-id'")
        return False
    
    # Проверяем формат credentials
    try:
        creds_json = json.loads(credentials)
        print(f"✅ Формат credentials корректен")
        print(f"   Project ID: {creds_json.get('project_id', 'Не найден')}")
        print(f"   Client Email: {creds_json.get('client_email', 'Не найден')}")
    except json.JSONDecodeError:
        print("❌ Ошибка в формате GOOGLE_SHEETS_CREDENTIALS")
        print("   Убедитесь, что это валидный JSON")
        return False
    
    # Пытаемся подключиться к Google Sheets
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        # Создаем credentials объект
        creds = Credentials.from_service_account_info(
            creds_json,
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
        
        return True
        
    except ImportError:
        print("❌ Библиотеки не установлены!")
        print("   Установите: pip install gspread google-auth")
        return False
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        print("   Проверьте:")
        print("   - Правильность credentials")
        print("   - Доступ к таблице (поделитесь с client_email)")
        print("   - Включен ли Google Sheets API")
        return False

def show_setup_instructions():
    """Показывает инструкции по настройке"""
    print("\n📚 ПОЛНЫЕ ИНСТРУКЦИИ ПО НАСТРОЙКЕ")
    print("=" * 50)
    print("1. 🌐 Перейдите в Google Cloud Console:")
    print("   https://console.cloud.google.com/")
    print()
    print("2. 📁 Создайте новый проект или выберите существующий")
    print()
    print("3. 🔌 Включите Google Sheets API:")
    print("   APIs & Services → Library → Google Sheets API → Enable")
    print()
    print("4. 👤 Создайте Service Account:")
    print("   APIs & Services → Credentials → Create Credentials → Service Account")
    print("   Name: telegram-bot-sheets")
    print()
    print("5. 🔑 Создайте ключ:")
    print("   Service Account → Keys → Add Key → Create new key → JSON")
    print()
    print("6. 📊 Создайте Google таблицу и поделитесь с client_email")
    print()
    print("7. 📝 Добавьте в .env файл:")
    print("   GOOGLE_SHEETS_CREDENTIALS='содержимое_JSON_файла'")
    print("   SPREADSHEET_ID='ID_вашей_таблицы'")

if __name__ == "__main__":
    success = test_google_sheets_setup()
    
    if not success:
        show_setup_instructions()
    else:
        print("\n🎉 Google Sheets настроен правильно!")
        print("Теперь можно использовать players_manager.py")
