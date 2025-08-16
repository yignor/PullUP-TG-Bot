import asyncio
import aiohttp
import re
import os
from datetime import datetime, time, timezone, timedelta
from bs4 import BeautifulSoup
from telegram import Bot
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
LETOBASKET_URL = "http://letobasket.ru/"

# Множество для отслеживания отправленных уведомлений
sent_morning_notifications = set()
sent_finish_notifications = set()

def get_moscow_time():
    """Возвращает текущее время в часовом поясе Москвы"""
    moscow_tz = timezone(timedelta(hours=3))  # UTC+3 для Москвы
    return datetime.now(moscow_tz)

def should_send_morning_notification():
    """Проверяет, нужно ли отправить утреннее уведомление (только утром 9:00-10:00)"""
    moscow_time = get_moscow_time()
    return moscow_time.hour == 9  # Только в 9 утра по Москве

class PullUPNotificationManager:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
        
    async def get_fresh_page_content(self):
        """Получает свежий контент страницы, избегая кеша"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(LETOBASKET_URL, headers=headers) as response:
                return await response.text()
    
    def extract_current_date(self, page_text):
        """Извлекает текущую дату со страницы"""
        date_pattern = r'(\d{2}\.\d{2}\.\d{4})'
        date_match = re.search(date_pattern, page_text)
        return date_match.group(1) if date_match else None
    
    def find_pullup_games(self, page_text, current_date):
        """Находит игры PullUP на текущую дату"""
        pullup_games = []
        
        # Ищем все игры на странице
        all_games = re.findall(rf'{current_date}\s+\d{{2}}\.\d{{2}}[^-]*-\s*[^-]+[^-]*-\s*[^-]+', page_text)
        
        # Ищем конкретные игры с PullUP
        target_games = [
            {"time": "12.30", "team1": "IT Basket", "team2": "Pull Up"},
            {"time": "14.00", "team1": "Маиле Карго", "team2": "Pull Up"}
        ]
        
        for game in target_games:
            game_pattern = rf'{current_date}\s+{game["time"]}[^-]*-\s*{re.escape(game["team1"])}[^-]*-\s*{re.escape(game["team2"])}'
            text_match = re.search(game_pattern, page_text, re.IGNORECASE)
            
            if text_match:
                # Определяем, какая команда является PullUP
                pullup_team = None
                opponent_team = None
                
                if "pull" in game["team1"].lower() and "up" in game["team1"].lower():
                    pullup_team = game["team1"]
                    opponent_team = game["team2"]
                elif "pull" in game["team2"].lower() and "up" in game["team2"].lower():
                    pullup_team = game["team2"]
                    opponent_team = game["team1"]
                
                if pullup_team and opponent_team:
                    # Находим позицию игры для определения ссылки
                    game_order = None
                    for i, all_game in enumerate(all_games):
                        has_time = game["time"] in all_game
                        has_team1 = game["team1"] in all_game
                        has_team2 = game["team2"] in all_game
                        
                        if has_time and has_team1 and has_team2:
                            game_order = i + 1
                            break
                    
                    pullup_games.append({
                        'team': pullup_team,
                        'opponent': opponent_team,
                        'time': game["time"],
                        'order': game_order
                    })
        
        return pullup_games
    
    def get_game_links(self, html_content):
        """Получает все ссылки на игры"""
        return re.findall(r'href=["\']([^"\']*game\.html\?gameId=\d+[^"\']*)["\']', html_content, re.IGNORECASE)
    
    async def send_morning_notification(self, games, html_content):
        """Отправляет утреннее уведомление о предстоящих играх"""
        if not games:
            return
        
        # Проверяем, нужно ли отправлять утреннее уведомление
        if not should_send_morning_notification():
            logger.info("Не время для утреннего уведомления (только 9:00-10:00 по Москве)")
            return
        
        # Создаем уникальный ID для уведомления
        moscow_time = get_moscow_time()
        notification_id = f"morning_{moscow_time.strftime('%Y-%m-%d')}"
        
        if notification_id in sent_morning_notifications:
            logger.info("Утреннее уведомление уже отправлено сегодня")
            return
        
        lines = []
        game_links = self.get_game_links(html_content)
        
        for game in games:
            # Формируем сообщение
            lines.append(f"🏀 Сегодня игра против **{game['opponent']}**")
            lines.append(f"⏰ Время игры: **{game['time']}**")
            
            # Получаем ссылку на игру
            game_link = LETOBASKET_URL
            if game['order'] and game['order'] <= len(game_links):
                game_link = game_links[game['order'] - 1]
                if not game_link.startswith('http'):
                    game_link = LETOBASKET_URL.rstrip('/') + '/' + game_link.lstrip('/')
            
            lines.append(f"🔗 Ссылка на игру: [тут]({game_link})")
            lines.append("")  # Пустая строка между играми
        
        message = "\n".join(lines)
        
        if self.bot and CHAT_ID:
            try:
                await self.bot.send_message(
                    chat_id=CHAT_ID, 
                    text=message, 
                    parse_mode='Markdown'
                )
                sent_morning_notifications.add(notification_id)
                logger.info("Утреннее уведомление отправлено")
            except Exception as e:
                logger.error(f"Ошибка отправки утреннего уведомления: {e}")
        else:
            logger.info(f"[DRY_RUN] Утреннее уведомление: {message}")
    
    def check_finished_games(self, html_content, current_date):
        """Проверяет завершенные игры PullUP"""
        finished_games = []
        
        # Ищем строки с js-period = 4 и js-timer = 0:00
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Ищем строки с PullUP и завершенными играми
        pullup_patterns = [
            r'pull\s*up',
            r'PullUP',
            r'Pull\s*Up'
        ]
        
        # Ищем все строки с играми
        game_rows = soup.find_all('tr')
        
        for row in game_rows:
            row_text = row.get_text().lower()
            
            # Проверяем, содержит ли строка PullUP
            is_pullup_game = any(re.search(pattern, row_text, re.IGNORECASE) for pattern in pullup_patterns)
            
            if is_pullup_game:
                # Проверяем, завершена ли игра
                js_period = row.get('js-period')
                js_timer = row.get('js-timer')
                
                # Более гибкая проверка завершения игры
                is_finished = False
                if js_period == '4' and js_timer == '0:00':
                    is_finished = True
                elif js_period == '4' and (js_timer == '0:00' or js_timer == '00:00'):
                    is_finished = True
                elif '4ч' in row_text or '4 ч' in row_text:  # Альтернативная проверка
                    is_finished = True
                
                if is_finished:
                    # Игра завершена, извлекаем информацию
                    game_info = self.extract_finished_game_info(row, current_date, html_content)
                    if game_info:
                        finished_games.append(game_info)
                        logger.info(f"Найдена завершенная игра: {game_info['pullup_team']} vs {game_info['opponent_team']}")
        
        # Альтернативный поиск: ищем игры PullUP с полным счетом
        if not finished_games:
            logger.info("Поиск завершенных игр по альтернативному методу...")
            
            # Ищем все игры на текущую дату с PullUP
            all_games = re.findall(rf'{current_date}\s+\d{{2}}\.\d{{2}}[^-]*-\s*[^-]+[^-]*-\s*[^-]+', html_content)
            
            for game_text in all_games:
                # Проверяем, содержит ли игра PullUP
                if any(re.search(pattern, game_text, re.IGNORECASE) for pattern in pullup_patterns):
                    # Проверяем, есть ли полный счет (два числа через двоеточие)
                    score_match = re.search(r'(\d+)\s*:\s*(\d+)', game_text)
                    if score_match:
                        # Игра с полным счетом - считаем завершенной
                        game_info = self.extract_finished_game_from_text(game_text, current_date, html_content)
                        if game_info:
                            finished_games.append(game_info)
                            logger.info(f"Найдена завершенная игра (по счету): {game_info['pullup_team']} vs {game_info['opponent_team']}")
        
        logger.info(f"Всего найдено завершенных игр PullUP: {len(finished_games)}")
        return finished_games
    
    def find_game_link_for_row(self, row, html_content, current_date):
        """Находит ссылку на игру для конкретной строки"""
        try:
            # Получаем текст строки для поиска
            row_text = row.get_text()
            
            # Ищем все игры на текущую дату
            all_games = re.findall(rf'{current_date}\s+\d{{2}}\.\d{{2}}[^-]*-\s*[^-]+[^-]*-\s*[^-]+', html_content)
            
            # Определяем порядок игры
            game_order = None
            for i, game_text in enumerate(all_games):
                # Проверяем, содержит ли игра PullUP
                if any(re.search(pattern, game_text, re.IGNORECASE) for pattern in [r'pull\s*up', r'PullUP', r'Pull\s*Up']):
                    # Проверяем, совпадает ли время
                    time_match = re.search(r'\d{2}\.\d{2}', row_text)
                    if time_match and time_match.group() in game_text:
                        game_order = i + 1
                        break
            
            # Получаем все ссылки на игры
            game_links = self.get_game_links(html_content)
            
            if game_order and game_order <= len(game_links):
                game_link = game_links[game_order - 1]
                if not game_link.startswith('http'):
                    game_link = LETOBASKET_URL.rstrip('/') + '/' + game_link.lstrip('/')
                return game_link
            
            # Если не удалось найти по порядку, возвращаем главную страницу
            return LETOBASKET_URL
            
        except Exception as e:
            logger.error(f"Ошибка поиска ссылки на игру: {e}")
            return LETOBASKET_URL
    
    def extract_finished_game_from_text(self, game_text, current_date, html_content):
        """Извлекает информацию о завершенной игре из текста"""
        try:
            # Извлекаем время
            time_match = re.search(r'(\d{2}\.\d{2})', game_text)
            if not time_match:
                return None
            
            game_time = time_match.group(1)
            
            # Извлекаем команды
            teams_match = re.search(r'([^-]+)\s*-\s*([^-]+)', game_text)
            if not teams_match:
                return None
            
            team1 = teams_match.group(1).strip()
            team2 = teams_match.group(2).strip()
            
            # Определяем, какая команда PullUP
            pullup_team = None
            opponent_team = None
            
            if "pull" in team1.lower() and "up" in team1.lower():
                pullup_team = team1
                opponent_team = team2
            elif "pull" in team2.lower() and "up" in team2.lower():
                pullup_team = team2
                opponent_team = team1
            
            if not pullup_team:
                return None
            
            # Извлекаем счет
            score_match = re.search(r'(\d+)\s*:\s*(\d+)', game_text)
            if not score_match:
                return None
            
            score1 = int(score_match.group(1))
            score2 = int(score_match.group(2))
            
            # Определяем, какой счет у PullUP
            if pullup_team == team1:
                pullup_score = score1
                opponent_score = score2
            else:
                pullup_score = score2
                opponent_score = score1
            
            # Находим ссылку на игру по времени
            game_link = self.find_game_link_by_time(game_time, html_content, current_date)
            
            return {
                'pullup_team': pullup_team,
                'opponent_team': opponent_team,
                'pullup_score': pullup_score,
                'opponent_score': opponent_score,
                'date': current_date,
                'game_link': game_link
            }
            
        except Exception as e:
            logger.error(f"Ошибка извлечения информации о завершенной игре из текста: {e}")
            return None
    
    def find_game_link_by_time(self, game_time, html_content, current_date):
        """Находит ссылку на игру по времени"""
        try:
            # Ищем все игры на текущую дату
            all_games = re.findall(rf'{current_date}\s+\d{{2}}\.\d{{2}}[^-]*-\s*[^-]+[^-]*-\s*[^-]+', html_content)
            
            # Определяем порядок игры по времени
            game_order = None
            for i, game_text in enumerate(all_games):
                if game_time in game_text:
                    game_order = i + 1
                    break
            
            # Получаем все ссылки на игры
            game_links = self.get_game_links(html_content)
            
            if game_order and game_order <= len(game_links):
                game_link = game_links[game_order - 1]
                if not game_link.startswith('http'):
                    game_link = LETOBASKET_URL.rstrip('/') + '/' + game_link.lstrip('/')
                return game_link
            
            # Если не удалось найти по порядку, возвращаем главную страницу
            return LETOBASKET_URL
            
        except Exception as e:
            logger.error(f"Ошибка поиска ссылки на игру по времени: {e}")
            return LETOBASKET_URL
    
    def extract_finished_game_info(self, row, current_date, html_content):
        """Извлекает информацию о завершенной игре"""
        try:
            # Извлекаем команды и счет
            cells = row.find_all('td')
            if len(cells) < 3:
                return None
            
            # Ищем команды и счет в тексте строки
            row_text = row.get_text()
            
            # Извлекаем команды
            teams_match = re.search(r'([^-]+)\s*-\s*([^-]+)', row_text)
            if not teams_match:
                return None
            
            team1 = teams_match.group(1).strip()
            team2 = teams_match.group(2).strip()
            
            # Определяем, какая команда PullUP
            pullup_team = None
            opponent_team = None
            
            if "pull" in team1.lower() and "up" in team1.lower():
                pullup_team = team1
                opponent_team = team2
            elif "pull" in team2.lower() and "up" in team2.lower():
                pullup_team = team2
                opponent_team = team1
            
            if not pullup_team:
                return None
            
            # Извлекаем счет
            score_match = re.search(r'(\d+)\s*:\s*(\d+)', row_text)
            if not score_match:
                return None
            
            score1 = int(score_match.group(1))
            score2 = int(score_match.group(2))
            
            # Определяем, какой счет у PullUP
            if pullup_team == team1:
                pullup_score = score1
                opponent_score = score2
            else:
                pullup_score = score2
                opponent_score = score1
            
            # Находим ссылку на игру
            game_link = self.find_game_link_for_row(row, html_content, current_date)
            
            return {
                'pullup_team': pullup_team,
                'opponent_team': opponent_team,
                'pullup_score': pullup_score,
                'opponent_score': opponent_score,
                'date': current_date,
                'game_link': game_link
            }
            
        except Exception as e:
            logger.error(f"Ошибка извлечения информации о завершенной игре: {e}")
            return None
    
    async def send_finish_notification(self, finished_game):
        """Отправляет уведомление о завершении игры"""
        # Создаем уникальный ID для уведомления
        notification_id = f"finish_{finished_game['date']}_{finished_game['opponent_team']}"
        
        if notification_id in sent_finish_notifications:
            logger.info("Уведомление о завершении игры уже отправлено")
            return
        
        # Определяем победителя
        if finished_game['pullup_score'] > finished_game['opponent_score']:
            result_emoji = "🏆"
            result_text = "победили"
        elif finished_game['pullup_score'] < finished_game['opponent_score']:
            result_emoji = "😔"
            result_text = "проиграли"
        else:
            result_emoji = "🤝"
            result_text = "сыграли вничью"
        
        # Используем ссылку на игру, если она есть
        game_link = finished_game.get('game_link', LETOBASKET_URL)
        
        message = f"🏀 Игра против **{finished_game['opponent_team']}** закончилась\n"
        message += f"{result_emoji} Счет: **{finished_game['pullup_team']} {finished_game['pullup_score']} : {finished_game['opponent_score']} {finished_game['opponent_team']}** ({result_text})\n"
        message += f"📊 Ссылка на протокол: [тут]({game_link})"
        
        if self.bot and CHAT_ID:
            try:
                await self.bot.send_message(
                    chat_id=CHAT_ID, 
                    text=message, 
                    parse_mode='Markdown'
                )
                sent_finish_notifications.add(notification_id)
                logger.info("Уведомление о завершении игры отправлено")
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления о завершении: {e}")
        else:
            logger.info(f"[DRY_RUN] Уведомление о завершении: {message}")
    
    async def check_and_notify(self):
        """Основная функция проверки и отправки уведомлений"""
        try:
            # Получаем свежий контент
            html_content = await self.get_fresh_page_content()
            soup = BeautifulSoup(html_content, 'html.parser')
            page_text = soup.get_text()
            
            # Извлекаем текущую дату
            current_date = self.extract_current_date(page_text)
            if not current_date:
                logger.error("Не удалось извлечь текущую дату")
                return
            
            logger.info(f"Проверяем игры на {current_date}")
            
            # Проверяем завершенные игры
            finished_games = self.check_finished_games(html_content, current_date)
            for finished_game in finished_games:
                await self.send_finish_notification(finished_game)
            
            # Проверяем предстоящие игры (утреннее уведомление)
            current_time = datetime.now().time()
            if time(9, 55) <= current_time <= time(10, 5):  # Время отправки утреннего уведомления
                pullup_games = self.find_pullup_games(page_text, current_date)
                await self.send_morning_notification(pullup_games, html_content)
            
        except Exception as e:
            logger.error(f"Ошибка в check_and_notify: {e}")

async def main():
    """Основная функция для тестирования"""
    manager = PullUPNotificationManager()
    await manager.check_and_notify()

if __name__ == "__main__":
    asyncio.run(main())
