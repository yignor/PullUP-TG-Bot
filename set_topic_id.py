#!/usr/bin/env python3
"""
Скрипт для установки ID топика в .env файл
"""

import os
import re

def set_topic_id(topic_id):
    """Устанавливает ID топика в .env файл"""
    
    env_file = ".env"
    
    if not os.path.exists(env_file):
        print(f"❌ Файл {env_file} не найден")
        return False
    
    # Читаем файл
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, есть ли уже эта переменная
    if "ANNOUNCEMENTS_TOPIC_ID=" in content:
        # Заменяем существующее значение
        new_content = re.sub(
            r'ANNOUNCEMENTS_TOPIC_ID=.*',
            f'ANNOUNCEMENTS_TOPIC_ID={topic_id}',
            content
        )
        print(f"✅ Обновлен ANNOUNCEMENTS_TOPIC_ID={topic_id}")
    else:
        # Добавляем новую переменную
        new_content = content + f"\nANNOUNCEMENTS_TOPIC_ID={topic_id}"
        print(f"✅ Добавлен ANNOUNCEMENTS_TOPIC_ID={topic_id}")
    
    # Записываем обратно
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    """Основная функция"""
    
    print("🔧 УСТАНОВКА ID ТОПИКА")
    print("=" * 30)
    
    # Используем найденный ID
    topic_id = "15"
    
    print(f"📋 Найденный ID топика: {topic_id}")
    print(f"📝 Устанавливаю в .env файл...")
    
    if set_topic_id(topic_id):
        print("\n✅ ID топика успешно установлен!")
        print("🧪 Теперь можно протестировать:")
        print("python test_topic_send.py")
    else:
        print("\n❌ Ошибка установки ID топика")

if __name__ == "__main__":
    main()
