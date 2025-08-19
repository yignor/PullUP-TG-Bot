#!/usr/bin/env python3
"""
Модуль для управления данными игроков через Google Sheets
"""

import os
import json
import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# Загружаем переменные окружения
load_dotenv()

# Получаем переменные окружения
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Настройки Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class PlayersManager:
    """Менеджер данных игроков"""
    
    def __init__(self):
        self.gc = None
        self.spreadsheet = None
        self.players_sheet = None
        self._init_google_sheets()
    
    def _init_google_sheets(self):
        """Инициализация Google Sheets"""
        try:
            if not GOOGLE_SHEETS_CREDENTIALS:
                print("⚠️ GOOGLE_SHEETS_CREDENTIALS не настроен")
                return
            
            if not SPREADSHEET_ID:
                print("⚠️ SPREADSHEET_ID не настроен")
                return
            
            # Парсим JSON credentials
            creds_dict = json.loads(GOOGLE_SHEETS_CREDENTIALS)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            
            self.gc = gspread.authorize(creds)
            self.spreadsheet = self.gc.open_by_key(SPREADSHEET_ID)
            
            # Получаем или создаем лист "Игроки"
            try:
                self.players_sheet = self.spreadsheet.worksheet("Игроки")
                print("✅ Лист 'Игроки' найден")
            except:
                # Создаем новый лист
                self.players_sheet = self.spreadsheet.add_worksheet(
                    title="Игроки", 
                    rows=100, 
                    cols=10
                )
                
                # Создаем заголовки
                headers = [
                    "Имя", "Ник", "Telegram ID", "Дата рождения", 
                    "Статус", "Команда", "Дата добавления", "Примечания"
                ]
                self.players_sheet.update('A1:H1', [headers])
                print("✅ Лист 'Игроки' создан с заголовками")
            
            print("✅ Google Sheets подключен успешно")
                
        except Exception as e:
            print(f"❌ Ошибка инициализации Google Sheets: {e}")
    
    def get_all_players(self) -> List[Dict[str, Any]]:
        """Получает всех игроков из таблицы"""
        try:
            if not self.players_sheet:
                print("❌ Лист 'Игроки' не доступен")
                return []
            
            # Получаем все данные
            all_records = self.players_sheet.get_all_records()
            
            players = []
            for record in all_records:
                # Проверяем обязательные поля
                if record.get('Имя') and record.get('Дата рождения'):
                    player = {
                        'surname': record.get('Фамилия', ''),  # Новый столбец "Фамилия"
                        'name': record.get('Имя', ''),  # Столбец "Имя" (только имя)
                        'nickname': record.get('Ник', ''),
                        'telegram_id': record.get('Telegram ID', ''),
                        'birthday': record.get('Дата рождения', ''),
                        'status': record.get('Статус', 'Активный'),
                        'team': record.get('Команда', ''),
                        'added_date': record.get('Дата добавления', ''),
                        'notes': record.get('Примечания', '')
                    }
                    players.append(player)
            
            print(f"✅ Загружено {len(players)} игроков")
            return players
            
        except Exception as e:
            print(f"❌ Ошибка получения игроков: {e}")
            return []
    
    def get_active_players(self) -> List[Dict[str, Any]]:
        """Получает только активных игроков"""
        all_players = self.get_all_players()
        return [p for p in all_players if p.get('status', '').lower() == 'активный']
    
    def get_players_with_birthdays_today(self) -> List[Dict[str, Any]]:
        """Получает игроков с днями рождения сегодня"""
        try:
            active_players = self.get_active_players()
            today = datetime.datetime.now()
            today_str = today.strftime("%m-%d")
            
            print(f"📅 Проверяем дни рождения на {today_str}")
            print(f"👥 Активных игроков: {len(active_players)}")
            
            birthday_players = []
            for player in active_players:
                birthday = player.get('birthday', '')
                name = player.get('name', 'Unknown')
                surname = player.get('surname', '')
                
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
                            print(f"⚠️ Неизвестный формат даты для {surname} {name}: {birthday}")
                            continue
                        
                        bd_str = bd_date.strftime("%m-%d")
                        print(f"🔍 Проверяем {surname} {name}: {birthday} -> {bd_str} vs {today_str}")
                        
                        if bd_str == today_str:
                            # Вычисляем возраст
                            age = today.year - bd_date.year
                            if today.month < bd_date.month or (today.month == bd_date.month and today.day < bd_date.day):
                                age -= 1
                            
                            player['age'] = age
                            birthday_players.append(player)
                            print(f"🎉 Найден именинник: {surname} {name} ({age} лет)")
                            
                    except ValueError:
                        print(f"⚠️ Неверный формат даты для {surname} {name}: {birthday}")
                        continue
                else:
                    print(f"⚠️ Нет даты рождения для {surname} {name}")
            
            print(f"🎂 Всего именинников сегодня: {len(birthday_players)}")
            return birthday_players
            
        except Exception as e:
            print(f"❌ Ошибка получения дней рождения: {e}")
            return []
    
    def add_player(self, name: str, birthday: str, nickname: str = "", 
                   telegram_id: str = "", team: str = "", notes: str = "", surname: str = "") -> bool:
        """Добавляет нового игрока"""
        try:
            if not self.players_sheet:
                print("❌ Лист 'Игроки' не доступен")
                return False
            
            # Проверяем обязательные поля
            if not name or not birthday:
                print("❌ Имя и дата рождения обязательны")
                return False
            
            # Подготавливаем данные (новая структура)
            row_data = [
                surname,  # Фамилия
                name,     # Имя
                nickname, # Ник
                telegram_id, # Telegram ID
                birthday, # Дата рождения
                "Активный", # Статус
                team,     # Команда
                datetime.datetime.now().strftime("%Y-%m-%d"), # Дата добавления
                notes     # Примечания
            ]
            
            # Добавляем строку
            self.players_sheet.append_row(row_data)
            print(f"✅ Игрок {surname} {name} добавлен")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка добавления игрока: {e}")
            return False
    
    def update_player_status(self, name: str, status: str) -> bool:
        """Обновляет статус игрока"""
        try:
            if not self.players_sheet:
                return False
            
            # Ищем игрока по имени
            all_records = self.players_sheet.get_all_records()
            for i, record in enumerate(all_records, start=2):  # Начинаем с 2 (после заголовков)
                if record.get('Имя') == name:
                    # Обновляем статус
                    self.players_sheet.update(f'E{i}', status)
                    print(f"✅ Статус игрока {name} обновлен на '{status}'")
                    return True
            
            print(f"❌ Игрок {name} не найден")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка обновления статуса: {e}")
            return False
    
    def get_player_by_telegram_id(self, telegram_id: str) -> Optional[Dict[str, Any]]:
        """Находит игрока по Telegram ID"""
        try:
            all_players = self.get_all_players()
            for player in all_players:
                if player.get('telegram_id') == telegram_id:
                    return player
            return None
            
        except Exception as e:
            print(f"❌ Ошибка поиска игрока: {e}")
            return None

# Глобальный экземпляр менеджера
players_manager = PlayersManager()

def get_years_word(age: int) -> str:
    """Возвращает правильное склонение слова 'год'"""
    if age % 10 == 1 and age % 100 != 11:
        return "год"
    elif age % 10 in [2, 3, 4] and age % 100 not in [12, 13, 14]:
        return "года"
    else:
        return "лет"

def test_players_manager():
    """Тестирует функциональность менеджера игроков"""
    print("🧪 ТЕСТИРОВАНИЕ МЕНЕДЖЕРА ИГРОКОВ")
    print("=" * 50)
    
    # Проверяем подключение
    if not players_manager.players_sheet:
        print("❌ Google Sheets не подключен")
        return
    
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
    
    print("✅ Тестирование завершено")

if __name__ == "__main__":
    test_players_manager()
