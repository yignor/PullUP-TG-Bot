#!/usr/bin/env python3
"""
Быстрое исправление .env файла на продакшене
"""

import os
import shutil
from datetime import datetime

def quick_fix():
    """Быстро исправляет .env файл"""
    
    print("🚨 БЫСТРОЕ ИСПРАВЛЕНИЕ .ENV ФАЙЛА")
    print("=" * 50)
    
    # Создаем резервную копию
    backup_name = f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2('.env', backup_name)
    print(f"✅ Создана резервная копия: {backup_name}")
    
    # Читаем текущий .env файл
    with open('.env', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Создаем новый .env файл без проблемной переменной
    new_lines = []
    removed_lines = 0
    
    for line in lines:
        if line.strip().startswith('GOOGLE_SHEETS_CREDENTIALS='):
            print("⚠️ Удаляем проблемную переменную GOOGLE_SHEETS_CREDENTIALS")
            removed_lines += 1
            continue
        else:
            new_lines.append(line)
    
    # Записываем новый .env файл
    with open('.env', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✅ Удалено {removed_lines} проблемных строк")
    print("✅ .env файл исправлен")
    
    # Проверяем, что файл можно загрузить
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        bot_token = os.getenv("BOT_TOKEN")
        chat_id = os.getenv("CHAT_ID")
        spreadsheet_id = os.getenv("SPREADSHEET_ID")
        
        print("\n🔍 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
        print(f"BOT_TOKEN: {'✅' if bot_token else '❌'}")
        print(f"CHAT_ID: {'✅' if chat_id else '❌'}")
        print(f"SPREADSHEET_ID: {'✅' if spreadsheet_id else '❌'}")
        
        # Проверяем наличие google_credentials.json
        if os.path.exists('google_credentials.json'):
            print("✅ google_credentials.json найден")
        else:
            print("❌ google_credentials.json не найден")
            print("⚠️ ВАЖНО: Создайте файл google_credentials.json с вашими Google credentials")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return False

def main():
    success = quick_fix()
    
    if success:
        print("\n✅ Исправление завершено успешно")
        print("📝 Теперь Google credentials загружаются из google_credentials.json")
        print("🔒 Все токены остались в .env файле")
        print("\n🧪 Тестирование:")
        print("python3 training_polls_enhanced.py")
    else:
        print("\n❌ Ошибка при исправлении")

if __name__ == "__main__":
    main()
