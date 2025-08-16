#!/usr/bin/env python3
"""
Тестовый скрипт для проверки GitHub Actions локально
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_environment_variables():
    """Проверяет наличие необходимых переменных окружения"""
    print("🔍 Проверка переменных окружения...")
    
    required_vars = {
        'BOT_TOKEN': 'Токен бота Telegram',
        'CHAT_ID': 'ID продакшн чата',
        'TEST_CHAT_ID': 'ID тестового чата (опционально)'
    }
    
    all_good = True
    
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            if var_name == 'BOT_TOKEN':
                print(f"✅ {var_name}: {value[:10]}... ({description})")
            else:
                print(f"✅ {var_name}: {value} ({description})")
        else:
            if var_name == 'TEST_CHAT_ID':
                print(f"⚠️ {var_name}: не установлен ({description}) - будет использовано значение по умолчанию")
            else:
                print(f"❌ {var_name}: не установлен ({description})")
                all_good = False
    
    return all_good

def test_dependencies():
    """Проверяет наличие необходимых зависимостей"""
    print("\n📦 Проверка зависимостей...")
    
    required_packages = [
        ('aiohttp', 'aiohttp'),
        ('beautifulsoup4', 'bs4'), 
        ('python-telegram-bot', 'telegram'),
        ('lxml', 'lxml'),
        ('python-dotenv', 'dotenv')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - не установлен")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n❌ Отсутствуют пакеты: {', '.join(missing_packages)}")
        print("Установите их командой: pip install -r requirements-github.txt")
        return False
    
    return True

def test_files():
    """Проверяет наличие необходимых файлов"""
    print("\n📁 Проверка файлов...")
    
    required_files = [
        'github_actions_monitor.py',
        'pullup_notifications.py',
        'requirements-github.txt'
    ]
    
    all_good = True
    
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} - не найден")
            all_good = False
    
    return all_good

def test_imports():
    """Проверяет импорты основных модулей"""
    print("\n🔧 Проверка импортов...")
    
    try:
        from github_actions_monitor import main
        print("✅ github_actions_monitor.py - импорт успешен")
    except Exception as e:
        print(f"❌ github_actions_monitor.py - ошибка импорта: {e}")
        return False
    
    try:
        from pullup_notifications import PullUPNotificationManager
        print("✅ pullup_notifications.py - импорт успешен")
    except Exception as e:
        print(f"❌ pullup_notifications.py - ошибка импорта: {e}")
        return False
    
    return True

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование GitHub Actions конфигурации\n")
    
    tests = [
        ("Переменные окружения", test_environment_variables),
        ("Зависимости", test_dependencies),
        ("Файлы", test_files),
        ("Импорты", test_imports)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "="*50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nРезультат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! GitHub Actions должен работать корректно.")
        return 0
    else:
        print("⚠️ Некоторые тесты провалены. Исправьте ошибки перед запуском GitHub Actions.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
