#!/usr/bin/env python3
"""
Гибридный менеджер данных игроков
Автоматически выбирает между Google Sheets и тестовыми данными
"""

import os
import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Проверяем доступность Google Sheets
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Тестовые данные игроков (используются если Google Sheets недоступен)
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
    }
]

class HybridPlayersManager:
    """Гибридный менеджер данных игроков"""
    
    def __init__(self):
        self.use_google_sheets = False
        self.google_manager = None
        self.test_manager = None
        self._init_manager()
    
    def _init_manager(self):
        """Инициализирует подходящий менеджер"""
        try:
            # Проверяем доступность Google Sheets
            if GOOGLE_SHEETS_CREDENTIALS and SPREADSHEET_ID:
                # Пытаемся импортировать Google Sheets менеджер
                from players_manager import PlayersManager
                self.google_manager = PlayersManager()
                
                # Проверяем, что Google Sheets работает
                if self.google_manager.players_sheet:
                    self.use_google_sheets = True
                    print("✅ Используется Google Sheets")
                else:
                    print("⚠️ Google Sheets недоступен, используем тестовые данные")
            else:
                print("⚠️ Google Sheets не настроен, используем тестовые данные")
                
        except Exception as e:
            print(f"⚠️ Ошибка инициализации Google Sheets: {e}")
            print("   Используем тестовые данные")
        
        # Инициализируем тестовый менеджер
        self.test_manager = TestPlayersManager()
    
    def get_all_players(self) -> List[Dict[str, Any]]:
        """Получает всех игроков"""
        if self.use_google_sheets and self.google_manager:
            return self.google_manager.get_all_players()
        else:
            return self.test_manager.get_all_players()
    
    def get_active_players(self) -> List[Dict[str, Any]]:
        """Получает только активных игроков"""
        if self.use_google_sheets and self.google_manager:
            return self.google_manager.get_active_players()
        else:
            return self.test_manager.get_active_players()
    
    def get_players_with_birthdays_today(self) -> List[Dict[str, Any]]:
        """Получает игроков с днями рождения сегодня"""
        if self.use_google_sheets and self.google_manager:
            return self.google_manager.get_players_with_birthdays_today()
        else:
            return self.test_manager.get_players_with_birthdays_today()
    
    def add_player(self, name: str, birthday: str, nickname: str = "", 
                   telegram_id: str = "", team: str = "", notes: str = "") -> bool:
        """Добавляет нового игрока"""
        if self.use_google_sheets and self.google_manager:
            return self.google_manager.add_player(name, birthday, nickname, telegram_id, team, notes)
        else:
            return self.test_manager.add_player(name, birthday, nickname, telegram_id, team, notes)
    
    def get_player_by_telegram_id(self, telegram_id: str) -> Optional[Dict[str, Any]]:
        """Находит игрока по Telegram ID"""
        if self.use_google_sheets and self.google_manager:
            return self.google_manager.get_player_by_telegram_id(telegram_id)
        else:
            return self.test_manager.get_player_by_telegram_id(telegram_id)
    
    def get_status(self) -> str:
        """Возвращает статус менеджера"""
        if self.use_google_sheets:
            return "Google Sheets"
        else:
            return "Тестовые данные"

class TestPlayersManager:
    """Тестовый менеджер данных игроков"""
    
    def __init__(self):
        self.players = TEST_PLAYERS.copy()
    
    def get_all_players(self) -> List[Dict[str, Any]]:
        """Получает всех игроков"""
        return self.players
    
    def get_active_players(self) -> List[Dict[str, Any]]:
        """Получает только активных игроков"""
        return [p for p in self.players if p.get('status', '').lower() == 'активный']
    
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
                        continue
            
            return birthday_players
            
        except Exception as e:
            return []
    
    def add_player(self, name: str, birthday: str, nickname: str = "", 
                   telegram_id: str = "", team: str = "", notes: str = "") -> bool:
        """Добавляет нового игрока (только в тестовой памяти)"""
        try:
            if not name or not birthday:
                return False
            
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
            
            self.players.append(new_player)
            return True
            
        except Exception as e:
            return False
    
    def get_player_by_telegram_id(self, telegram_id: str) -> Optional[Dict[str, Any]]:
        """Находит игрока по Telegram ID"""
        try:
            for player in self.players:
                if player.get('telegram_id') == telegram_id:
                    return player
            return None
            
        except Exception as e:
            return None

# Глобальный экземпляр гибридного менеджера
players_manager = HybridPlayersManager()

def get_years_word(age: int) -> str:
    """Возвращает правильное склонение слова 'год'"""
    if age % 10 == 1 and age % 100 != 11:
        return "год"
    elif age % 10 in [2, 3, 4] and age % 100 not in [12, 13, 14]:
        return "года"
    else:
        return "лет"

def test_hybrid_manager():
    """Тестирует гибридный менеджер игроков"""
    print("🧪 ТЕСТИРОВАНИЕ ГИБРИДНОГО МЕНЕДЖЕРА ИГРОКОВ")
    print("=" * 50)
    
    # Показываем статус
    status = players_manager.get_status()
    print(f"📊 Режим работы: {status}")
    
    # Получаем всех игроков
    all_players = players_manager.get_all_players()
    print(f"📊 Всего игроков: {len(all_players)}")
    
    # Получаем активных игроков
    active_players = players_manager.get_active_players()
    print(f"✅ Активных игроков: {len(active_players)}")
    
    # Проверяем дни рождения сегодня
    birthday_players = players_manager.get_players_with_birthdays_today()
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
    test_hybrid_manager()
