#!/usr/bin/env python3
"""
Универсальная система защиты от дублирования
Использует лист "Сервисный" в Google таблице для централизованного контроля
"""

import os
import json
import datetime
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from datetime_utils import get_moscow_time

# Загружаем переменные окружения
load_dotenv()

# Переменные окружения
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Настройки Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class EnhancedDuplicateProtection:
    """Универсальная система защиты от дублирования"""
    
    def __init__(self):
        self.gc = None
        self.spreadsheet = None
        self.service_worksheet = None
        self._init_google_sheets()
    
    def _init_google_sheets(self):
        """Инициализация Google Sheets"""
        try:
            if not GOOGLE_SHEETS_CREDENTIALS:
                print("❌ GOOGLE_SHEETS_CREDENTIALS не настроен")
                return
            
            creds_dict = json.loads(GOOGLE_SHEETS_CREDENTIALS)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            
            self.gc = gspread.authorize(creds)
            
            if SPREADSHEET_ID:
                self.spreadsheet = self.gc.open_by_key(SPREADSHEET_ID)
                print("✅ Google Sheets подключен успешно")
                
                # Получаем лист "Сервисный"
                try:
                    self.service_worksheet = self.spreadsheet.worksheet("Сервисный")
                    print("✅ Лист 'Сервисный' подключен")
                except gspread.WorksheetNotFound:
                    print("❌ Лист 'Сервисный' не найден")
                    print("💡 Запустите create_service_sheet.py для создания листа")
            else:
                print("❌ SPREADSHEET_ID не настроен")
                
        except Exception as e:
            print(f"❌ Ошибка инициализации Google Sheets: {e}")
    
    def _get_service_worksheet(self):
        """Получает лист 'Сервисный'"""
        if not self.service_worksheet:
            try:
                self.service_worksheet = self.spreadsheet.worksheet("Сервисный")
            except gspread.WorksheetNotFound:
                print("❌ Лист 'Сервисный' не найден")
                return None
        return self.service_worksheet
    
    def _create_unique_key(self, data_type: str, identifier: str, **kwargs) -> str:
        """Создает уникальный ключ для записи"""
        # Базовый ключ
        base_key = f"{data_type}_{identifier}"
        
        # Добавляем дополнительные параметры для уникальности
        if kwargs:
            additional = "_".join([f"{k}_{v}" for k, v in sorted(kwargs.items())])
            base_key = f"{base_key}_{additional}"
        
        return base_key
    
    def _get_current_datetime(self) -> str:
        """Получает текущую дату и время в московском часовом поясе"""
        now = get_moscow_time()
        return now.strftime('%d.%m.%Y %H:%M')
    
    def check_duplicate(self, data_type: str, identifier: str, **kwargs) -> Dict[str, Any]:
        """Проверяет существование дубликата"""
        worksheet = self._get_service_worksheet()
        if not worksheet:
            return {'exists': False, 'error': 'Лист не найден'}
        
        try:
            # Создаем уникальный ключ
            unique_key = self._create_unique_key(data_type, identifier, **kwargs)
            
            # Получаем все данные
            all_data = worksheet.get_all_values()
            
            # Ищем дубликат по уникальному ключу (колонка C) И по типу данных (колонка A)
            for i, row in enumerate(all_data):
                if (len(row) >= 3 and 
                    row[0].upper() == data_type.upper() and 
                    row[2] == unique_key):
                    return {
                        'exists': True,
                        'row': i + 1,
                        'data': row,
                        'unique_key': unique_key
                    }
            
            # Дополнительная проверка: ищем по типу и идентификатору
            for i, row in enumerate(all_data):
                if (len(row) >= 3 and 
                    row[0].upper() == data_type.upper() and 
                    identifier in row[2]):
                    return {
                        'exists': True,
                        'row': i + 1,
                        'data': row,
                        'unique_key': row[2],
                        'reason': 'Найден по типу и идентификатору'
                    }
            
            return {'exists': False, 'unique_key': unique_key}
            
        except Exception as e:
            return {'exists': False, 'error': str(e)}
    
    def add_record(self, data_type: str, identifier: str, status: str = "АКТИВЕН", 
                   additional_data: str = "", **kwargs) -> Dict[str, Any]:
        """Добавляет новую запись в сервисный лист"""
        worksheet = self._get_service_worksheet()
        if not worksheet:
            return {'success': False, 'error': 'Лист не найден'}
        
        try:
            # Проверяем дубликат
            duplicate_check = self.check_duplicate(data_type, identifier, **kwargs)
            
            if duplicate_check.get('exists'):
                return {
                    'success': False,
                    'error': 'Дубликат уже существует',
                    'duplicate_info': duplicate_check
                }
            
            # Создаем уникальный ключ
            unique_key = duplicate_check.get('unique_key') or self._create_unique_key(data_type, identifier, **kwargs)
            
            # Получаем текущую дату
            current_datetime = self._get_current_datetime()
            
            # Создаем новую запись
            new_record = [
                data_type.upper(),
                current_datetime,
                unique_key,
                status,
                additional_data
            ]
            
            # Добавляем запись в конец
            worksheet.append_row(new_record)
            
            print(f"✅ Запись добавлена: {data_type} - {identifier}")
            
            return {
                'success': True,
                'unique_key': unique_key,
                'row': len(worksheet.get_all_values())
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_record_status(self, unique_key: str, new_status: str) -> Dict[str, Any]:
        """Обновляет статус существующей записи"""
        worksheet = self._get_service_worksheet()
        if not worksheet:
            return {'success': False, 'error': 'Лист не найден'}
        
        try:
            # Получаем все данные
            all_data = worksheet.get_all_values()
            
            # Ищем запись по уникальному ключу
            for i, row in enumerate(all_data):
                if len(row) >= 3 and row[2] == unique_key:
                    # Обновляем статус (колонка D)
                    worksheet.update(values=[[new_status]], range_name=f'D{i+1}')
                    
                    print(f"✅ Статус обновлен: {unique_key} -> {new_status}")
                    
                    return {
                        'success': True,
                        'row': i + 1,
                        'old_status': row[3] if len(row) > 3 else '',
                        'new_status': new_status
                    }
            
            return {'success': False, 'error': 'Запись не найдена'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_records_by_type(self, data_type: str) -> List[Dict[str, Any]]:
        """Получает все записи определенного типа"""
        worksheet = self._get_service_worksheet()
        if not worksheet:
            return []
        
        try:
            all_data = worksheet.get_all_values()
            records = []
            
            for i, row in enumerate(all_data):
                if len(row) >= 1 and row[0].upper() == data_type.upper():
                    records.append({
                        'row': i + 1,
                        'type': row[0],
                        'date': row[1] if len(row) > 1 else '',
                        'unique_key': row[2] if len(row) > 2 else '',
                        'status': row[3] if len(row) > 3 else '',
                        'additional_data': row[4] if len(row) > 4 else ''
                    })
            
            return records
            
        except Exception as e:
            print(f"❌ Ошибка получения записей: {e}")
            return []
    
    def get_active_records(self, data_type: str) -> List[Dict[str, Any]]:
        """Получает активные записи определенного типа"""
        all_records = self.get_records_by_type(data_type)
        return [record for record in all_records if record.get('status') == 'АКТИВЕН']
    
    def cleanup_old_records(self, data_type: str, days_old: int = 30) -> Dict[str, Any]:
        """Очищает старые записи определенного типа"""
        worksheet = self._get_service_worksheet()
        if not worksheet:
            return {'success': False, 'error': 'Лист не найден'}
        
        try:
            all_records = self.get_records_by_type(data_type)
            current_date = datetime.datetime.now()
            cleaned_count = 0
            
            for record in all_records:
                try:
                    # Парсим дату из записи
                    record_date = datetime.datetime.strptime(record['date'], '%d.%m.%Y %H:%M')
                    days_diff = (current_date - record_date).days
                    
                    if days_diff > days_old:
                        # Удаляем старую запись
                        worksheet.delete_rows(record['row'])
                        cleaned_count += 1
                        
                except ValueError:
                    # Пропускаем записи с некорректной датой
                    continue
            
            print(f"✅ Очищено {cleaned_count} старых записей типа {data_type}")
            
            return {
                'success': True,
                'cleaned_count': cleaned_count,
                'data_type': data_type
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получает статистику по всем типам записей"""
        worksheet = self._get_service_worksheet()
        if not worksheet:
            return {'error': 'Лист не найден'}
        
        try:
            all_data = worksheet.get_all_values()
            stats = {}
            
            for row in all_data:
                if len(row) >= 1 and row[0]:
                    data_type = row[0]
                    if data_type.startswith('===') or data_type.startswith('ТИП ДАННЫХ'):
                        continue
                    
                    if data_type not in stats:
                        stats[data_type] = {'total': 0, 'active': 0, 'completed': 0}
                    
                    stats[data_type]['total'] += 1
                    
                    if len(row) >= 4:
                        status = row[3]
                        if status == 'АКТИВЕН':
                            stats[data_type]['active'] += 1
                        elif status in ['ЗАВЕРШЕН', 'ОТПРАВЛЕН', 'ОБРАБОТАН', 'ОТПРАВЛЕНО']:
                            stats[data_type]['completed'] += 1
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}

# Глобальный экземпляр для использования в других модулях
duplicate_protection = EnhancedDuplicateProtection()

def test_duplicate_protection():
    """Тестирует систему защиты от дублирования"""
    print("🧪 ТЕСТИРОВАНИЕ УСИЛЕННОЙ СИСТЕМЫ ЗАЩИТЫ ОТ ДУБЛИРОВАНИЯ")
    print("=" * 70)
    
    if not duplicate_protection.gc:
        print("❌ Google Sheets не подключен")
        return False
    
    if not duplicate_protection.service_worksheet:
        print("❌ Лист 'Сервисный' не найден")
        return False
    
    print("✅ Система готова к тестированию")
    
    # Тест 1: Проверка дубликата
    print(f"\n🧪 ТЕСТ 1: Проверка существующего дубликата")
    duplicate_check = duplicate_protection.check_duplicate("ОПРОС_ТРЕНИРОВКА", "5312150808802889330")
    print(f"   Результат: {duplicate_check}")
    
    # Тест 2: Добавление новой записи
    print(f"\n🧪 ТЕСТ 2: Добавление новой записи")
    new_record = duplicate_protection.add_record(
        "ТЕСТ_ЗАПИСЬ", 
        "test_001", 
        "АКТИВЕН", 
        "Тестовая запись для проверки"
    )
    print(f"   Результат: {new_record}")
    
    # Тест 3: Получение статистики
    print(f"\n🧪 ТЕСТ 3: Получение статистики")
    stats = duplicate_protection.get_statistics()
    print(f"   Статистика: {stats}")
    
    # Тест 4: Получение записей по типу
    print(f"\n🧪 ТЕСТ 4: Получение записей по типу")
    training_records = duplicate_protection.get_records_by_type("ОПРОС_ТРЕНИРОВКА")
    print(f"   Записи опросов тренировок: {len(training_records)}")
    
    print(f"\n✅ Тестирование завершено")
    return True

if __name__ == "__main__":
    test_duplicate_protection()
