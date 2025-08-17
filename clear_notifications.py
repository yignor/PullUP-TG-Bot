#!/usr/bin/env python3
"""
Скрипт для очистки отправленных уведомлений
Используется для тестирования и сброса состояния
"""

import os
import json
from notification_manager import notification_manager

def clear_all_notifications():
    """Очищает все отправленные уведомления"""
    print("🧹 Очистка всех отправленных уведомлений...")
    
    # Очищаем в памяти
    notification_manager.clear_notifications()
    
    # Удаляем файл с уведомлениями
    notifications_file = "sent_notifications.json"
    if os.path.exists(notifications_file):
        os.remove(notifications_file)
        print(f"✅ Файл {notifications_file} удален")
    
    print("✅ Все уведомления очищены")

def show_notifications():
    """Показывает текущие отправленные уведомления"""
    notifications_file = "sent_notifications.json"
    
    if not os.path.exists(notifications_file):
        print("📊 Файл с уведомлениями не найден")
        return
    
    try:
        with open(notifications_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("📊 ТЕКУЩИЕ ОТПРАВЛЕННЫЕ УВЕДОМЛЕНИЯ:")
        print("=" * 50)
        
        game_end = data.get('game_end', [])
        game_start = data.get('game_start', [])
        game_result = data.get('game_result', [])
        morning = data.get('morning', [])
        
        print(f"🏁 Завершение игр: {len(game_end)}")
        for notification in game_end:
            print(f"   - {notification}")
        
        print(f"🏀 Начало игр: {len(game_start)}")
        for notification in game_start:
            print(f"   - {notification}")
        
        print(f"📊 Результаты игр: {len(game_result)}")
        for notification in game_result:
            print(f"   - {notification}")
        
        print(f"🌅 Утренние: {len(morning)}")
        for notification in morning:
            print(f"   - {notification}")
        
        total = len(game_end) + len(game_start) + len(game_result) + len(morning)
        print(f"\n📈 Всего отправленных уведомлений: {total}")
        
    except Exception as e:
        print(f"❌ Ошибка чтения файла уведомлений: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "clear":
            clear_all_notifications()
        elif command == "show":
            show_notifications()
        else:
            print("Использование:")
            print("  python clear_notifications.py clear  # Очистить все уведомления")
            print("  python clear_notifications.py show   # Показать текущие уведомления")
    else:
        print("🧹 СКРИПТ ОЧИСТКИ УВЕДОМЛЕНИЙ")
        print("=" * 40)
        print()
        show_notifications()
        print()
        print("Для очистки всех уведомлений выполните:")
        print("  python clear_notifications.py clear")
