import asyncio
import aiohttp
import re
import os
from datetime import datetime, time, timezone, timedelta
from bs4 import BeautifulSoup
import logging

# Импортируем общие модули
from game_parser import game_parser
from notification_manager import notification_manager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        pass
        
    async def get_fresh_page_content(self):
        """Получает свежий контент страницы, избегая кеша"""
        return await game_parser.get_fresh_page_content()
    
    def extract_current_date(self, page_text):
        """Извлекает текущую дату со страницы"""
        return game_parser.extract_current_date(page_text)
    
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
        
        # Получаем текущую дату
        moscow_time = get_moscow_time()
        current_date = moscow_time.strftime('%Y-%m-%d')
        
        # Используем общий менеджер уведомлений
        await notification_manager.send_morning_notification(games, current_date)
    
    def check_finished_games(self, html_content, current_date):
        """Проверяет завершенные игры PullUP"""
        return game_parser.check_finished_games(html_content, current_date)
    
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
                    game_link = "http://letobasket.ru/".rstrip('/') + '/' + game_link.lstrip('/')
                return game_link
            
            # Если не удалось найти по порядку, возвращаем главную страницу
            return "http://letobasket.ru/"
            
        except Exception as e:
            logger.error(f"Ошибка поиска ссылки на игру: {e}")
            return "http://letobasket.ru/"
    
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
                    game_link = "http://letobasket.ru/".rstrip('/') + '/' + game_link.lstrip('/')
                return game_link
            
            # Если не удалось найти по порядку, возвращаем главную страницу
            return "http://letobasket.ru/"
            
        except Exception as e:
            logger.error(f"Ошибка поиска ссылки на игру по времени: {e}")
            return "http://letobasket.ru/"
    
    def extract_finished_game_info(self, row, current_date, html_content):
        """Извлекает информацию о завершенной игре"""
        return game_parser.extract_finished_game_info(row, html_content, current_date)
    
    async def send_finish_notification(self, finished_game):
        """Отправляет уведомление о завершении игры"""
        await notification_manager.send_game_result_notification(finished_game)
    
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
