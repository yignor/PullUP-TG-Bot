#!/usr/bin/env python3
"""
Тестовая версия менеджера игроков для локального тестирования
"""

import datetime
from typing import List, Dict, Any, Optional

# Тестовые данные игроков (вместо Google Sheets)
TEST_PLAYERS = [
    {
        'name': 'Шахманов Максим',
        'nickname': '@max_shah',
        'telegram_id': '123456789',
        'birthday': '2006-08-17',
        'status': 'Активный',
        'team': 'Pull Up',
        'added_date': '2025-08-18',
        'notes': 'Тестовые данные'
    },
    {
        'name': 'Иванов Иван',
        'nickname': '@ivan_ball',
        'telegram_id': '987654321',
        'birthday': '1995-03-15',
        'status': 'Активный',
        'team': 'Pull Up-Фарм',
        'added_date': '2025-08-18',
        'notes': 'Тестовые данные'
    },
    {
        'name': 'Петров Петр',
        'nickname': '@petr_hoop',
        'telegram_id': '555666777',
        'birthday': '1998-11-22',
        'status': 'Неактивный',
        'team': 'Pull Up',
        'added_date': '2025-08-18',
        'notes': 'Тестовые данные'
    }
]

class TestPlayersManager:
    """Тестовый менеджер данных игроков"""
    
    def __init__(self):
        self.players = TEST_PLAYERS.copy()
        print("🧪 Тестовый менеджер игроков инициализирован")
    
    def get_all_players(self) -> List[Dict[str, Any]]:
        """Получает всех игроков"""
        print(f"✅ Загружено {len(self.players)} игроков (тестовые данные)")
        return self.players
    
    def get_active_players(self) -> List[Dict[str, Any]]:
        """Получает только активных игроков"""
        active_players = [p for p in self.players if p.get('status', '').lower() == 'активный']
        print(f"✅ Активных игроков: {len(active_players)}")
        return active_players
    
    def get_players_with_birthdays_today(self) -> List[Dict[str, Any]]:
        """Получает игроков с днями рождения сегодня"""
        try:
            active_players = self.get_active_players()
            today = datetime.datetime.now()
            today_str = today.strftime("%m-%d")
            
            birthday_players = []
            for player in active_players:
                birthday = player.get('birthday', '')
                if birthday:
                    try:
                        # Парсим дату рождения
                        if '-' in birthday:
                            # Формат YYYY-MM-DD
                            bd_date = datetime.datetime.strptime(birthday, "%Y-%m-%d")
                        elif '.' in birthday:
                            # Формат DD.MM.YYYY
                            bd_date = datetime.datetime.strptime(birthday, "%d.%m.%Y")
                        else:
                            continue
                        
                        bd_str = bd_date.strftime("%m-%d")
                        if bd_str == today_str:
                            # Вычисляем возраст
                            age = today.year - bd_date.year
                            if today.month < bd_date.month or (today.month == bd_date.month and today.day < bd_date.day):
                                age -= 1
                            
                            player_copy = player.copy()
                            player_copy['age'] = age
                            birthday_players.append(player_copy)
                            
                    except ValueError:
                        print(f"⚠️ Неверный формат даты для {player.get('name')}: {birthday}")
                        continue
            
            print(f"🎂 Дней рождения сегодня: {len(birthday_players)}")
            return birthday_players
            
        except Exception as e:
            print(f"❌ Ошибка получения дней рождения: {e}")
            return []
    
    def add_player(self, name: str, birthday: str, nickname: str = "", 
                   telegram_id: str = "", team: str = "", notes: str = "") -> bool:
        """Добавляет нового игрока (только в тестовой памяти)"""
        try:
            # Проверяем обязательные поля
            if not name or not birthday:
                print("❌ Имя и дата рождения обязательны")
                return False
            
            # Создаем нового игрока
            new_player = {
                'name': name,
                'nickname': nickname,
                'telegram_id': telegram_id,
                'birthday': birthday,
                'status': 'Активный',
                'team': team,
                'added_date': datetime.datetime.now().strftime("%Y-%m-%d"),
                'notes': notes
            }
            
            # Добавляем в список
            self.players.append(new_player)
            print(f"✅ Игрок {name} добавлен (тестовые данные)")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка добавления игрока: {e}")
            return False
    
    def get_player_by_telegram_id(self, telegram_id: str) -> Optional[Dict[str, Any]]:
        """Находит игрока по Telegram ID"""
        try:
            for player in self.players:
                if player.get('telegram_id') == telegram_id:
                    return player
            return None
            
        except Exception as e:
            print(f"❌ Ошибка поиска игрока: {e}")
            return None

# Глобальный экземпляр тестового менеджера
test_players_manager = TestPlayersManager()

def get_years_word(age: int) -> str:
    """Возвращает правильное склонение слова 'год'"""
    if age % 10 == 1 and age % 100 != 11:
        return "год"
    elif age % 10 in [2, 3, 4] and age % 100 not in [12, 13, 14]:
        return "года"
    else:
        return "лет"

def run_test():
    """Тестирует функциональность тестового менеджера игроков"""
    print("🧪 ТЕСТИРОВАНИЕ ТЕСТОВОГО МЕНЕДЖЕРА ИГРОКОВ")
    print("=" * 50)
    
    # Получаем всех игроков
    all_players = test_players_manager.get_all_players()
    print(f"📊 Всего игроков: {len(all_players)}")
    
    # Получаем активных игроков
    active_players = test_players_manager.get_active_players()
    print(f"✅ Активных игроков: {len(active_players)}")
    
    # Проверяем дни рождения сегодня
    birthday_players = test_players_manager.get_players_with_birthdays_today()
    print(f"🎂 Дней рождения сегодня: {len(birthday_players)}")
    
    if birthday_players:
        print("🎉 Именинники:")
        for player in birthday_players:
            age = player.get('age', 0)
            years_word = get_years_word(age)
            print(f"   - {player['name']} ({age} {years_word})")
    
    # Показываем всех игроков
    print(f"\n📋 СПИСОК ВСЕХ ИГРОКОВ:")
    for i, player in enumerate(all_players, 1):
        status_emoji = "✅" if player['status'] == 'Активный' else "❌"
        print(f"   {i}. {status_emoji} {player['name']} - {player['birthday']} - {player.get('team', '')}")
    
    print("✅ Тестирование завершено")

if __name__ == "__main__":
    run_test()
