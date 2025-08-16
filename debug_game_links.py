import asyncio
import aiohttp
import re
from bs4 import BeautifulSoup

async def debug_game_links():
    url = "http://letobasket.ru/"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html_content = await response.text()
    
    # Ищем все ссылки game.html
    game_links = re.findall(r'href=["\']([^"\']*game\.html\?gameId=\d+[^"\']*)["\']', html_content, re.IGNORECASE)
    print(f"Найдено ссылок game.html: {len(game_links)}")
    for i, link in enumerate(game_links):
        print(f"  {i+1}. {link}")
    
    print("\n" + "="*80)
    
    # Ищем контекст для каждой игры PullUP
    pullup_games = [
        {"time": "12.30", "team1": "IT Basket", "team2": "Pull Up-Фарм"},
        {"time": "14.00", "team1": "Маиле Карго", "team2": "Pull Up"}
    ]
    
    current_date = "16.08.2025"
    
    for i, game in enumerate(pullup_games):
        print(f"\n--- Игра {i+1}: {game['time']} {game['team1']} vs {game['team2']} ---")
        
        game_context = f"{current_date} {game['time']} {game['team1']} {game['team2']}"
        context_start = html_content.lower().find(game_context[:50].lower())
        
        if context_start != -1:
            print(f"Найден контекст на позиции: {context_start}")
            
            # Показываем контекст вокруг игры
            search_start = max(0, context_start - 200)
            search_end = min(len(html_content), context_start + 500)
            context_area = html_content[search_start:search_end]
            
            print("Контекст вокруг игры:")
            print(context_area)
            
            # Ищем ссылки в этом контексте
            links_in_context = re.findall(r'href=["\']([^"\']*game\.html\?gameId=\d+[^"\']*)["\']', context_area, re.IGNORECASE)
            print(f"Ссылки в контексте: {links_in_context}")
            
            # Ищем "СТРАНИЦА ИГРЫ" в контексте
            page_links = re.findall(r'СТРАНИЦА ИГРЫ[^>]*href=["\']([^"\']+)["\']', context_area, re.IGNORECASE)
            print(f"Ссылки 'СТРАНИЦА ИГРЫ': {page_links}")
        else:
            print("Контекст не найден!")

if __name__ == "__main__":
    asyncio.run(debug_game_links())
