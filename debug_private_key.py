#!/usr/bin/env python3
"""
Скрипт для детальной диагностики private_key
"""

import os
import json
import re

def debug_private_key():
    """Детальная диагностика private_key"""
    print("🔍 ДЕТАЛЬНАЯ ДИАГНОСТИКА PRIVATE_KEY")
    print("=" * 50)
    
    # Получаем переменные окружения
    google_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    
    if not google_credentials:
        print("❌ GOOGLE_SHEETS_CREDENTIALS не найден")
        return
    
    # Парсим JSON с тщательной очисткой
    try:
        # Тщательная очистка от всех проблемных символов
        cleaned_credentials = google_credentials
        
        # Убираем экранированные символы
        cleaned_credentials = cleaned_credentials.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
        
        # Убираем недопустимые управляющие символы
        cleaned_credentials = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned_credentials)
        
        # Убираем лишние пробелы
        cleaned_credentials = cleaned_credentials.strip()
        
        creds_dict = json.loads(cleaned_credentials)
        print("✅ JSON успешно распарсен")
        
    except Exception as e:
        print(f"❌ Ошибка обработки JSON: {e}")
        return
    
    # Анализируем private_key
    if 'private_key' not in creds_dict:
        print("❌ private_key отсутствует в credentials")
        return
    
    private_key = creds_dict['private_key']
    print(f"\n📏 Длина private_key: {len(private_key)} символов")
    
    # Проверяем формат private_key
    print(f"\n🔍 Анализ private_key:")
    print(f"   Начинается с '-----BEGIN PRIVATE KEY-----': {'✅' if private_key.startswith('-----BEGIN PRIVATE KEY-----') else '❌'}")
    print(f"   Заканчивается на '-----END PRIVATE KEY-----': {'✅' if private_key.endswith('-----END PRIVATE KEY-----') else '❌'}")
    
    # Показываем начало и конец
    print(f"\n📄 Начало private_key (первые 100 символов):")
    print(f"   {private_key[:100]}...")
    
    print(f"\n📄 Конец private_key (последние 100 символов):")
    print(f"   ...{private_key[-100:]}")
    
    # Проверяем на наличие переносов строк
    print(f"\n🔍 Проверка переносов строк:")
    contains_escaped_newline = '\\n' in private_key
    contains_real_newline = '\n' in private_key
    print(f"   Содержит '\\n': {'✅' if contains_escaped_newline else '❌'}")
    print(f"   Содержит реальные переносы строк: {'✅' if contains_real_newline else '❌'}")
    
    # Показываем количество строк
    lines = private_key.split('\n')
    print(f"   Количество строк: {len(lines)}")
    
    # Проверяем каждую строку
    print(f"\n📋 Анализ строк private_key:")
    for i, line in enumerate(lines[:10]):  # Показываем первые 10 строк
        print(f"   Строка {i+1}: {line[:50]}...")
    
    if len(lines) > 10:
        print(f"   ... и еще {len(lines) - 10} строк")
    
    # Пробуем очистить private_key
    print(f"\n🧹 Очистка private_key...")
    
    # Убираем экранированные символы
    cleaned_private_key = private_key.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
    
    # Убираем лишние пробелы в начале и конце
    cleaned_private_key = cleaned_private_key.strip()
    
    print(f"   Длина после очистки: {len(cleaned_private_key)} символов")
    print(f"   Начинается правильно: {'✅' if cleaned_private_key.startswith('-----BEGIN PRIVATE KEY-----') else '❌'}")
    print(f"   Заканчивается правильно: {'✅' if cleaned_private_key.endswith('-----END PRIVATE KEY-----') else '❌'}")
    
    # Показываем очищенный ключ
    print(f"\n📄 Очищенный private_key (первые 200 символов):")
    print(f"   {cleaned_private_key[:200]}...")
    
    # Проверяем, что ключ содержит правильное количество строк
    cleaned_lines = cleaned_private_key.split('\n')
    print(f"\n📊 Анализ очищенного ключа:")
    print(f"   Количество строк: {len(cleaned_lines)}")
    print(f"   Ожидается примерно 28-30 строк для RSA ключа")
    
    # Проверяем структуру
    if len(cleaned_lines) >= 3:
        print(f"   Строка 1: {cleaned_lines[0]}")
        print(f"   Строка 2: {cleaned_lines[1][:20]}...")
        print(f"   Последняя строка: {cleaned_lines[-1]}")
    
    # Проверяем, что ключ не обрезан
    if len(cleaned_private_key) < 1000:
        print(f"⚠️ ВНИМАНИЕ: private_key слишком короткий ({len(cleaned_private_key)} символов)")
        print(f"   Возможно, ключ обрезан в GitHub Secrets")
    else:
        print(f"✅ Длина private_key выглядит нормально")

if __name__ == "__main__":
    debug_private_key()
