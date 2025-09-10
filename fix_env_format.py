#!/usr/bin/env python3
"""
Скрипт для исправления формата .env файла
"""

import os
import json
import shutil
from datetime import datetime

def fix_env_format():
    """Исправляет формат .env файла"""
    
    # Создаем резервную копию
    backup_name = f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2('.env', backup_name)
    print(f"✅ Создана резервная копия: {backup_name}")
    
    # Читаем текущий .env файл
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("📄 Текущее содержимое .env файла:")
    print("=" * 50)
    print(content)
    print("=" * 50)
    
    # Парсим строки
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines, 1):
        if line.strip().startswith('GOOGLE_SHEETS_CREDENTIALS='):
            print(f"🔧 Исправляем строку {i}: GOOGLE_SHEETS_CREDENTIALS")
            
            # Извлекаем JSON часть
            json_start = line.find('{')
            if json_start != -1:
                json_part = line[json_start:]
                
                try:
                    # Парсим JSON для проверки
                    creds_dict = json.loads(json_part)
                    print("✅ JSON валидный")
                    
                    # Создаем новую строку с правильным экранированием
                    # Заменяем переносы строк на \n
                    escaped_json = json_part.replace('\n', '\\n')
                    new_line = f"GOOGLE_SHEETS_CREDENTIALS={escaped_json}"
                    new_lines.append(new_line)
                    print("✅ JSON правильно экранирован")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Ошибка парсинга JSON: {e}")
                    new_lines.append(line)  # Оставляем как есть
            else:
                print(f"❌ JSON не найден в строке {i}")
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Записываем исправленный файл
    with open('.env', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("\n✅ .env файл исправлен")
    
    # Проверяем, что файл можно загрузить
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        bot_token = os.getenv("BOT_TOKEN")
        chat_id = os.getenv("CHAT_ID")
        google_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        spreadsheet_id = os.getenv("SPREADSHEET_ID")
        
        print("\n🔍 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
        print(f"BOT_TOKEN: {'✅' if bot_token else '❌'}")
        print(f"CHAT_ID: {'✅' if chat_id else '❌'}")
        print(f"GOOGLE_SHEETS_CREDENTIALS: {'✅' if google_credentials else '❌'}")
        print(f"SPREADSHEET_ID: {'✅' if spreadsheet_id else '❌'}")
        
        if google_credentials:
            try:
                creds_dict = json.loads(google_credentials)
                print("✅ JSON в GOOGLE_SHEETS_CREDENTIALS валидный")
            except json.JSONDecodeError as e:
                print(f"❌ JSON в GOOGLE_SHEETS_CREDENTIALS невалидный: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return False

def main():
    print("🔧 ИСПРАВЛЕНИЕ ФОРМАТА .ENV ФАЙЛА")
    print("=" * 50)
    
    success = fix_env_format()
    
    if success:
        print("\n✅ Исправление завершено успешно")
    else:
        print("\n❌ Ошибка при исправлении")

if __name__ == "__main__":
    main()
