import asyncio
import aiohttp
import re

async def debug_page_text():
    url = "http://letobasket.ru/"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html_content = await response.text()
    
    # Извлекаем текст из HTML
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    page_text = soup.get_text()
    
    print("=== АНАЛИЗ ТЕКСТА СТРАНИЦЫ ===")
    
    # Ищем текущую дату
    date_pattern = r'(\d{2}\.\d{2}\.\d{4})'
    date_match = re.search(date_pattern, page_text)
    if date_match:
        current_date = date_match.group(1)
        print(f"📅 Найдена дата: {current_date}")
    else:
        print("❌ Дата не найдена")
        return
    
    # Ищем игры PullUP
    pullup_games = [
        {"time": "12.30", "team1": "IT Basket", "team2": "Pull Up-Фарм"},
        {"time": "14.00", "team1": "Маиле Карго", "team2": "Pull Up"}
    ]
    
    print(f"\n=== ПОИСК ИГР PULLUP ===")
    
    for i, game in enumerate(pullup_games):
        print(f"\n--- Игра {i+1}: {game['time']} {game['team1']} vs {game['team2']} ---")
        
        # Ищем эту игру в тексте
        game_pattern = rf'{current_date}\s+{game["time"]}[^-]*-\s*{re.escape(game["team1"])}[^-]*-\s*{re.escape(game["team2"])}'
        match = re.search(game_pattern, page_text, re.IGNORECASE)
        
        if match:
            print(f"✅ Найдена игра: {match.group(0)}")
            
            # Показываем контекст вокруг найденной игры
            start_pos = max(0, match.start() - 100)
            end_pos = min(len(page_text), match.end() + 100)
            context = page_text[start_pos:end_pos]
            print(f"Контекст: {context}")
        else:
            print("❌ Игра не найдена")
            
            # Попробуем найти частично
            print("🔍 Поиск частичных совпадений:")
            
            # Ищем время
            time_pattern = rf'{current_date}\s+{game["time"]}'
            time_match = re.search(time_pattern, page_text)
            if time_match:
                print(f"  ✅ Найдено время: {time_match.group(0)}")
            
            # Ищем команды
            for team in [game["team1"], game["team2"]]:
                team_match = re.search(re.escape(team), page_text, re.IGNORECASE)
                if team_match:
                    print(f"  ✅ Найдена команда: {team}")
                else:
                    print(f"  ❌ Команда не найдена: {team}")

if __name__ == "__main__":
    asyncio.run(debug_page_text())
