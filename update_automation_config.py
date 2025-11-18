#!/usr/bin/env python3
"""
Скрипт для обновления раздела автоматических сообщений в Google Sheets
Добавляет новые настройки из AUTOMATION_DEFAULT_ROWS
"""

from enhanced_duplicate_protection import duplicate_protection

def main():
    """Обновляет раздел автоматических сообщений в Google Sheets"""
    print("🔄 Обновление раздела автоматических сообщений в Google Sheets")
    print("=" * 60)
    
    if not duplicate_protection.config_worksheet:
        print("❌ Лист 'Конфиг' не найден")
        return
    
    try:
        # Вызываем метод, который автоматически обновит раздел автоматических сообщений
        duplicate_protection._ensure_automation_section_structure(duplicate_protection.config_worksheet)
        print("✅ Раздел автоматических сообщений успешно обновлен")
        print("\n📋 Добавлены/обновлены следующие настройки:")
        from enhanced_duplicate_protection import AUTOMATION_DEFAULT_ROWS
        for row in AUTOMATION_DEFAULT_ROWS:
            print(f"   • {row['name']} ({row['key']})")
        print("\n💡 Теперь можно настроить ID топика для 'Календарные события' в Google Sheets")
    except Exception as e:
        print(f"❌ Ошибка обновления: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

