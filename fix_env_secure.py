#!/usr/bin/env python3
"""
Безопасный скрипт для исправления .env файла
НЕ СОДЕРЖИТ ТОКЕНОВ ИЛИ СЕКРЕТНЫХ ДАННЫХ
"""

import os
import shutil
from datetime import datetime

def fix_env_secure():
    """Безопасно исправляет .env файл"""
    
    # Создаем резервную копию
    backup_name = f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2('.env', backup_name)
    print(f"✅ Создана резервная копия: {backup_name}")
    
    # Читаем текущий .env файл
    with open('.env', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Создаем новый .env файл без проблемной переменной
    new_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith('GOOGLE_SHEETS_CREDENTIALS='):
            print("⚠️ Удаляем проблемную переменную GOOGLE_SHEETS_CREDENTIALS")
            continue
        elif line and not line.startswith('#'):
            new_lines.append(line)
        elif line.startswith('#'):
            new_lines.append(line)
    
    # Добавляем комментарий о том, что credentials теперь в отдельном файле
    new_lines.append("")
    new_lines.append("# Google credentials теперь в отдельном файле google_credentials.json")
    new_lines.append("# GOOGLE_SHEETS_CREDENTIALS удален из .env для избежания проблем с парсингом")
    
    # Записываем новый .env файл
    with open('.env', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("✅ .env файл исправлен")
    print("✅ Проблемная переменная GOOGLE_SHEETS_CREDENTIALS удалена")
    print("✅ Google credentials должны быть в файле google_credentials.json")
    
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
    print("🔧 БЕЗОПАСНОЕ ИСПРАВЛЕНИЕ .ENV ФАЙЛА")
    print("=" * 50)
    print("⚠️ ВНИМАНИЕ: Этот скрипт НЕ содержит токенов или секретных данных")
    
    success = fix_env_secure()
    
    if success:
        print("\n✅ Исправление завершено успешно")
        print("📝 Теперь Google credentials должны быть в google_credentials.json")
        print("🔒 Все токены остались в вашем .env файле")
    else:
        print("\n❌ Ошибка при исправлении")

if __name__ == "__main__":
    main()
