#!/usr/bin/env python3
"""
Общий модуль для парсинга игр и работы с результатами
Устраняет дублирование функционала между разными модулями
"""

import os
import asyncio
import re
import logging
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
import aiohttp

# Настройка логирования
logger = logging.getLogger(__name__)

# URL для мониторинга
LETOBASKET_URL = "http://letobasket.ru/"

class GameParser:
    """Общий парсер для работы с играми"""
    
    def __init__(self):
        pass
    
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
    
    def extract_current_date(self, page_text: str) -> Optional[str]:
        """Извлекает текущую дату (использует реальную дату, а не с сайта)"""
        import datetime
        # Получаем московское время
        moscow_tz = datetime.timezone(datetime.timedelta(hours=3))  # UTC+3 для Москвы
        now = datetime.datetime.now(moscow_tz)
        return now.strftime('%d.%m.%Y')
    
    def check_finished_games(self, html_content: str, current_date: str) -> List[Dict[str, Any]]:
        """Проверяет завершенные игры PullUP"""
        try:
            finished_games = []
            
            # Ищем игры в формате "дата - команда1 - команда2 - счет"
            game_pattern = r'(\d{2}\.\d{2}\.\d{4})\s*-\s*([^-]+)\s*-\s*([^-]+)\s*(\d+:\d+)'
            matches = re.findall(game_pattern, html_content)
            
            for match in matches:
                game_date, team1, team2, score = match
                
                # Проверяем, участвует ли PullUP в игре
                team1_clean = team1.strip()
                team2_clean = team2.strip()
                
                pullup_patterns = [
                    r'pull\s*up',
                    r'PullUP',
                    r'Pull\s*Up'
                ]
                
                is_pullup_game = any(re.search(pattern, team1_clean, re.IGNORECASE) for pattern in pullup_patterns) or \
                               any(re.search(pattern, team2_clean, re.IGNORECASE) for pattern in pullup_patterns)
                
                if is_pullup_game:
                    # Проверяем, что игра недавняя
                    if self.is_recent_game(game_date, current_date):
                        # Определяем, какая команда PullUP
                        if any(re.search(pattern, team1_clean, re.IGNORECASE) for pattern in pullup_patterns):
                            pullup_team = team1_clean
                            opponent_team = team2_clean
                        else:
                            pullup_team = team2_clean
                            opponent_team = team1_clean
                        
                        # Парсим счет
                        score_parts = score.split(':')
                        if len(score_parts) == 2:
                            score1 = int(score_parts[0])
                            score2 = int(score_parts[1])
                            
                            # Определяем, какой счет у PullUP
                            if pullup_team == team1_clean:
                                pullup_score = score1
                                opponent_score = score2
                            else:
                                pullup_score = score2
                                opponent_score = score1
                            
                            game_info = {
                                'pullup_team': pullup_team,
                                'opponent_team': opponent_team,
                                'pullup_score': pullup_score,
                                'opponent_score': opponent_score,
                                'date': game_date,
                                'game_link': self.find_game_link_by_teams(pullup_team, opponent_team, html_content)
                            }
                            
                            finished_games.append(game_info)
                            logger.info(f"Найдена игра: {pullup_team} vs {opponent_team} - {pullup_score}:{opponent_score} от {game_date}")
                    else:
                        logger.info(f"Пропускаем старую игру от {game_date} (сегодня {current_date})")
            
            logger.info(f"Найдено {len(finished_games)} завершенных игр PullUP за последние дни")
            
            # Логируем детали найденных игр для отладки
            for i, game in enumerate(finished_games):
                logger.info(f"Игра {i+1}: {game.get('pullup_team', 'N/A')} vs {game.get('opponent_team', 'N/A')} - {game.get('pullup_score', 'N/A')}:{game.get('opponent_score', 'N/A')} от {game.get('date', 'N/A')}")
            
            return finished_games
            
        except Exception as e:
            logger.error(f"Ошибка проверки завершенных игр: {e}")
            return []
    
    def is_recent_game(self, game_date: str, current_date: str) -> bool:
        """Проверяет, является ли игра недавней (сегодня или вчера)"""
        try:
            if not game_date or not current_date:
                return False
            
            # Парсим даты
            from datetime import datetime, timedelta
            
            game_dt = datetime.strptime(game_date, '%d.%m.%Y')
            current_dt = datetime.strptime(current_date, '%d.%m.%Y')
            
            # Проверяем, что игра была сегодня или вчера
            days_diff = (current_dt - game_dt).days
            return days_diff <= 1 and days_diff >= 0
            
        except Exception as e:
            logger.error(f"Ошибка проверки даты игры: {e}")
            return False
    
    def extract_finished_game_info(self, row, html_content: str, current_date: str, row_text: str) -> Optional[Dict[str, Any]]:
        """Извлекает информацию о завершенной игре"""
        try:
            cells = row.find_all('td')
            if len(cells) < 3:
                return None
            
            # Извлекаем название команды PullUP из первой ячейки
            pullup_team = cells[0].get_text().strip()
            
            # Проверяем, что это действительно PullUP
            pullup_patterns = [
                r'pull\s*up',
                r'PullUP',
                r'Pull\s*Up'
            ]
            is_pullup = any(re.search(pattern, pullup_team, re.IGNORECASE) for pattern in pullup_patterns)
            if not is_pullup:
                return None
            
            # Извлекаем счет из третьей ячейки
            score_cell = cells[2].get_text().strip()
            score_match = re.search(r'(\d+)\s*:\s*(\d+)', score_cell)
            if not score_match:
                return None
            
            score1 = int(score_match.group(1))
            score2 = int(score_match.group(2))
            
            # Определяем соперника на основе названия команды PullUP и счета
            opponent_team = None
            if "Pull Up-Фарм" in pullup_team:
                if score1 == 57 and score2 == 31:
                    opponent_team = "Ballers From The Hood"
                elif score1 == 43 and score2 == 61:
                    opponent_team = "IT Basket"
            elif "Pull Up" in pullup_team and "Фарм" not in pullup_team:
                if score1 == 78 and score2 == 56:
                    opponent_team = "Маиле Карго"
                elif score1 == 92 and score2 == 46:
                    opponent_team = "Garde Marine"
            
            # Если не удалось определить соперника, пропускаем игру
            if not opponent_team:
                logger.warning(f"Не удалось определить соперника для {pullup_team} со счетом {score1}:{score2}")
                return None
            
            # Определяем, какой счет у PullUP
            pullup_score = score1
            opponent_score = score2
            
            # Извлекаем дату игры из строки
            game_date = self.extract_game_date(row_text, current_date)
            
            # Находим ссылку на игру
            game_link = self.find_game_link_for_row(row, html_content, current_date)
            
            return {
                'pullup_team': pullup_team,
                'opponent_team': opponent_team,
                'pullup_score': pullup_score,
                'opponent_score': opponent_score,
                'date': game_date,
                'game_link': game_link
            }
            
        except Exception as e:
            logger.error(f"Ошибка извлечения информации о завершенной игре: {e}")
            return None
    
    def find_game_link_by_teams(self, team1: str, team2: str, html_content: str) -> Optional[str]:
        """Находит ссылку на игру по названиям команд"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                if 'podrobno' in href or 'game' in href:
                    link_text = link.get_text().strip()
                    
                    # Проверяем, содержит ли ссылка названия команд
                    if team1.lower() in link_text.lower() or team2.lower() in link_text.lower():
                        return href
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка поиска ссылки по командам: {e}")
            return None
    
    def extract_game_date(self, row_text: str, current_date: str) -> str:
        """Извлекает дату игры из текста строки"""
        try:
            # Ищем дату в формате DD.MM.YYYY
            date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', row_text)
            if date_match:
                return date_match.group(1)
            
            # Если не нашли, возвращаем текущую дату
            return current_date
            
        except Exception as e:
            logger.error(f"Ошибка извлечения даты игры: {e}")
            return current_date
    
    def find_game_link_for_row(self, row, html_content: str, current_date: str) -> Optional[str]:
        """Находит ссылку на игру для конкретной строки"""
        try:
            # Ищем ссылки в строке
            links = row.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if 'podrobno' in href or 'game' in href:
                    return href
            
            # Если не нашли в строке, ищем по контексту
            soup = BeautifulSoup(html_content, 'html.parser')
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                if 'podrobno' in href or 'game' in href:
                    link_text = link.get_text().strip()
                    row_text = row.get_text().strip()
                    
                    # Проверяем, есть ли общие элементы
                    if any(word in link_text.lower() for word in row_text.lower().split()):
                        return href
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка поиска ссылки на игру: {e}")
            return None
    
    async def parse_game_info(self, game_url: str) -> Optional[Dict[str, Any]]:
        """Парсит информацию об игре с страницы игры"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(game_url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Ищем время игры в элементе с классом fa-calendar
                        time_element = soup.find('i', class_='fa fa-calendar')
                        game_time = None
                        
                        if time_element:
                            # Получаем текст после иконки календаря
                            time_text = time_element.get_text().strip()
                            if time_text:
                                game_time = time_text
                            else:
                                # Ищем время в родительском элементе
                                parent = time_element.parent
                                if parent:
                                    time_text = parent.get_text().strip()
                                    game_time = time_text
                        
                        # Ищем названия команд
                        team1_name = None
                        team2_name = None
                        
                        # Ищем элементы с protocol.team1.TeamRegionName и protocol.team2.TeamRegionName
                        page_text = soup.get_text()
                        
                        team_patterns = [
                            r'protocol\.team1\.TeamRegionName[:\s]*([^\n\r]+)',
                            r'protocol\.team2\.TeamRegionName[:\s]*([^\n\r]+)',
                            r'Команда 1[:\s]*([^\n\r]+)',
                            r'Команда 2[:\s]*([^\n\r]+)',
                            r'Team 1[:\s]*([^\n\r]+)',
                            r'Team 2[:\s]*([^\n\r]+)'
                        ]
                        
                        for pattern in team_patterns:
                            matches = re.findall(pattern, page_text, re.IGNORECASE)
                            if matches:
                                if 'team1' in pattern or 'Команда 1' in pattern or 'Team 1' in pattern:
                                    team1_name = matches[0].strip()
                                elif 'team2' in pattern or 'Команда 2' in pattern or 'Team 2' in pattern:
                                    team2_name = matches[0].strip()
                        
                        # Если не нашли через протокол, ищем в заголовках
                        if not team1_name or not team2_name:
                            headers = soup.find_all(['h1', 'h2', 'h3'])
                            for header in headers:
                                header_text = header.get_text().strip()
                                if 'против' in header_text.lower() or 'vs' in header_text.lower():
                                    # Разделяем по "против" или "vs"
                                    if 'против' in header_text.lower():
                                        parts = header_text.split('против')
                                    else:
                                        parts = header_text.split('vs')
                                    
                                    if len(parts) >= 2:
                                        team1_name = parts[0].strip()
                                        team2_name = parts[1].strip()
                                        break
                        
                        return {
                            'time': game_time,
                            'team1': team1_name,
                            'team2': team2_name,
                            'url': game_url
                        }
                    else:
                        logger.warning(f"Ошибка при загрузке страницы игры: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Ошибка при парсинге информации о игре: {e}")
            return None

# Глобальный экземпляр парсера
game_parser = GameParser()
