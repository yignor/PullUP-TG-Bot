#!/usr/bin/env python3
"""
Скрипт для детальной диагностики credentials в GitHub Actions
"""

import os
import json
import tempfile
import gspread

def debug_credentials():
    """Детальная диагностика credentials"""
    print("🔍 ДЕТАЛЬНАЯ ДИАГНОСТИКА CREDENTIALS")
    print("=" * 50)
    
    # Получаем переменные окружения
    google_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    
    print(f"🔍 Проверка переменных:")
    print(f"   GOOGLE_SHEETS_CREDENTIALS: {'✅' if google_credentials else '❌'}")
    print(f"   SPREADSHEET_ID: {'✅' if spreadsheet_id else '❌'}")
    
    if not google_credentials:
        print("❌ GOOGLE_SHEETS_CREDENTIALS не найден")
        return
    
    print(f"\n📏 Длина GOOGLE_SHEETS_CREDENTIALS: {len(google_credentials)} символов")
    print(f"🔤 Первые 100 символов: {google_credentials[:100]}...")
    print(f"🔤 Последние 100 символов: ...{google_credentials[-100:]}")
    
    # Проверяем на специальные символы
    print(f"\n🔍 Проверка специальных символов:")
    contains_newline = '\\n' in google_credentials
    contains_return = '\\r' in google_credentials
    contains_tab = '\\t' in google_credentials
    print(f"   Содержит \\n: {'✅' if contains_newline else '❌'}")
    print(f"   Содержит \\r: {'✅' if contains_return else '❌'}")
    print(f"   Содержит \\t: {'✅' if contains_tab else '❌'}")
    
    # Пробуем разные способы парсинга
    print(f"\n1️⃣ Парсинг JSON...")
    try:
        # Способ 1: Прямой парсинг
        creds_dict = json.loads(google_credentials)
        print("✅ JSON успешно распарсен (прямой)")
        print(f"   Тип: {type(creds_dict)}")
        print(f"   Ключи: {list(creds_dict.keys())}")
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка прямого парсинга: {e}")
        
        # Способ 2: Тщательная очистка от всех проблемных символов
        try:
            cleaned_credentials = google_credentials
            
            # Убираем экранированные символы
            cleaned_credentials = cleaned_credentials.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
            
            # Убираем недопустимые управляющие символы
            import re
            cleaned_credentials = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned_credentials)
            
            # Убираем лишние пробелы
            cleaned_credentials = cleaned_credentials.strip()
            
            print(f"   🔍 Очищенная строка (первые 200 символов): {cleaned_credentials[:200]}...")
            
            creds_dict = json.loads(cleaned_credentials)
            print("✅ JSON успешно распарсен (после тщательной очистки)")
            print(f"   Тип: {type(creds_dict)}")
            print(f"   Ключи: {list(creds_dict.keys())}")
            
            # Обрабатываем private_key
            if 'private_key' in creds_dict:
                private_key = creds_dict['private_key']
                if isinstance(private_key, str):
                    cleaned_private_key = private_key.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
                    creds_dict['private_key'] = cleaned_private_key
                    print(f"   ✅ Private key обработан (длина: {len(cleaned_private_key)})")
                    
        except json.JSONDecodeError as e2:
            print(f"❌ Ошибка парсинга после очистки: {e2}")
            print(f"   🔍 Первые 100 символов оригинала: {google_credentials[:100]}...")
            print(f"   🔍 Первые 100 символов после очистки: {cleaned_credentials[:100]}...")
            return
    
    # Проверяем обязательные поля
    required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
    print(f"\n2️⃣ Проверка обязательных полей:")
    for field in required_fields:
        if field in creds_dict:
            value = creds_dict[field]
            if field == 'private_key':
                print(f"   ✅ {field}: {'✅' if value else '❌'} (длина: {len(str(value))})")
            else:
                print(f"   ✅ {field}: {value}")
        else:
            print(f"   ❌ {field}: отсутствует")
    
    # Пробуем разные способы авторизации
    print(f"\n3️⃣ Тестирование авторизации...")
    
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # Метод 1: service_account_from_dict
    print(f"\n   Метод 1: gspread.service_account_from_dict")
    try:
        gc1 = gspread.service_account_from_dict(creds_dict, scopes=scopes)
        print("   ✅ Успешно!")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Метод 2: Временный файл
    print(f"\n   Метод 2: Временный файл")
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(creds_dict, f, ensure_ascii=False)
            temp_file = f.name
        
        print(f"   📁 Создан файл: {temp_file}")
        
        gc2 = gspread.service_account(temp_file)
        print("   ✅ Успешно!")
        
        # Проверяем доступ к таблице
        if spreadsheet_id:
            spreadsheet = gc2.open_by_key(spreadsheet_id)
            print(f"   📊 Таблица: {spreadsheet.title}")
        
        # Удаляем временный файл
        os.unlink(temp_file)
        print("   🗑️ Файл удален")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        if 'temp_file' in locals():
            try:
                os.unlink(temp_file)
            except:
                pass
    
    # Метод 3: Строка как файл
    print(f"\n   Метод 3: Строка как файл")
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(google_credentials)
            temp_file = f.name
        
        print(f"   📁 Создан файл из строки: {temp_file}")
        
        gc3 = gspread.service_account(temp_file)
        print("   ✅ Успешно!")
        
        # Удаляем временный файл
        os.unlink(temp_file)
        print("   🗑️ Файл удален")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        if 'temp_file' in locals():
            try:
                os.unlink(temp_file)
            except:
                pass

if __name__ == "__main__":
    debug_credentials()
