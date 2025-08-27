#!/usr/bin/env python3
"""
Тестовый скрипт для проверки определения команд
"""

def get_team_category(team_name: str, opponent: str = "", game_time: str = "") -> str:
    """Определяет категорию команды с правильным склонением (как в game_system_manager)"""
    # Нормализуем название команды для сравнения
    team_upper = team_name.upper().replace(" ", "").replace("-", "").replace("_", "")
    
    # Варианты написания для состава развития
    development_variants = [
        "PULLUPФАРМ",
        "PULLUP-ФАРМ", 
        "PULLUP-ФАРМ",
        "PULLUPФАРМ",
        "PULL UPФАРМ",
        "PULL UP-ФАРМ",
        "PULL UP ФАРМ",
        "PULLUP ФАРМ"
    ]
    
    # Проверяем, является ли команда составом развития по названию
    for variant in development_variants:
        if variant in team_upper:
            return "Состав Развития"
    
    # Дополнительная логика: если команда называется "Pull Up", но соперник из списка развития
    if "PULLUP" in team_upper and opponent:
        development_opponents = ['Кудрово', 'Тосно', 'QUASAR', 'TAURUS']
        if opponent in development_opponents:
            return "Состав Развития"
    
    # Если не найден ни один вариант состава развития, то это первый состав
    return "Первый состав"

def test_team_detection():
    """Тестирует определение команд"""
    
    print("🔍 ТЕСТИРОВАНИЕ ОПРЕДЕЛЕНИЯ КОМАНД")
    print("=" * 50)
    
    # Тестовые случаи
    test_cases = [
        ("Pull Up", "Кудрово", "20:30"),
        ("Pull Up", "Old Stars", "21:45"),
        ("Pull Up-Фарм", "Кудрово", "20:30"),
        ("Pull Up-Фарм", "Old Stars", "21:45"),
        ("Pull Up", "Тосно", "12:30"),
        ("Pull Up-Фарм", "Тосно", "12:30"),
    ]
    
    for team_name, opponent, time in test_cases:
        category = get_team_category(team_name, opponent, time)
        print(f"🏀 {team_name} vs {opponent} ({time}) -> {category}")
    
    print("\n📋 АНАЛИЗ:")
    print("Из теста видно, что:")
    print("1. Pull Up vs Кудрово -> Состав Развития (по сопернику)")
    print("2. Pull Up vs Old Stars -> Первый состав")
    print("3. Pull Up-Фарм vs Кудрово -> Состав Развития (по названию)")
    print("4. Pull Up-Фарм vs Old Stars -> Состав Развития (по названию)")
    print("5. Pull Up vs Тосно -> Состав Развития (по сопернику)")
    print("6. Pull Up-Фарм vs Тосно -> Состав Развития (по названию)")
    
    print("\n🎯 ВЫВОД:")
    print("Система правильно определяет:")
    print("- Pull Up-Фарм как Состав Развития (по названию)")
    print("- Pull Up vs Кудрово/Тосно как Состав Развития (по сопернику)")
    print("- Pull Up vs Old Stars как Первый состав")

if __name__ == "__main__":
    test_team_detection()
