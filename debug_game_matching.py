import asyncio
import aiohttp
import re

async def debug_game_matching():
    url = "http://letobasket.ru/"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html_content = await response.text()
    
    # Извлекаем текст из HTML
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    page_text = soup.get_text()
    
    print("=== АНАЛИЗ СОВПАДЕНИЯ ИГР ===")
    
    # Ищем текущую дату
    date_pattern = r'(\d{2}\.\d{2}\.\d{4})'
    date_match = re.search(date_pattern, page_text)
    if date_match:
        current_date = date_match.group(1)
        print(f"📅 Найдена дата: {current_date}")
    else:
        print("❌ Дата не найдена")
        return
    
    # Ищем все игры на странице
    all_games = re.findall(rf'{current_date}\s+\d{{2}}\.\d{{2}}[^-]*-\s*[^-]+[^-]*-\s*[^-]+', page_text)
    
    print(f"\nВсе игры на странице:")
    for i, game in enumerate(all_games):
        print(f"  {i+1}. '{game}'")
    
    # Ищем конкретную игру PullUP
    target_game = {"time": "12.30", "team1": "IT Basket", "team2": "Pull Up-Фарм"}
    game_pattern = rf'{current_date}\s+{target_game["time"]}[^-]*-\s*{re.escape(target_game["team1"])}[^-]*-\s*{re.escape(target_game["team2"])}'
    text_match = re.search(game_pattern, page_text, re.IGNORECASE)
    
    if text_match:
        current_game_text = text_match.group(0)
        print(f"\n🎯 Найденная игра PullUP: '{current_game_text}'")
        
        # Пробуем найти совпадение
        for i, game in enumerate(all_games):
            print(f"\nСравнение с игрой {i+1}:")
            print(f"  Игра в списке: '{game}'")
            print(f"  Игра PullUP:   '{current_game_text}'")
            print(f"  Точное совпадение: {game.strip() == current_game_text.strip()}")
            print(f"  Без пробелов: {game.replace(' ', '').lower() == current_game_text.replace(' ', '').lower()}")
            
            # Проверяем, содержит ли игра нужные элементы
            has_time = target_game["time"] in game
            has_team1 = target_game["team1"] in game
            has_team2 = target_game["team2"] in game
            print(f"  Содержит время '{target_game['time']}': {has_time}")
            print(f"  Содержит команду1 '{target_game['team1']}': {has_team1}")
            print(f"  Содержит команду2 '{target_game['team2']}': {has_team2}")
            
            if has_time and has_team1 and has_team2:
                print(f"  ✅ ПОЛНОЕ СОВПАДЕНИЕ! Позиция: {i+1}")
                break
    else:
        print("❌ Игра PullUP не найдена")

if __name__ == "__main__":
    asyncio.run(debug_game_matching())
