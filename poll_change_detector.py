#!/usr/bin/env python3
"""
Система детекции изменений в опросах
Предотвращает ложные обновления и обеспечивает стабильность данных
"""

import os
import json
import hashlib
import datetime
from typing import Dict, List, Optional, Any, Tuple
from datetime_utils import get_moscow_time

class PollChangeDetector:
    """Система детекции изменений в опросах"""
    
    def __init__(self):
        self.history_file = "poll_change_history.json"
        self.false_positives_file = "poll_false_positives.json"
        self.change_history = self._load_history()
        self.false_positives = self._load_false_positives()
    
    def _load_history(self) -> Dict:
        """Загружает историю изменений"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Ошибка загрузки истории изменений: {e}")
        return {}
    
    def _load_false_positives(self) -> Dict:
        """Загружает историю ложных срабатываний"""
        try:
            if os.path.exists(self.false_positives_file):
                with open(self.false_positives_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Ошибка загрузки ложных срабатываний: {e}")
        return {"false_positives": []}
    
    def _save_history(self):
        """Сохраняет историю изменений"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.change_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения истории изменений: {e}")
    
    def _save_false_positives(self):
        """Сохраняет историю ложных срабатываний"""
        try:
            with open(self.false_positives_file, 'w', encoding='utf-8') as f:
                json.dump(self.false_positives, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения ложных срабатываний: {e}")
    
    def _create_poll_hash(self, poll_data: Dict) -> str:
        """Создает хеш данных опроса для отслеживания изменений"""
        # Создаем строку из ключевых данных опроса
        hash_components = [
            poll_data.get('poll_id', ''),
            str(poll_data.get('total_voters', 0)),
            str(poll_data.get('tuesday_count', 0)),
            str(poll_data.get('thursday_count', 0)),
            str(poll_data.get('friday_count', 0)),
            str(sorted(poll_data.get('tuesday_voters', []))),
            str(sorted(poll_data.get('thursday_voters', []))),
            str(sorted(poll_data.get('friday_voters', [])))
        ]
        hash_string = '_'.join(hash_components)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def _create_user_hash(self, user_data: Dict) -> str:
        """Создает хеш пользователя для отслеживания изменений"""
        hash_components = [
            user_data.get('name', ''),
            user_data.get('telegram_id', ''),
            str(sorted(user_data.get('options', [])))
        ]
        hash_string = '_'.join(hash_components)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def detect_changes(self, old_data: Dict, new_data: Dict) -> Dict:
        """Обнаруживает изменения между двумя состояниями опроса"""
        changes = {
            'has_changes': False,
            'added_voters': [],
            'removed_voters': [],
            'changed_voters': [],
            'day_changes': {},
            'confidence_score': 0.0,
            'is_likely_false_positive': False
        }
        
        # Создаем хеши для сравнения
        old_hash = self._create_poll_hash(old_data)
        new_hash = self._create_poll_hash(new_data)
        
        if old_hash == new_hash:
            return changes
        
        changes['has_changes'] = True
        
        # Проверяем изменения по дням
        for day in ['tuesday', 'thursday', 'friday']:
            old_voters = set(old_data.get(f'{day}_voters', []))
            new_voters = set(new_data.get(f'{day}_voters', []))
            
            added = new_voters - old_voters
            removed = old_voters - new_voters
            
            if added or removed:
                changes['day_changes'][day] = {
                    'added': list(added),
                    'removed': list(removed),
                    'added_count': len(added),
                    'removed_count': len(removed)
                }
                changes['added_voters'].extend(added)
                changes['removed_voters'].extend(removed)
        
        # Вычисляем confidence score
        changes['confidence_score'] = self._calculate_confidence_score(changes)
        
        # Проверяем, не является ли это ложным срабатыванием
        changes['is_likely_false_positive'] = self._is_likely_false_positive(changes, old_data, new_data)
        
        return changes
    
    def _calculate_confidence_score(self, changes: Dict) -> float:
        """Вычисляет оценку уверенности в изменениях"""
        score = 0.0
        
        total_added = len(changes['added_voters'])
        total_removed = len(changes['removed_voters'])
        
        # Базовый счетчик на основе количества изменений
        if total_added > 0:
            score += min(total_added * 0.3, 1.0)  # До 1.0 за добавления
        if total_removed > 0:
            score += min(total_removed * 0.4, 1.0)  # До 1.0 за удаления
        
        # Бонус за множественные изменения в одном дне
        for day, day_changes in changes['day_changes'].items():
            if day_changes['added_count'] > 1 or day_changes['removed_count'] > 1:
                score += 0.2
        
        # Штраф за очень маленькие изменения
        if total_added == 1 and total_removed == 0:
            score -= 0.3
        elif total_added == 0 and total_removed == 1:
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _is_likely_false_positive(self, changes: Dict, old_data: Dict, new_data: Dict) -> bool:
        """Определяет, является ли изменение ложным срабатыванием"""
        now = get_moscow_time()
        today_key = now.strftime('%Y-%m-%d')
        
        # Проверяем историю ложных срабатываний за последние 3 дня
        recent_false_positives = []
        for i in range(3):
            check_date = (now - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
            if check_date in self.false_positives.get('false_positives', []):
                recent_false_positives.extend(self.false_positives['false_positives'][check_date])
        
        # Если было много ложных срабатываний, повышаем порог
        if len(recent_false_positives) > 5:
            return changes['confidence_score'] < 0.7
        
        # Проверяем паттерны ложных срабатываний
        for false_positive in recent_false_positives:
            if (false_positive.get('added_count', 0) == changes.get('added_count', 0) and
                false_positive.get('removed_count', 0) == changes.get('removed_count', 0)):
                return True
        
        # Низкая уверенность = возможное ложное срабатывание
        return changes['confidence_score'] < 0.5
    
    def should_apply_changes(self, changes: Dict, poll_id: str) -> bool:
        """Определяет, следует ли применять изменения"""
        if not changes['has_changes']:
            return False
        
        # Если это явно ложное срабатывание, не применяем
        if changes['is_likely_false_positive']:
            print(f"⚠️ Изменения в опросе {poll_id} выглядят как ложное срабатывание")
            print(f"   Confidence score: {changes['confidence_score']:.2f}")
            return False
        
        # Если уверенность высокая, применяем
        if changes['confidence_score'] >= 0.7:
            return True
        
        # Для средней уверенности проверяем дополнительные условия
        if changes['confidence_score'] >= 0.5:
            # Если изменения затрагивают несколько дней, применяем
            if len(changes['day_changes']) > 1:
                return True
            
            # Если много добавлений или удалений, применяем
            if len(changes['added_voters']) > 2 or len(changes['removed_voters']) > 2:
                return True
        
        return False
    
    def log_changes(self, poll_id: str, changes: Dict, applied: bool):
        """Логирует изменения в опросе"""
        now = get_moscow_time()
        timestamp = now.isoformat()
        today_key = now.strftime('%Y-%m-%d')
        
        change_entry = {
            'timestamp': timestamp,
            'poll_id': poll_id,
            'changes': changes,
            'applied': applied,
            'confidence_score': changes.get('confidence_score', 0.0),
            'is_false_positive': changes.get('is_likely_false_positive', False)
        }
        
        # Добавляем в историю
        if today_key not in self.change_history:
            self.change_history[today_key] = []
        
        self.change_history[today_key].append(change_entry)
        
        # Ограничиваем размер истории (последние 30 дней)
        cutoff_date = (now - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        self.change_history = {k: v for k, v in self.change_history.items() if k >= cutoff_date}
        
        # Если это ложное срабатывание, добавляем в соответствующий список
        if changes.get('is_likely_false_positive', False):
            if today_key not in self.false_positives:
                self.false_positives[today_key] = []
            
            self.false_positives[today_key].append({
                'timestamp': timestamp,
                'poll_id': poll_id,
                'added_count': len(changes.get('added_voters', [])),
                'removed_count': len(changes.get('removed_voters', []))
            })
            
            # Ограничиваем размер ложных срабатываний
            self.false_positives = {k: v for k, v in self.false_positives.items() if k >= cutoff_date}
            self._save_false_positives()
        
        self._save_history()
    
    def get_change_statistics(self, days: int = 7) -> Dict:
        """Получает статистику изменений за указанное количество дней"""
        now = get_moscow_time()
        stats = {
            'total_changes': 0,
            'applied_changes': 0,
            'false_positives': 0,
            'average_confidence': 0.0,
            'day_breakdown': {}
        }
        
        total_confidence = 0.0
        confidence_count = 0
        
        for i in range(days):
            check_date = (now - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
            
            if check_date in self.change_history:
                day_changes = self.change_history[check_date]
                stats['total_changes'] += len(day_changes)
                
                day_stats = {
                    'changes': len(day_changes),
                    'applied': 0,
                    'false_positives': 0,
                    'avg_confidence': 0.0
                }
                
                day_confidence = 0.0
                day_confidence_count = 0
                
                for change in day_changes:
                    if change.get('applied', False):
                        stats['applied_changes'] += 1
                        day_stats['applied'] += 1
                    
                    if change.get('is_false_positive', False):
                        stats['false_positives'] += 1
                        day_stats['false_positives'] += 1
                    
                    confidence = change.get('confidence_score', 0.0)
                    if confidence > 0:
                        total_confidence += confidence
                        confidence_count += 1
                        day_confidence += confidence
                        day_confidence_count += 1
                
                if day_confidence_count > 0:
                    day_stats['avg_confidence'] = day_confidence / day_confidence_count
                
                stats['day_breakdown'][check_date] = day_stats
        
        if confidence_count > 0:
            stats['average_confidence'] = total_confidence / confidence_count
        
        return stats
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Очищает старые данные"""
        now = get_moscow_time()
        cutoff_date = (now - datetime.timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
        
        # Очищаем историю изменений
        self.change_history = {k: v for k, v in self.change_history.items() if k >= cutoff_date}
        
        # Очищаем ложные срабатывания
        self.false_positives = {k: v for k, v in self.false_positives.items() if k >= cutoff_date}
        
        self._save_history()
        self._save_false_positives()
        
        print(f"✅ Очищены данные старше {days_to_keep} дней")
