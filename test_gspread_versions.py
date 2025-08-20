#!/usr/bin/env python3
"""
Скрипт для тестирования разных версий gspread и способов авторизации
"""

import os
import json
import tempfile
import subprocess
import sys

def test_gspread_versions():
    """Тестирует разные версии gspread"""
    print("🧪 ТЕСТИРОВАНИЕ ВЕРСИЙ GSPREAD")
    print("=" * 50)
    
    # Получаем переменные окружения
    google_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    
    if not google_credentials:
        print("❌ GOOGLE_SHEETS_CREDENTIALS не найден")
        return
    
    # Парсим JSON
    try:
        cleaned_credentials = google_credentials.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
        creds_dict = json.loads(cleaned_credentials)
        
        # Обрабатываем private_key
        if 'private_key' in creds_dict:
            private_key = creds_dict['private_key']
            if isinstance(private_key, str):
                cleaned_private_key = private_key.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
                creds_dict['private_key'] = cleaned_private_key
        
        print("✅ JSON успешно обработан")
    except Exception as e:
        print(f"❌ Ошибка обработки JSON: {e}")
        return
    
    # Проверяем текущую версию gspread
    try:
        import gspread
        print(f"📦 Текущая версия gspread: {gspread.__version__}")
    except ImportError:
        print("❌ gspread не установлен")
        return
    
    # Тестируем разные способы авторизации
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    print(f"\n🔧 Тестирование способов авторизации...")
    
    # Метод 1: service_account_from_dict
    print(f"\n1️⃣ Метод: gspread.service_account_from_dict")
    try:
        gc1 = gspread.service_account_from_dict(creds_dict, scopes=scopes)
        print("   ✅ Успешно!")
        
        if spreadsheet_id:
            spreadsheet = gc1.open_by_key(spreadsheet_id)
            print(f"   📊 Таблица: {spreadsheet.title}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        print(f"   🔍 Тип ошибки: {type(e).__name__}")
    
    # Метод 2: Временный файл с json.dump
    print(f"\n2️⃣ Метод: Временный файл (json.dump)")
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(creds_dict, f, ensure_ascii=False, indent=2)
            temp_file = f.name
        
        print(f"   📁 Создан файл: {temp_file}")
        
        # Показываем содержимое файла
        with open(temp_file, 'r') as f:
            content = f.read()
            print(f"   📄 Первые 200 символов файла:")
            print(f"   {content[:200]}...")
        
        gc2 = gspread.service_account(temp_file)
        print("   ✅ Успешно!")
        
        if spreadsheet_id:
            spreadsheet = gc2.open_by_key(spreadsheet_id)
            print(f"   📊 Таблица: {spreadsheet.title}")
        
        # Удаляем временный файл
        os.unlink(temp_file)
        print("   🗑️ Файл удален")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        print(f"   🔍 Тип ошибки: {type(e).__name__}")
        if 'temp_file' in locals():
            try:
                os.unlink(temp_file)
            except:
                pass
    
    # Метод 3: Прямая запись строки в файл
    print(f"\n3️⃣ Метод: Прямая запись строки в файл")
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(cleaned_credentials)
            temp_file = f.name
        
        print(f"   📁 Создан файл: {temp_file}")
        
        # Показываем содержимое файла
        with open(temp_file, 'r') as f:
            content = f.read()
            print(f"   📄 Первые 200 символов файла:")
            print(f"   {content[:200]}...")
        
        gc3 = gspread.service_account(temp_file)
        print("   ✅ Успешно!")
        
        if spreadsheet_id:
            spreadsheet = gc3.open_by_key(spreadsheet_id)
            print(f"   📊 Таблица: {spreadsheet.title}")
        
        # Удаляем временный файл
        os.unlink(temp_file)
        print("   🗑️ Файл удален")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        print(f"   🔍 Тип ошибки: {type(e).__name__}")
        if 'temp_file' in locals():
            try:
                os.unlink(temp_file)
            except:
                pass
    
    # Метод 4: Попробуем с google-auth напрямую
    print(f"\n4️⃣ Метод: google-auth напрямую")
    try:
        from google.oauth2.service_account import Credentials
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc4 = gspread.authorize(creds)
        print("   ✅ Успешно!")
        
        if spreadsheet_id:
            spreadsheet = gc4.open_by_key(spreadsheet_id)
            print(f"   📊 Таблица: {spreadsheet.title}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        print(f"   🔍 Тип ошибки: {type(e).__name__}")

if __name__ == "__main__":
    test_gspread_versions()
