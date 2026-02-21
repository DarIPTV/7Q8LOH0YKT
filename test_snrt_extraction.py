#!/usr/bin/env python3
"""
Simple SNRT stream extraction test
"""

import asyncio
import sys
from playwright.async_api import async_playwright

async def test_extraction():
    """Test extracting stream from Al Aoula page"""
    
    print("Starting browser...")
    
    m3u8_urls = []
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            print("✓ Browser launched")
            
            page = await browser.new_page()
            print("✓ Page created")
            
            # Listen for all requests
            def log_request(request):
                url = request.url
                if '.m3u8' in url:
                    print(f"📡 Found M3U8: {url[:100]}...")
                    m3u8_urls.append(url)
            
            page.on("request", log_request)
            
            print("Loading https://snrtlive.ma/fr/al-aoula ...")
            await page.goto("https://snrtlive.ma/fr/al-aoula", timeout=60000)
            print("✓ Page loaded")
            
            # Wait for network to settle
            print("Waiting for video player to load...")
            await asyncio.sleep(10)
            
            # Check page content
            title = await page.title()
            print(f"Page title: {title}")
            
            # Look for iframe
            iframes = await page.query_selector_all("iframe")
            print(f"Found {len(iframes)} iframes")
            
            if m3u8_urls:
                print(f"\n✅ SUCCESS! Found {len(m3u8_urls)} M3U8 URLs:")
                for url in m3u8_urls:
                    print(f"  {url}")
            else:
                print("\n⚠️  No M3U8 URLs captured yet")
                print("The page might use a different streaming method")
            
            await browser.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    return m3u8_urls


if __name__ == "__main__":
    print("="*60)
    print("SNRT Stream Extraction Test")
    print("="*60)
    print()
    
    urls = asyncio.run(test_extraction())
    
    if urls:
        print(f"\n✅ Extraction successful!")
        print(f"Use this URL: {urls[0]}")
    else:
        print(f"\n❌ Extraction failed - no M3U8 URLs found")
        sys.exit(1)
