import asyncio
import aiohttp
import re

async def debug_specific_links():
    url = "http://letobasket.ru/"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html_content = await response.text()
    
    print("=== ПРОВЕРКА КОНКРЕТНЫХ GAMEID ===")
    
    # Проверяем конкретные gameId, которые должны быть правильными
    target_game_ids = ["921732", "921733", "921726", "921734", "921735"]
    
    for game_id in target_game_ids:
        # Ищем ссылку с этим gameId
        link_pattern = rf'game\.html\?gameId={game_id}[^"\']*'
        match = re.search(link_pattern, html_content, re.IGNORECASE)
        
        if match:
            full_link = match.group(0)
            print(f"✅ GameID {game_id}: {full_link}")
            
            # Ищем контекст вокруг этой ссылки
            start_pos = max(0, match.start() - 200)
            end_pos = min(len(html_content), match.end() + 200)
            context = html_content[start_pos:end_pos]
            
            # Извлекаем текст из контекста
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(context, 'html.parser')
            context_text = soup.get_text()
            
            print(f"   Контекст: {context_text[:100]}...")
        else:
            print(f"❌ GameID {game_id}: не найден")
    
    print(f"\n=== ВСЕ НАЙДЕННЫЕ ССЫЛКИ ===")
    game_links = re.findall(r'href=["\']([^"\']*game\.html\?gameId=\d+[^"\']*)["\']', html_content, re.IGNORECASE)
    for i, link in enumerate(game_links):
        game_id_match = re.search(r'gameId=(\d+)', link)
        game_id = game_id_match.group(1) if game_id_match else "неизвестно"
        print(f"  {i+1}. {link} (GameID: {game_id})")

if __name__ == "__main__":
    asyncio.run(debug_specific_links())
