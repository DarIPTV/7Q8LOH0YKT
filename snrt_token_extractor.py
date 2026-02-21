#!/usr/bin/env python3
"""
SNRT Stream Token Extractor
Uses browser automation to extract valid m3u8 URLs with tokens from snrtlive.ma
"""

import asyncio
import re
from playwright.async_api import async_playwright
import json

CHANNELS = {
    "al-aoula": "https://snrtlive.ma/fr/al-aoula",
    "arriadia": "https://snrtlive.ma/fr/arryadia",
    "assadissa": "https://snrtlive.ma/fr/assadissa",
    "al-maghribia": "https://snrtlive.ma/fr/almaghribia",
    "tamazight": "https://snrtlive.ma/fr/tamazight",
}


async def extract_stream_url(page_url, channel_name):
    """Extract m3u8 URL from SNRT page"""
    
    m3u8_urls = []
    
    def handle_request(request):
        """Capture m3u8 requests"""
        url = request.url
        if '.m3u8' in url and 'easybroadcast' in url:
            m3u8_urls.append(url)
            print(f"  📡 Captured: {url[:80]}...")
    
    async with async_playwright() as p:
        print(f"\n🌐 Loading {channel_name}...")
        
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Listen for network requests
        page.on("request", handle_request)
        
        try:
            # Navigate to page
            await page.goto(page_url, wait_until="networkidle", timeout=30000)
            
            # Wait a bit for video player to load and start
            await asyncio.sleep(5)
            
            # Try to click play button if exists
            try:
                play_button = await page.query_selector('button[class*="play"], .play-button, iframe')
                if play_button:
                    await play_button.click()
                    await asyncio.sleep(3)
            except:
                pass
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        finally:
            await browser.close()
    
    if m3u8_urls:
        # Return the playlist_dvr.m3u8 URL (the main one)
        for url in m3u8_urls:
            if 'playlist_dvr' in url or 'playlist' in url:
                return url
        return m3u8_urls[0]  # Fallback to first one
    
    return None


async def extract_all_channels():
    """Extract stream URLs for all SNRT channels"""
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     SNRT Stream Token Extractor                             ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    results = {}
    
    for channel_id, page_url in CHANNELS.items():
        stream_url = await extract_stream_url(page_url, channel_id)
        
        if stream_url:
            print(f"  ✅ Extracted successfully")
            results[channel_id] = stream_url
        else:
            print(f"  ❌ Failed to extract")
            results[channel_id] = None
    
    return results


async def main():
    """Main entry point"""
    
    try:
        results = await extract_all_channels()
        
        print("\n" + "="*60)
        print("RESULTS:")
        print("="*60)
        
        for channel_id, url in results.items():
            if url:
                print(f"\n{channel_id}:")
                print(f"  {url}")
        
        # Save to file
        output_file = "snrt_streams.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Saved to {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nℹ️  You may need to install Playwright:")
        print("    pip install playwright")
        print("    playwright install chromium")


if __name__ == "__main__":
    asyncio.run(main())
