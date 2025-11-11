#!/usr/bin/env python3
"""
Универсальная система защиты от дублирования
Использует лист "Сервисный" в Google таблице для централизованного контроля
"""

import os
import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from datetime_utils import get_moscow_time

SERVICE_HEADER = [
    "ТИП ДАННЫХ",
    "ДАТА И ВРЕМЯ",
    "УНИКАЛЬНЫЙ КЛЮЧ",
    "СТАТУС",
    "ДОПОЛНИТЕЛЬНЫЕ ДАННЫЕ",
    "ССЫЛКА",
    "ИД СОРЕВНОВАНИЯ",
    "ИД КОМАНДЫ",
    "АЛЬТЕРНАТИВНОЕ ИМЯ",
    "НАСТРОЙКИ",
    "GAME ID",
    "GAME DATE",
    "GAME TIME",
    "АРЕНА",
    "TEAM A ID",
    "TEAM B ID",
]

# Индексы колонок (0-based)
TYPE_COL = 0
DATE_COL = 1
KEY_COL = 2
STATUS_COL = 3
ADDITIONAL_DATA_COL = 4
LINK_COL = 5
COMP_ID_COL = 6
TEAM_ID_COL = 7
ALT_NAME_COL = 8
CONFIG_COL = 9
GAME_ID_COL = 10
GAME_DATE_COL = 11
GAME_TIME_COL = 12
ARENA_COL = 13
TEAM_A_ID_COL = 14
TEAM_B_ID_COL = 15

END_COLUMN_LETTER = chr(ord('A') + len(SERVICE_HEADER) - 1)
# Загружаем переменные окружения
load_dotenv()

# Переменные окружения
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"  # Тестовый режим

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
                    self._ensure_service_header()
                except gspread.WorksheetNotFound:
                    print("❌ Лист 'Сервисный' не найден")
                    print("💡 Запустите create_service_sheet.py для создания листа")
            else:
                print("❌ SPREADSHEET_ID не настроен")
                
        except Exception as e:
            print(f"❌ Ошибка инициализации Google Sheets: {e}")
    
    def _ensure_service_header(self):
        """Убеждаемся, что заголовок содержит обязательные колонки"""
        worksheet = self._get_service_worksheet(raw=True)
        if not worksheet:
            return
        
        try:
            header = worksheet.row_values(1)
            if not header:
                worksheet.update(f'A1:{END_COLUMN_LETTER}1', [SERVICE_HEADER])
                return
            
            desired_length = len(SERVICE_HEADER)
            if len(header) < desired_length:
                header.extend([""] * (desired_length - len(header)))
            
            updated = False
            for index, expected in enumerate(SERVICE_HEADER):
                if not header[index]:
                    header[index] = expected
                    updated = True
            
            if updated:
                worksheet.update(f'A1:{END_COLUMN_LETTER}1', [header])
        except Exception as e:
            print(f"⚠️ Не удалось обновить заголовок сервисного листа: {e}")

    def _get_service_worksheet(self, raw: bool = False):
        """Получает лист 'Сервисный'"""
        if not self.spreadsheet:
            print("❌ Google Sheets не инициализирован")
            return None
            
        if not self.service_worksheet:
            try:
                self.service_worksheet = self.spreadsheet.worksheet("Сервисный")
            except gspread.WorksheetNotFound:
                print("❌ Лист 'Сервисный' не найден")
                return None
        
        if not raw:
            self._ensure_service_header()
        return self.service_worksheet
    
    def _create_unique_key(self, data_type: str, identifier: str, **kwargs) -> str:
        """Создает уникальный ключ для записи"""
        # Базовый ключ
        base_key = f"{data_type}_{identifier}"
        
        # Добавляем префикс TEST_ в тестовом режиме
        if TEST_MODE:
            base_key = f"TEST_{base_key}"
        
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
    
    def add_record(
        self,
        data_type: str,
        identifier: str,
        status: str = "АКТИВЕН",
        additional_data: str = "",
        game_link: str = "",
        comp_id: Optional[int] = None,
        team_id: Optional[int] = None,
        alt_name: str = "",
        settings: str = "",
        game_id: Optional[int] = None,
        game_date: str = "",
        game_time: str = "",
        arena: str = "",
        team_a_id: Optional[int] = None,
        team_b_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
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
                additional_data,
                game_link,
                str(comp_id) if comp_id is not None else "",
                str(team_id) if team_id is not None else "",
                alt_name,
                settings,
                str(game_id) if game_id is not None else "",
                game_date,
                game_time,
                arena,
                str(team_a_id) if team_a_id is not None else "",
                str(team_b_id) if team_b_id is not None else "",
            ]
            
            if len(new_record) < len(SERVICE_HEADER):
                new_record.extend([""] * (len(SERVICE_HEADER) - len(new_record)))
            
            # Добавляем запись в начало (под заголовком)
            worksheet.insert_row(new_record, index=2)
            
            print(f"✅ Запись добавлена: {data_type} - {identifier}")
            
            return {
                'success': True,
                'unique_key': unique_key,
                'row': 2
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def find_game_link_for_today(self, team1: str, team2: str) -> Optional[str]:
        """Ищет ссылку на игру для сегодняшней даты"""
        worksheet = self._get_service_worksheet()
        if not worksheet:
            print("❌ Лист 'Сервисный' не найден")
            return None
        
        try:
            from datetime_utils import get_moscow_time
            today = get_moscow_time().strftime('%d.%m.%Y')
            
            # Получаем все данные
            all_data = worksheet.get_all_values()
            
            print(f"🔍 Ищем ссылку на игру для {today}: {team1} vs {team2}")
            
            # Ищем записи типа АНОНС_ИГРА за сегодня
            for row in all_data:
                if (len(row) > LINK_COL and 
                    row[TYPE_COL] == "АНОНС_ИГРА" and 
                    today in row[DATE_COL] and  # Дата в колонке B
                    row[LINK_COL]):  # Ссылка в колонке F
                    
                    # Более точный поиск команд
                    unique_key = row[2].lower()
                    team1_lower = team1.lower()
                    team2_lower = team2.lower()
                    
                    # Нормализуем названия команд для сравнения
                    def _normalize_team_name(name: str) -> str:
                        import re as _re
                        return _re.sub(r"[\W_]+", "", name.lower())

                    def _build_variants(name: str) -> Set[str]:
                        variants: Set[str] = set()
                        if not name:
                            return variants
                        lowered = name.lower()
                        variants.add(lowered)
                        variants.add(_normalize_team_name(name))
                        for part in lowered.replace('-', ' ').replace('_', ' ').split():
                            if len(part) > 2:
                                variants.add(part)
                        return {variant for variant in variants if variant}

                    team1_variants = _build_variants(team1)
                    team2_variants = _build_variants(team2)
                    unique_key_lower = unique_key.lower()
                    unique_key_normalized = _normalize_team_name(unique_key)

                    def _contains_variant(variants: Set[str]) -> bool:
                        for variant in variants:
                            if len(variant) <= 2:
                                continue
                            if variant in unique_key_lower or variant in unique_key_normalized:
                                return True
                        return False

                    team1_found = _contains_variant(team1_variants)
                    team2_found = _contains_variant(team2_variants)

                    # Если найдены обе команды — возвращаем ссылку
                    if team1_found and team2_found:
                        game_link = row[LINK_COL]
                        print(f"✅ Найдена точная ссылка в сервисном листе: {game_link}")
                        print(f"   По ключу: {row[2]}")
                        print(f"   Для команд: {team1} vs {team2}")
                        return game_link
            
            print(f"❌ Ссылка на игру не найдена в сервисном листе")
            return None
            
        except Exception as e:
            print(f"❌ Ошибка поиска ссылки в сервисном листе: {e}")
            return None
    
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
                        'type': row[TYPE_COL] if len(row) > TYPE_COL else '',
                        'date': row[DATE_COL] if len(row) > DATE_COL else '',
                        'unique_key': row[KEY_COL] if len(row) > KEY_COL else '',
                        'status': row[STATUS_COL] if len(row) > STATUS_COL else '',
                        'additional_data': row[ADDITIONAL_DATA_COL] if len(row) > ADDITIONAL_DATA_COL else '',
                        'link': row[LINK_COL] if len(row) > LINK_COL else '',
                        'comp_id': row[COMP_ID_COL] if len(row) > COMP_ID_COL else '',
                        'team_id': row[TEAM_ID_COL] if len(row) > TEAM_ID_COL else '',
                        'alt_name': row[ALT_NAME_COL] if len(row) > ALT_NAME_COL else '',
                        'settings': row[CONFIG_COL] if len(row) > CONFIG_COL else '',
                        'game_id': row[GAME_ID_COL] if len(row) > GAME_ID_COL else '',
                        'game_date': row[GAME_DATE_COL] if len(row) > GAME_DATE_COL else '',
                        'game_time': row[GAME_TIME_COL] if len(row) > GAME_TIME_COL else '',
                        'arena': row[ARENA_COL] if len(row) > ARENA_COL else '',
                        'team_a_id': row[TEAM_A_ID_COL] if len(row) > TEAM_A_ID_COL else '',
                        'team_b_id': row[TEAM_B_ID_COL] if len(row) > TEAM_B_ID_COL else ''
                    })
            
            return records
            
        except Exception as e:
            print(f"❌ Ошибка получения записей: {e}")
            return []
    
    def get_game_record(self, data_type: str, game_id: Any) -> Optional[Dict[str, Any]]:
        """Возвращает запись об игре по GameID"""
        worksheet = self._get_service_worksheet()
        if not worksheet:
            return None
        
        try:
            game_id_str = str(game_id)
            all_data = worksheet.get_all_values()
            for row_index, row in enumerate(all_data[1:], start=2):
                if len(row) <= max(GAME_ID_COL, TYPE_COL):
                    continue
                if row[TYPE_COL].upper() != data_type.upper():
                    continue
                if row[GAME_ID_COL] == game_id_str:
                    return {
                        'row': row_index,
                        'type': row[TYPE_COL],
                        'date': row[DATE_COL],
                        'unique_key': row[KEY_COL],
                        'status': row[STATUS_COL],
                        'additional_data': row[ADDITIONAL_DATA_COL],
                        'link': row[LINK_COL],
                        'comp_id': row[COMP_ID_COL],
                        'team_id': row[TEAM_ID_COL],
                        'alt_name': row[ALT_NAME_COL],
                        'settings': row[CONFIG_COL],
                        'game_id': row[GAME_ID_COL],
                        'game_date': row[GAME_DATE_COL],
                        'game_time': row[GAME_TIME_COL],
                        'arena': row[ARENA_COL],
                        'team_a_id': row[TEAM_A_ID_COL],
                        'team_b_id': row[TEAM_B_ID_COL],
                    }
            return None
        except Exception as e:
            print(f"⚠️ Ошибка поиска записи игры: {e}")
            return None
    
    def upsert_game_record(
        self,
        data_type: str,
        identifier: str,
        status: str,
        additional_data: str,
        game_link: str,
        comp_id: Optional[int],
        team_id: Optional[int],
        alt_name: str,
        settings: str,
        game_id: Any,
        game_date: str,
        game_time: str,
        arena: str,
        team_a_id: Optional[int],
        team_b_id: Optional[int],
        **kwargs,
    ) -> Dict[str, Any]:
        """Создает или обновляет запись об игре"""
        worksheet = self._get_service_worksheet()
        if not worksheet:
            return {'success': False, 'error': 'Лист не найден'}
        
        try:
            game_id_str = str(game_id) if game_id is not None else ""
            existing = self.get_game_record(data_type, game_id_str) if game_id_str else None
            unique_key = existing.get('unique_key') if existing else self._create_unique_key(data_type, identifier, **kwargs)
            current_datetime = self._get_current_datetime()
            
            row_values = [
                data_type.upper(),
                current_datetime,
                unique_key,
                status,
                additional_data,
                game_link,
                str(comp_id) if comp_id is not None else "",
                str(team_id) if team_id is not None else "",
                alt_name,
                settings,
                game_id_str,
                game_date,
                game_time,
                arena,
                str(team_a_id) if team_a_id is not None else "",
                str(team_b_id) if team_b_id is not None else "",
            ]
            
            if existing:
                row_index = existing['row']
                worksheet.update(f"A{row_index}:{END_COLUMN_LETTER}{row_index}", [row_values])
                print(f"🔄 Обновлена запись {data_type} для GameID {game_id_str}")
                return {'success': True, 'action': 'updated', 'row': row_index}
            
            result = self.add_record(
                data_type=data_type,
                identifier=identifier,
                status=status,
                additional_data=additional_data,
                game_link=game_link,
                comp_id=comp_id,
                team_id=team_id,
                alt_name=alt_name,
                settings=settings,
                game_id=game_id,
                game_date=game_date,
                game_time=game_time,
                arena=arena,
                team_a_id=team_a_id,
                team_b_id=team_b_id,
                **kwargs,
            )
            result['action'] = 'inserted' if result.get('success') else 'error'
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
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
            all_data = worksheet.get_all_values()
            current_datetime = get_moscow_time()
            rows_to_delete: List[int] = []
            
            for row_index, row in enumerate(all_data[1:], start=2):
                if len(row) <= max(DATE_COL, TYPE_COL):
                    continue
                
                row_type = row[TYPE_COL].upper() if len(row) > TYPE_COL else ''
                if row_type != data_type.upper():
                    continue
                
                date_value = row[DATE_COL]
                if not date_value:
                    continue
                
                try:
                    from datetime import datetime as dt
                    record_date = dt.strptime(date_value, '%d.%m.%Y %H:%M')
                except ValueError:
                    continue
                
                record_date = record_date.replace(tzinfo=current_datetime.tzinfo)
                age_days = (current_datetime - record_date).days
                
                if age_days > days_old:
                    rows_to_delete.append(row_index)
            
            for row_index in reversed(rows_to_delete):
                worksheet.delete_rows(row_index)
            
            print(f"✅ Очищено {len(rows_to_delete)} старых записей типа {data_type}")
            
            return {
                'success': True,
                'cleaned_count': len(rows_to_delete),
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

    def cleanup_expired_records(self, max_age_days: int = 30) -> Dict[str, Any]:
        """Удаляет все записи старше указанного количества дней"""
        worksheet = self._get_service_worksheet()
        if not worksheet:
            return {'success': False, 'error': 'Лист не найден'}
        
        try:
            all_data = worksheet.get_all_values()
            if not all_data:
                return {'success': True, 'cleaned_count': 0, 'details': []}
            
            current_datetime = get_moscow_time()
            rows_to_delete: List[Tuple[int, str]] = []
            
            for row_index, row in enumerate(all_data[1:], start=2):
                if len(row) <= DATE_COL:
                    continue
                
                date_value = row[DATE_COL]
                if not date_value:
                    continue
                
                try:
                    from datetime import datetime as dt
                    record_date = dt.strptime(date_value, '%d.%m.%Y %H:%M')
                except ValueError:
                    continue
                
                record_date = record_date.replace(tzinfo=current_datetime.tzinfo)
                age_days = (current_datetime - record_date).days
                
                if age_days > max_age_days:
                    record_type = row[TYPE_COL] if len(row) > TYPE_COL else ''
                    rows_to_delete.append((row_index, record_type))
            
            for row_index, _ in reversed(rows_to_delete):
                worksheet.delete_rows(row_index)
            
            print(f"✅ Очищено {len(rows_to_delete)} записей старше {max_age_days} дней")
            
            return {
                'success': True,
                'cleaned_count': len(rows_to_delete),
                'details': rows_to_delete
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _parse_ids(cell_value: str) -> List[int]:
        """Парсит числовые ID из значения ячейки"""
        if not cell_value:
            return []
        
        normalized = cell_value.replace('\n', ',').replace(';', ',')
        parts = [part.strip() for part in normalized.split(',') if part.strip()]
        ids: List[int] = []
        for part in parts:
            matches = re.findall(r'\d+', part)
            for match in matches:
                try:
                    ids.append(int(match))
                except ValueError:
                    continue
        return ids
    
    @staticmethod
    def _parse_json_config(cell_value: str) -> Dict[str, Any]:
        """Парсит JSON из ячейки конфигурации"""
        if not cell_value:
            return {}
        if isinstance(cell_value, dict):
            return cell_value
        try:
            return json.loads(cell_value)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"⚠️ Некорректный JSON в конфигурации сервисного листа: {e}")
            return {}

    def get_full_config(self) -> Dict[str, Any]:
        """Возвращает полную конфигурацию, хранящуюся в сервисном листе"""
        worksheet = self._get_service_worksheet()
        if not worksheet:
            return {
                'comp_ids': set(),
                'team_ids': set(),
                'teams': {},
                'training_polls': [],
                'fallback_sources': []
            }
        
        try:
            all_data = worksheet.get_all_values()
            if not all_data:
                return {
                    'comp_ids': set(),
                    'team_ids': set(),
                    'teams': {},
                    'training_polls': [],
                    'fallback_sources': []
                }
            
            comp_ids: Set[int] = set()
            team_ids: Set[int] = set()
            teams: Dict[int, Dict[str, Any]] = {}
            training_polls: List[Dict[str, Any]] = []
            fallback_sources: List[Dict[str, Any]] = []
            
            for row in all_data[1:]:
                if len(row) <= TYPE_COL:
                    continue
                
                row_type = (row[TYPE_COL] or "").strip().upper()
                if not row_type:
                    continue
                
                row_comp_ids = self._parse_ids(row[COMP_ID_COL]) if len(row) > COMP_ID_COL else []
                row_team_ids = self._parse_ids(row[TEAM_ID_COL]) if len(row) > TEAM_ID_COL else []
                alt_name = (row[ALT_NAME_COL] or "").strip() if len(row) > ALT_NAME_COL else ""
                config_payload = self._parse_json_config(row[CONFIG_COL] if len(row) > CONFIG_COL else "")
                
                if row_type in {"CONFIG", "CONFIG_IDS", "CONFIG_ROW", "CONFIG_COMP", "COMP_CONFIG"}:
                    comp_ids.update(row_comp_ids)
                
                if row_type in {"CONFIG", "CONFIG_IDS", "CONFIG_ROW", "CONFIG_TEAM", "TEAM_CONFIG"}:
                    comp_ids.update(row_comp_ids)
                    for team_id in row_team_ids:
                        team_ids.add(team_id)
                        team_entry = teams.setdefault(team_id, {"alt_name": None, "comp_ids": set(), "metadata": {}})
                        if alt_name:
                            team_entry["alt_name"] = alt_name
                        if row_comp_ids:
                            team_entry["comp_ids"].update(row_comp_ids)
                        if config_payload:
                            team_entry["metadata"].update(config_payload)
                
                elif row_type in {"TRAINING_POLL", "TRAINING_CONFIG"}:
                    training_entry = {
                        "title": config_payload.get("title") or (row[ADDITIONAL_DATA_COL] if len(row) > ADDITIONAL_DATA_COL else ""),
                        "weekday": config_payload.get("weekday"),
                        "time": config_payload.get("time") or (row[STATUS_COL] if len(row) > STATUS_COL else ""),
                        "location": config_payload.get("location") or (row[LINK_COL] if len(row) > LINK_COL else ""),
                        "topic_id": config_payload.get("topic_id"),
                        "metadata": config_payload
                    }
                    training_polls.append(training_entry)
                
                elif row_type in {"FALLBACK", "FALLBACK_SOURCE", "FALLBACK_CONFIG"}:
                    fallback_entry = {
                        "name": config_payload.get("name") or alt_name or (row[ADDITIONAL_DATA_COL] if len(row) > ADDITIONAL_DATA_COL else ""),
                        "url": config_payload.get("url") or (row[LINK_COL] if len(row) > LINK_COL else ""),
                        "metadata": config_payload
                    }
                    fallback_sources.append(fallback_entry)
                
                else:
                    # Для прочих типов сохраняем ID, если они указаны
                    if row_comp_ids:
                        comp_ids.update(row_comp_ids)
                    if row_team_ids:
                        for team_id in row_team_ids:
                            team_ids.add(team_id)
                            team_entry = teams.setdefault(team_id, {"alt_name": None, "comp_ids": set(), "metadata": {}})
                            if alt_name:
                                team_entry["alt_name"] = alt_name
                            if config_payload:
                                team_entry["metadata"].update(config_payload)
            
            # Преобразуем множества comp_ids в списки для команд
            for team in teams.values():
                if isinstance(team.get("comp_ids"), set):
                    team["comp_ids"] = sorted(team["comp_ids"])
                if not team.get("metadata"):
                    team.pop("metadata", None)
                if not team.get("alt_name"):
                    team.pop("alt_name", None)
            
            return {
                'comp_ids': comp_ids,
                'team_ids': team_ids,
                'teams': teams,
                'training_polls': training_polls,
                'fallback_sources': fallback_sources
            }
        except Exception as e:
            print(f"⚠️ Ошибка чтения конфигурации из сервисного листа: {e}")
            return {
                'comp_ids': set(),
                'team_ids': set(),
                'teams': {},
                'training_polls': [],
                'fallback_sources': []
            }

    def get_config_ids(self) -> Dict[str, Any]:
        """Совместимая обёртка вокруг полной конфигурации"""
        full_config = self.get_full_config()
        return {
            'comp_ids': sorted(full_config.get('comp_ids', set())),
            'team_ids': sorted(full_config.get('team_ids', set())),
            'teams': full_config.get('teams', {}),
            'training_polls': full_config.get('training_polls', []),
            'fallback_sources': full_config.get('fallback_sources', [])
        }

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
