#!/usr/bin/env python3
"""
SNRT Stream Extraction - Navigate into iframe
"""

import asyncio
from playwright.async_api import async_playwright

async def extract_from_iframe():
    """Extract stream by navigating directly to the iframe URL"""
    
    print("Starting browser...")
    
    m3u8_urls = []
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Listen for all requests across all frames
            def log_request(request):
                url = request.url
                if '.m3u8' in url or 'easybroadcast' in url:
                    print(f"📡 {url[:120]}...")
                    if '.m3u8' in url:
                        m3u8_urls.append(url)
            
            page.on("request", log_request)
            
            # Navigate directly to the Easybroadcast iframe
            iframe_url = "https://snrt.player.easybroadcast.io/events/73_aloula_w1dqfwm"
            print(f"\nNavigating to iframe: {iframe_url}")
            
            await page.goto(iframe_url, wait_until="networkidle", timeout=60000)
            print("✓ Iframe loaded")
            
            # Wait longer for player to initialize and load stream
            print("Waiting for player to initialize...")
            await asyncio.sleep(15)
            
            # Try to find and click play button
            try:
                # Common play button selectors
                selectors = [
                    'button[aria-label*="play"]',
                    'button.play',
                    '[class*="play-button"]',
                    'button[title*="Play"]',
                    '.vjs-big-play-button'
                ]
                
                for selector in selectors:
                    try:
                        button = await page.query_selector(selector)
                        if button:
                            print(f"Found play button: {selector}")
                            await button.click()
                            print("Clicked play button")
                            await asyncio.sleep(5)
                            break
                    except:
                        pass
            except Exception as e:
                print(f"No play button found: {e}")
            
            # Get page content for debugging
            content = await page.content()
            if 'easybroadcast' in content.lower():
                print("✓ Easybroadcast player detected in page")
            
            # Wait a bit more for stream to start
            await asyncio.sleep(10)
            
            await browser.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    return m3u8_urls


if __name__ == "__main__":
    print("="*60)
    print("SNRT Iframe Stream Extraction")
    print("="*60)
    
    urls = asyncio.run(extract_from_iframe())
    
    if urls:
        print(f"\n✅ SUCCESS! Found {len(urls)} M3U8 URLs:")
        for url in urls:
            print(f"\n{url}")
        
        # Save to file
        import json
        with open('snrt_streams.json', 'w') as f:
            json.dump({"al-aoula": urls[0] if urls else None}, f, indent=2)
        print(f"\n💾 Saved to snrt_streams.json")
    else:
        print(f"\n❌ No M3U8 URLs found")
        print("\nThis suggests Easybroadcast is using stronger protection.")
        print("The streams may require:")
        print("  • Valid session cookies")
        print("  • Token authentication")
        print("  • Geo-location verification")
