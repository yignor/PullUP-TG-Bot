#!/usr/bin/env python3
"""
Тест доступа к Google таблице
"""

import os
import json
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_table_access():
    """Тестирует доступ к таблице"""
    print("🧪 ТЕСТ ДОСТУПА К ТАБЛИЦЕ")
    print("=" * 50)
    
    # Получаем переменные
    credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    
    print(f"📋 Credentials тип: {type(credentials).__name__}")
    print(f"📋 Credentials длина: {len(credentials) if credentials else 0}")
    print(f"📋 Credentials начало: {credentials[:20] if credentials else 'Нет'}...")
    print(f"📊 Spreadsheet ID: {spreadsheet_id}")
    
    # Проверяем, что это JSON
    if not credentials:
        print("❌ GOOGLE_SHEETS_CREDENTIALS не настроен")
        return False
        
    try:
        creds_json = json.loads(credentials)
        print(f"✅ Это валидный JSON")
        print(f"   Тип: {creds_json.get('type', 'Не указан')}")
        print(f"   Project ID: {creds_json.get('project_id', 'Не найден')}")
        print(f"   Client Email: {creds_json.get('client_email', 'Не найден')}")
        
        # Пытаемся подключиться
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
    
    except json.JSONDecodeError:
        print(f"❌ Это не валидный JSON")
        print(f"   Возможно, это API ключ или другой тип credentials")
        
        # Пытаемся использовать как API ключ
        try:
            import gspread
            
            # Пытаемся подключиться с API ключом
            client = gspread.service_account_from_dict({
                'type': 'service_account',
                'project_id': 'test',
                'private_key_id': credentials,
                'private_key': credentials,
                'client_email': 'test@test.com',
                'client_id': '123',
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
                'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/test%40test.com'
            })
            
            # Пытаемся открыть таблицу
            spreadsheet = client.open_by_key(spreadsheet_id)
            print(f"✅ Подключение с API ключом успешно!")
            print(f"   Название таблицы: {spreadsheet.title}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка подключения с API ключом: {e}")
            print(f"   Нужен полный JSON файл Service Account")
            return False

def show_credentials_help():
    """Показывает помощь по credentials"""
    print("\n📚 ПОМОЩЬ ПО CREDENTIALS")
    print("=" * 50)
    print("❌ Текущие credentials не подходят для Google Sheets API")
    print()
    print("🔑 Нужен полный JSON файл Service Account, который содержит:")
    print("   - type: 'service_account'")
    print("   - project_id: 'ваш-проект'")
    print("   - private_key: '-----BEGIN PRIVATE KEY-----...'")
    print("   - client_email: 'service@project.iam.gserviceaccount.com'")
    print("   - и другие поля")
    print()
    print("📝 Как получить правильные credentials:")
    print("1. Перейдите в https://console.cloud.google.com/")
    print("2. Создайте проект и включите Google Sheets API")
    print("3. Создайте Service Account")
    print("4. Скачайте JSON ключ (не API ключ!)")
    print("5. Скопируйте ВСЁ содержимое JSON файла в .env")
    print()
    print("💡 Пример правильного формата:")
    print("GOOGLE_SHEETS_CREDENTIALS='{\"type\":\"service_account\",\"project_id\":\"...\",...}'")

if __name__ == "__main__":
    success = test_table_access()
    
    if not success:
        show_credentials_help()
    else:
        print("\n🎉 Доступ к таблице работает!")
        print("Теперь можно использовать players_manager.py")
