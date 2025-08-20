#!/usr/bin/env python3
"""
Скрипт для очистки истории анонсов
"""

import json
import os

def clear_announcements_history():
    """Очищает историю анонсов"""
    history_file = "game_announcements.json"
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            print(f"📋 Текущая история анонсов:")
            for key, value in history.items():
                print(f"   {key}: {value.get('status', 'unknown')}")
            
            # Очищаем историю
            history = {}
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            print(f"✅ История анонсов очищена")
            
        except Exception as e:
            print(f"❌ Ошибка очистки истории: {e}")
    else:
        print(f"📁 Файл {history_file} не найден")

if __name__ == "__main__":
    clear_announcements_history()
