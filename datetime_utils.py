#!/usr/bin/env python3
"""
Централизованный модуль для работы с датами и временем
Обеспечивает единообразную работу с московским временем во всех системах
"""

import datetime
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

def get_moscow_time():
    """
    Получает текущее время в московском часовом поясе (UTC+3)
    
    Returns:
        datetime.datetime: Текущее время в московском часовом поясе
    """
    try:
        moscow_tz = datetime.timezone(datetime.timedelta(hours=3))
        now = datetime.datetime.now(moscow_tz)
        logger.debug(f"Получено московское время: {now}")
        return now
    except Exception as e:
        logger.error(f"Ошибка получения московского времени: {e}")
        # Fallback к UTC+3
        return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))

def get_moscow_date():
    """
    Получает текущую дату в московском часовом поясе
    
    Returns:
        datetime.date: Текущая дата в московском часовом поясе
    """
    return get_moscow_time().date()

def format_date_for_display(date_obj):
    """
    Форматирует дату для отображения в формате DD.MM.YYYY
    
    Args:
        date_obj: datetime.date или datetime.datetime объект
        
    Returns:
        str: Дата в формате DD.MM.YYYY
    """
    if isinstance(date_obj, datetime.datetime):
        return date_obj.strftime('%d.%m.%Y')
    elif isinstance(date_obj, datetime.date):
        return date_obj.strftime('%d.%m.%Y')
    else:
        raise ValueError(f"Неожиданный тип даты: {type(date_obj)}")

def parse_date_from_string(date_string, format='%d.%m.%Y'):
    """
    Парсит дату из строки
    
    Args:
        date_string (str): Строка с датой
        format (str): Формат даты (по умолчанию DD.MM.YYYY)
        
    Returns:
        datetime.date: Объект даты
        
    Raises:
        ValueError: Если не удается распарсить дату
    """
    try:
        return datetime.datetime.strptime(date_string, format).date()
    except Exception as e:
        logger.error(f"Ошибка парсинга даты '{date_string}': {e}")
        raise ValueError(f"Не удается распарсить дату: {date_string}")

def is_same_date(date1, date2):
    """
    Проверяет, совпадают ли две даты
    
    Args:
        date1: Первая дата (datetime.date, datetime.datetime или str)
        date2: Вторая дата (datetime.date, datetime.datetime или str)
        
    Returns:
        bool: True если даты совпадают
    """
    try:
        # Приводим к datetime.date
        if isinstance(date1, str):
            date1 = parse_date_from_string(date1)
        elif isinstance(date1, datetime.datetime):
            date1 = date1.date()
            
        if isinstance(date2, str):
            date2 = parse_date_from_string(date2)
        elif isinstance(date2, datetime.datetime):
            date2 = date2.date()
            
        return date1 == date2
    except Exception as e:
        logger.error(f"Ошибка сравнения дат: {e}")
        return False

def is_today(date_obj):
    """
    Проверяет, является ли дата сегодняшней
    
    Args:
        date_obj: Дата для проверки (datetime.date, datetime.datetime или str)
        
    Returns:
        bool: True если дата сегодняшняя
    """
    return is_same_date(date_obj, get_moscow_date())

def get_current_time_info():
    """
    Получает подробную информацию о текущем времени
    
    Returns:
        dict: Словарь с информацией о времени
    """
    now = get_moscow_time()
    return {
        'datetime': now,
        'date': now.date(),
        'time': now.time(),
        'hour': now.hour,
        'minute': now.minute,
        'weekday': now.weekday(),
        'weekday_name': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][now.weekday()],
        'formatted_date': format_date_for_display(now),
        'formatted_time': now.strftime('%H:%M:%S'),
        'formatted_datetime': now.strftime('%Y-%m-%d %H:%M:%S')
    }

def log_current_time():
    """
    Логирует текущее время для отладки
    """
    time_info = get_current_time_info()
    logger.info(f"Текущее время (Москва): {time_info['formatted_datetime']}")
    logger.info(f"День недели: {time_info['weekday_name']}")
    return time_info
