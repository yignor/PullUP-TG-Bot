#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправленной функции format_announcement_message
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

def format_announcement_message(game_info: dict, game_link: str = None, found_team: str = None) -> str:
    """Форматирует сообщение анонса игры (исправленная версия)"""
    # Определяем нашу команду и соперника
    team1 = game_info.get('team1', '')
    team2 = game_info.get('team2', '')
    
    print(f"🔍 Анализируем команды: {team1} vs {team2}")
    
    # Находим нашу команду (используем расширенный поиск)
    our_team = None
    opponent = None
    
    # Проверяем team1
    if any(target_team in team1 for target_team in ['Pull Up', 'PullUP']):
        our_team = team1
        opponent = team2
        print(f"   ✅ Наша команда найдена в team1: {our_team}")
        print(f"   🏀 Соперник: {opponent}")
    # Проверяем team2
    elif any(target_team in team2 for target_team in ['Pull Up', 'PullUP']):
        our_team = team2
        opponent = team1
        print(f"   ✅ Наша команда найдена в team2: {our_team}")
        print(f"   🏀 Соперник: {opponent}")
    else:
        print(f"   ❌ Наша команда не найдена ни в одной из команд")
        return f"🏀 Сегодня игра против {team2} в {game_info['venue']}.\n🕐 Время игры: {game_info['time']}."
    
    # Определяем категорию команды с правильным склонением
    # Используем найденную команду из iframe, если она передана, но всегда учитываем соперника
    if found_team:
        team_category = get_team_category(found_team, opponent)
        print(f"🏷️ Используем найденную команду для категории: {found_team} vs {opponent} -> {team_category}")
    else:
        team_category = get_team_category(our_team, opponent)
        print(f"🏷️ Используем команду из расписания для категории: {our_team} vs {opponent} -> {team_category}")
    
    # Формируем анонс
    # Нормализуем время (заменяем точку на двоеточие для ясности)
    normalized_time = game_info['time'].replace('.', ':')
    announcement = f"🏀 Сегодня игра {team_category} против {opponent} в {game_info['venue']}.\n"
    announcement += f"🕐 Время игры: {normalized_time}."
    
    if game_link:
        if game_link.startswith('game.html?'):
            full_url = f"http://letobasket.ru/{game_link}"
        else:
            full_url = game_link
        announcement += f"\n🔗 Ссылка на игру: <a href=\"{full_url}\">тут</a>"
    
    return announcement

def test_format_announcement():
    """Тестирует функцию format_announcement_message"""
    
    print("🔍 ТЕСТИРОВАНИЕ ФУНКЦИИ FORMAT_ANNOUNCEMENT_MESSAGE")
    print("=" * 60)
    
    # Тестовые случаи
    test_cases = [
        {
            'name': 'Кудрово vs Pull Up (без ссылки)',
            'game_info': {
                'team1': 'Кудрово',
                'team2': 'Pull Up',
                'date': '27.08.2025',
                'time': '20.30',
                'venue': 'MarvelHall'
            },
            'game_link': None,
            'found_team': None
        },
        {
            'name': 'Old Stars vs Pull Up (с ссылкой)',
            'game_info': {
                'team1': 'Old Stars',
                'team2': 'Pull Up',
                'date': '27.08.2025',
                'time': '21.45',
                'venue': 'MarvelHall'
            },
            'game_link': 'game.html?gameId=921010&apiUrl=https://reg.infobasket.su&lang=ru',
            'found_team': 'Pull Up'
        },
        {
            'name': 'Pull Up vs Кудрово (перевернутый порядок)',
            'game_info': {
                'team1': 'Pull Up',
                'team2': 'Кудрово',
                'date': '27.08.2025',
                'time': '20.30',
                'venue': 'MarvelHall'
            },
            'game_link': None,
            'found_team': None
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 ТЕСТ {i}: {test_case['name']}")
        print("-" * 40)
        
        announcement = format_announcement_message(
            test_case['game_info'],
            test_case['game_link'],
            test_case['found_team']
        )
        
        print(f"📢 РЕЗУЛЬТАТ:")
        print(announcement)
        print()

if __name__ == "__main__":
    test_format_announcement()
