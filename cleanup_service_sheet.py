#!/usr/bin/env python3
"""
Скрипт автоматической очистки старых записей в сервисном листе
"""

import asyncio
from enhanced_duplicate_protection import duplicate_protection

async def cleanup_service_sheet():
    """Очищает старые записи в сервисном листе"""
    print("🧹 АВТОМАТИЧЕСКАЯ ОЧИСТКА СЕРВИСНОГО ЛИСТА")
    print("=" * 60)
    
    try:
        if not duplicate_protection.gc:
            print("❌ Google Sheets не подключен")
            return False
        
        if not duplicate_protection.service_worksheet:
            print("❌ Лист 'Сервисный' не найден")
            return False
        
        print("✅ Система готова к очистке")
        
        # Получаем статистику до очистки
        print(f"\n📊 СТАТИСТИКА ДО ОЧИСТКИ:")
        stats_before = duplicate_protection.get_statistics()
        if 'error' not in stats_before:
            for data_type, data in stats_before.items():
                print(f"   📊 {data_type}: {data['total']} записей")
        
        cleanup_results = []
        
        # Универсальная очистка записей старше 30 дней
        global_cleanup = duplicate_protection.cleanup_expired_records(30)
        if global_cleanup.get('success'):
            cleaned_count = global_cleanup.get('cleaned_count', 0)
            print(f"\n🧽 Общая очистка: удалено {cleaned_count} записей старше 30 дней")
            if cleaned_count > 0:
                cleanup_results.append(f"ВСЕ ТИПЫ: {cleaned_count} записей")
        else:
            print(f"\n⚠️ Общая очистка не выполнена: {global_cleanup.get('error')}")
        
        # Очищаем старые записи по типам
        # Очищаем старые опросы тренировок (старше 30 дней)
        result = duplicate_protection.cleanup_old_records("ОПРОС_ТРЕНИРОВКА", 30)
        if result['success']:
            cleanup_results.append(f"ОПРОС_ТРЕНИРОВКА: {result['cleaned_count']} записей")
        
        # Очищаем старые опросы игр (старше 30 дней)
        result = duplicate_protection.cleanup_old_records("ОПРОС_ИГРА", 30)
        if result['success']:
            cleanup_results.append(f"ОПРОС_ИГРА: {result['cleaned_count']} записей")
        
        # Очищаем старые анонсы игр (старше 30 дней)
        result = duplicate_protection.cleanup_old_records("АНОНС_ИГРА", 30)
        if result['success']:
            cleanup_results.append(f"АНОНС_ИГРА: {result['cleaned_count']} записей")
        
        # Очищаем старые уведомления (старше 30 дней)
        result = duplicate_protection.cleanup_old_records("УВЕДОМЛЕНИЕ", 30)
        if result['success']:
            cleanup_results.append(f"УВЕДОМЛЕНИЕ: {result['cleaned_count']} записей")
        
        # Очищаем старые результаты игр (старше 30 дней)
        result = duplicate_protection.cleanup_old_records("РЕЗУЛЬТАТ_ИГРА", 30)
        if result['success']:
            cleanup_results.append(f"РЕЗУЛЬТАТ_ИГРА: {result['cleaned_count']} записей")
        
        # Очищаем старые дни рождения (старше 30 дней)
        result = duplicate_protection.cleanup_old_records("ДЕНЬ_РОЖДЕНИЯ", 30)
        if result['success']:
            cleanup_results.append(f"ДЕНЬ_РОЖДЕНИЯ: {result['cleaned_count']} записей")
        
        # Получаем статистику после очистки
        print(f"\n📊 СТАТИСТИКА ПОСЛЕ ОЧИСТКИ:")
        stats_after = duplicate_protection.get_statistics()
        if 'error' not in stats_after:
            for data_type, data in stats_after.items():
                print(f"   📊 {data_type}: {data['total']} записей")
        
        # Выводим результаты очистки
        print(f"\n🧹 РЕЗУЛЬТАТЫ ОЧИСТКИ:")
        print("=" * 40)
        if cleanup_results:
            for result in cleanup_results:
                print(f"   ✅ {result}")
        else:
            print("   ℹ️ Старые записи не найдены")
        
        print(f"\n✅ Очистка завершена успешно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка очистки: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(cleanup_service_sheet())
