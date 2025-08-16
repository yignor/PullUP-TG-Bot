#!/usr/bin/env python3
"""
Общий модуль для управления уведомлениями
Устраняет дублирование функционала уведомлений между разными модулями
"""

import os
import logging
from typing import Dict, List, Optional, Any, Set
from telegram import Bot

# Настройка логирования
logger = logging.getLogger(__name__)

class NotificationManager:
    """Общий менеджер уведомлений"""
    
    def __init__(self):
        self.bot = None
        self.chat_id = os.getenv('CHAT_ID')
        self._init_bot()
        
        # Множества для отслеживания отправленных уведомлений
        self.sent_game_end_notifications: Set[str] = set()
        self.sent_game_start_notifications: Set[str] = set()
        self.sent_game_result_notifications: Set[str] = set()
        self.sent_morning_notifications: Set[str] = set()
    
    def _init_bot(self):
        """Инициализация бота"""
        bot_token = os.getenv('BOT_TOKEN')
        if bot_token:
            try:
                self.bot = Bot(token=bot_token)
                logger.info("✅ Бот инициализирован успешно")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации бота: {e}")
        else:
            logger.error("❌ BOT_TOKEN не настроен")
    
    async def send_game_end_notification(self, game_info: Dict[str, Any], game_url: str):
        """Отправляет уведомление о завершении игры"""
        if not self.bot or not self.chat_id:
            logger.error("Бот или CHAT_ID не настроены")
            return
        
        # Создаем уникальный ID для уведомления
        notification_id = f"game_end_{game_url}"
        
        if notification_id in self.sent_game_end_notifications:
            logger.info("Уведомление о завершении игры уже отправлено")
            return
        
        try:
            team1 = game_info.get('team1', 'Команда 1')
            team2 = game_info.get('team2', 'Команда 2')
            score = game_info.get('score', 'Неизвестно')
            
            message = (
                f"🏁 Игра закончилась!\n\n"
                f"🏀 {team1} vs {team2}\n"
                f"📊 Счет: {score}\n\n"
                f"Ссылка на статистику: {game_url}"
            )
            
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            self.sent_game_end_notifications.add(notification_id)
            logger.info(f"✅ Отправлено уведомление о завершении игры: {score}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о завершении игры: {e}")
    
    async def send_game_start_notification(self, game_info: Dict[str, Any], game_url: str):
        """Отправляет уведомление о начале игры"""
        if not self.bot or not self.chat_id:
            logger.error("Бот или CHAT_ID не настроены")
            return
        
        # Создаем уникальный ID для уведомления
        notification_id = f"game_start_{game_url}"
        
        if notification_id in self.sent_game_start_notifications:
            logger.info("Уведомление о начале игры уже отправлено")
            return
        
        try:
            team1 = game_info.get('team1', 'Команда 1')
            team2 = game_info.get('team2', 'Команда 2')
            game_time = game_info.get('time', 'Неизвестно')
            
            message = f"🏀 Игра {team1} против {team2} начинается в {game_time}!\n\nСсылка на игру: {game_url}"
            
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            self.sent_game_start_notifications.add(notification_id)
            logger.info(f"✅ Отправлено уведомление о начале игры: {team1} vs {team2} в {game_time}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о начале игры: {e}")
    
    async def send_game_result_notification(self, game_info: Dict[str, Any], poll_results: Optional[Dict[str, Any]] = None):
        """Отправляет уведомление о результате игры с количеством участников"""
        if not self.bot or not self.chat_id:
            logger.error("Бот или CHAT_ID не настроены")
            return
        
        # Создаем уникальный ID для уведомления
        notification_id = f"game_result_{game_info['date']}_{game_info['opponent_team']}"
        
        if notification_id in self.sent_game_result_notifications:
            logger.info("Уведомление о результате игры уже отправлено")
            return
        
        try:
            # Определяем победителя
            if game_info['pullup_score'] > game_info['opponent_score']:
                result_emoji = "🏆"
                result_text = "победили"
            elif game_info['pullup_score'] < game_info['opponent_score']:
                result_emoji = "😔"
                result_text = "проиграли"
            else:
                result_emoji = "🤝"
                result_text = "сыграли вничью"
            
            # Формируем сообщение
            message = f"🏀 Игра против **{game_info['opponent_team']}** закончилась\n"
            message += f"{result_emoji} Счет: **{game_info['pullup_team']} {game_info['pullup_score']} : {game_info['opponent_score']} {game_info['opponent_team']}** ({result_text})\n"
            
            # Добавляем информацию о голосовании, если есть
            if poll_results:
                votes = poll_results.get('votes', {})
                ready_count = votes.get('ready', 0)
                not_ready_count = votes.get('not_ready', 0)
                coach_count = votes.get('coach', 0)
                total_votes = votes.get('total', 0)
                
                message += f"\n📊 **Статистика голосования:**\n"
                message += f"✅ Готовы: {ready_count}\n"
                message += f"❌ Не готовы: {not_ready_count}\n"
                message += f"👨‍🏫 Тренер: {coach_count}\n"
                message += f"📈 Всего проголосовало: {total_votes}"
                
                # Анализ посещаемости
                if ready_count > 0:
                    attendance_rate = (ready_count / total_votes * 100) if total_votes > 0 else 0
                    if attendance_rate >= 80:
                        message += f"\n🎯 **Отличная готовность!** ({attendance_rate:.1f}%)"
                    elif attendance_rate >= 60:
                        message += f"\n👍 **Хорошая готовность** ({attendance_rate:.1f}%)"
                    elif attendance_rate >= 40:
                        message += f"\n⚠️ **Средняя готовность** ({attendance_rate:.1f}%)"
                    else:
                        message += f"\n😕 **Низкая готовность** ({attendance_rate:.1f}%)"
                else:
                    message += f"\n⚠️ **Никто не проголосовал за участие**"
            else:
                message += f"\n📊 **Статистика голосования:** Недоступна"
            
            message += f"\n\n📅 Дата: {game_info['date']}"
            
            # Отправляем сообщение
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            # Отмечаем уведомление как отправленное
            self.sent_game_result_notifications.add(notification_id)
            logger.info(f"Отправлено уведомление о результате игры: {game_info['opponent_team']}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о результате игры: {e}")
    
    async def send_morning_notification(self, games: List[Dict[str, Any]], date: str):
        """Отправляет утреннее уведомление о предстоящих играх"""
        if not self.bot or not self.chat_id:
            logger.error("Бот или CHAT_ID не настроены")
            return
        
        # Создаем уникальный ID для уведомления
        notification_id = f"morning_{date}"
        
        if notification_id in self.sent_morning_notifications:
            logger.info("Утреннее уведомление уже отправлено")
            return
        
        try:
            if not games:
                message = f"📅 {date}\n\n🏀 Сегодня игр PullUP нет"
            else:
                message = f"📅 {date}\n\n🏀 Сегодня игры PullUP:\n\n"
                for i, game in enumerate(games, 1):
                    message += f"{i}. {game['time']} - {game['team']} vs {game['opponent']}\n"
            
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            self.sent_morning_notifications.add(notification_id)
            logger.info(f"✅ Отправлено утреннее уведомление для {date}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки утреннего уведомления: {e}")
    
    def clear_notifications(self):
        """Очищает все отслеживаемые уведомления (для тестирования)"""
        self.sent_game_end_notifications.clear()
        self.sent_game_start_notifications.clear()
        self.sent_game_result_notifications.clear()
        self.sent_morning_notifications.clear()
        logger.info("Очищены все отслеживаемые уведомления")

# Глобальный экземпляр менеджера уведомлений
notification_manager = NotificationManager()
