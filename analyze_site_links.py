#!/usr/bin/env python3
"""
Скрипт для детального анализа всех ссылок на сайте letobasket.ru
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def analyze_site_links():
    """Анализирует все ссылки на сайте letobasket.ru"""
    print("🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ССЫЛОК НА САЙТЕ LETOBASKET.RU")
    print("=" * 60)
    
    try:
        url = "http://letobasket.ru"
        
        print(f"🌐 Получение данных с {url}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    print(f"❌ Ошибка получения страницы: {response.status}")
                    return
                
                html = await response.text()
                print(f"✅ Страница получена, размер: {len(html)} символов")
        
        # Парсим HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ищем все ссылки на странице
        all_links = soup.find_all('a', href=True)
        
        print(f"\n📊 НАЙДЕНО {len(all_links)} ССЫЛОК НА СТРАНИЦЕ")
        print("=" * 60)
        
        # Анализируем ссылки
        game_related_links = []
        vizotek_links = []
        basketball_links = []
        
        for i, link in enumerate(all_links):
            href = link.get('href', '')
            link_text = link.get_text().strip()
            
            if not href or not link_text:
                continue
            
            # Ищем ссылки, связанные с играми
            if any(keyword in href.lower() or keyword in link_text.lower() 
                   for keyword in ['game', 'match', 'podrobno', 'игра', 'матч', 'протокол']):
                game_related_links.append({
                    'index': i,
                    'href': href,
                    'text': link_text
                })
            
            # Ищем ссылки с упоминанием Визотек
            if 'визотек' in link_text.lower() or 'vizotek' in link_text.lower():
                vizotek_links.append({
                    'index': i,
                    'href': href,
                    'text': link_text
                })
            
            # Ищем ссылки с баскетбольными терминами
            if any(keyword in link_text.lower() 
                   for keyword in ['баскет', 'basket', 'лига', 'league', 'турнир']):
                basketball_links.append({
                    'index': i,
                    'href': href,
                    'text': link_text
                })
        
        # Выводим результаты
        print(f"\n🏀 ССЫЛКИ, СВЯЗАННЫЕ С ИГРАМИ ({len(game_related_links)}):")
        for link in game_related_links[:20]:  # Показываем первые 20
            print(f"   {link['index']:3d}. {link['text']} -> {link['href']}")
        
        if len(game_related_links) > 20:
            print(f"   ... и еще {len(game_related_links) - 20} ссылок")
        
        print(f"\n🎯 ССЫЛКИ С УПОМИНАНИЕМ ВИЗОТЕК ({len(vizotek_links)}):")
        for link in vizotek_links:
            print(f"   {link['index']:3d}. {link['text']} -> {link['href']}")
        
        if not vizotek_links:
            print("   ❌ Ссылки с упоминанием Визотек не найдены")
        
        print(f"\n🏆 БАСКЕТБОЛЬНЫЕ ССЫЛКИ ({len(basketball_links)}):")
        for link in basketball_links[:15]:  # Показываем первые 15
            print(f"   {link['index']:3d}. {link['text']} -> {link['href']}")
        
        if len(basketball_links) > 15:
            print(f"   ... и еще {len(basketball_links) - 15} ссылок")
        
        # Ищем все уникальные тексты ссылок
        unique_texts = set()
        for link in all_links:
            text = link.get_text().strip()
            if text and len(text) > 2:
                unique_texts.add(text)
        
        print(f"\n📋 ВСЕГО УНИКАЛЬНЫХ ТЕКСТОВ ССЫЛОК: {len(unique_texts)}")
        
        # Показываем некоторые уникальные тексты
        print("\n🔍 ПРИМЕРЫ ТЕКСТОВ ССЫЛОК:")
        for i, text in enumerate(sorted(unique_texts)[:30]):
            print(f"   {i+1:2d}. {text}")
        
        if len(unique_texts) > 30:
            print(f"   ... и еще {len(unique_texts) - 30} текстов")
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_site_links())
