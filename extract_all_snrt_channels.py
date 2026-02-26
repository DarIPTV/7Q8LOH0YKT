#!/usr/bin/env python3
"""
Extract tokens for ALL SNRT channels
"""
import asyncio
from playwright.async_api import async_playwright
import json
import sys

CHANNELS = {
    "al-aoula": "https://snrt.player.easybroadcast.io/events/73_aloula_w1dqfwm",
    "arriadia": "https://snrt.player.easybroadcast.io/events/73_arryadia_k2tgcj0",  # Note: arryadia (double r)
    "assadissa": "https://snrt.player.easybroadcast.io/events/73_assadissa_7b7u5n1",
    "al-maghribia": "https://snrt.player.easybroadcast.io/events/73_almaghribia_83tz85q",
    "tamazight": "https://snrt.player.easybroadcast.io/events/73_tamazight_tccybxt",
    "laayoune": "https://snrt.player.easybroadcast.io/events/73_laayoune_pgagr52",
    "attakafiya": "https://snrt.player.easybroadcast.io/events/73_arrabia_hthcj4p"  # Cultural channel
}

async def extract_channel(channel_id, iframe_url):
    """Extract M3U8 URL for a single channel"""
    print(f"\n🔍 Extracting {channel_id}...", flush=True)
    
    m3u8_urls = []
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Capture M3U8 requests
            def log_request(request):
                url = request.url
                # Skip token metadata URLs
                if 'token.easybroadcast.io' in url:
                    return
                
                if '.m3u8' in url:
                    # Only capture actual stream URLs
                    if 'cdn.live.easybroadcast' in url:
                        if url not in m3u8_urls:  # Avoid duplicates
                            m3u8_urls.append(url)
                            print(f"  📡 Captured!", flush=True)
            
            page.on("request", log_request)
            
            # Navigate and wait (longer timeout for slow pages)
            try:
                await page.goto(iframe_url, wait_until="domcontentloaded", timeout=45000)
            except:
                pass  # Continue even if timeout - streams might still load
            
            await asyncio.sleep(25)
            
            # Try to click play
            try:
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
                            await button.click()
                            await asyncio.sleep(5)
                            break
                    except:
                        pass
            except:
                pass
            
            # Wait for stream to start (longer for reliability)
            await asyncio.sleep(20)
            
            await browser.close()
            
        except Exception as e:
            print(f"  ❌ Error: {e}", flush=True)
    
    if m3u8_urls:
        import time, re
        now = int(time.time())
        
        # Prefer fresh tokens with >30 min remaining
        for url in m3u8_urls:
            if 'playlist_dvr' in url or 'hls_variant' in url:
                m = re.search(r'expires=(\d+)', url)
                if m:
                    expires = int(m.group(1))
                    remaining = expires - now
                    if remaining < 1800:  # Skip if < 30 min left
                        print(f"  ⚠️  Token only has {remaining//60}min left, skipping...", flush=True)
                        continue
                print(f"  ✅ Success!", flush=True)
                return url
        # Fallback to first URL regardless of expiry
        print(f"  ✅ Success! (fallback)", flush=True)
        return m3u8_urls[0]
    
    print(f"  ❌ Failed", flush=True)
    return None

async def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     Extracting ALL SNRT Channels                            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(flush=True)
    
    results = {}
    
    for channel_id, iframe_url in CHANNELS.items():
        url = await extract_channel(channel_id, iframe_url)
        results[channel_id] = url
    
    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    
    success_count = 0
    for channel_id, url in results.items():
        if url:
            print(f"✅ {channel_id}")
            success_count += 1
        else:
            print(f"❌ {channel_id}")
    
    print(f"\n{success_count}/{len(CHANNELS)} channels extracted")
    
    # Save to file - merge with existing data (don't overwrite good tokens with None)
    try:
        with open("snrt_streams.json", 'r') as f:
            existing = json.load(f)
    except:
        existing = {}
    
    # Only update channels that successfully extracted
    for channel_id, url in results.items():
        if url is not None:
            existing[channel_id] = url
    
    with open("snrt_streams.json", 'w') as f:
        json.dump(existing, f, indent=2)
    
    print(f"💾 Saved to snrt_streams.json\n", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
