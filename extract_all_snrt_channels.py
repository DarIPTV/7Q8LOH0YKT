#!/usr/bin/env python3
"""
Extract tokens for ALL SNRT channels - runs ALL channels in PARALLEL
Tokens are short-lived (~5-10 min), so parallel extraction is critical
"""
import asyncio
from playwright.async_api import async_playwright
import json
import sys
import time
import re

CHANNELS = {
    "al-aoula": "https://snrt.player.easybroadcast.io/events/73_aloula_w1dqfwm",
    "arriadia": "https://snrt.player.easybroadcast.io/events/73_arryadia_k2tgcj0",
    "assadissa": "https://snrt.player.easybroadcast.io/events/73_assadissa_7b7u5n1",
    "al-maghribia": "https://snrt.player.easybroadcast.io/events/73_almaghribia_83tz85q",
    "tamazight": "https://snrt.player.easybroadcast.io/events/73_tamazight_tccybxt",
    "laayoune": "https://snrt.player.easybroadcast.io/events/73_laayoune_pgagr52",
    "attakafiya": "https://snrt.player.easybroadcast.io/events/73_arrabia_hthcj4p"
}

async def extract_channel(channel_id, iframe_url):
    """Extract M3U8 URL for a single channel"""
    print(f"🔍 Starting {channel_id}...", flush=True)

    m3u8_urls = []

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()

            # Capture M3U8 requests — only real stream URLs
            def log_request(request):
                url = request.url
                if 'token.easybroadcast.io' in url:
                    return
                if '.m3u8' in url and 'cdn.live.easybroadcast' in url:
                    if url not in m3u8_urls:
                        m3u8_urls.append(url)
                        print(f"  📡 {channel_id}: captured URL", flush=True)

            page.on("request", log_request)

            try:
                await page.goto(iframe_url, wait_until="domcontentloaded", timeout=45000)
            except:
                pass

            await asyncio.sleep(20)

            # Try to click play
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
                        await asyncio.sleep(3)
                        break
                except:
                    pass

            await asyncio.sleep(15)
            await browser.close()

        except Exception as e:
            print(f"  ❌ {channel_id}: {e}", flush=True)

    if m3u8_urls:
        now = int(time.time())

        # Pick best token: most time remaining (> 2 min), prefer playlist_dvr
        best_url = None
        best_remaining = -1

        for url in m3u8_urls:
            if 'playlist_dvr' in url:
                m = re.search(r'expires=(\d+)', url)
                if m:
                    expires = int(m.group(1))
                    remaining = expires - now
                    if remaining > 120 and remaining > best_remaining:  # > 2 min
                        best_url = url
                        best_remaining = remaining

        if best_url:
            mins = best_remaining // 60
            print(f"  ✅ {channel_id}: {mins}min remaining", flush=True)
            return best_url

        # Fallback: use the LAST captured URL (most recently issued = freshest)
        fallback = m3u8_urls[-1]
        m = re.search(r'expires=(\d+)', fallback)
        if m:
            remaining = int(m.group(1)) - now
            print(f"  ⚠️  {channel_id}: fallback, {remaining//60}min remaining", flush=True)
        else:
            print(f"  ⚠️  {channel_id}: fallback (no expiry info)", flush=True)
        return fallback

    print(f"  ❌ {channel_id}: no URLs captured", flush=True)
    return None


async def main():
    start = time.time()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     Extracting ALL SNRT Channels (PARALLEL)                 ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(flush=True)

    # Run ALL channels simultaneously
    tasks = [extract_channel(cid, url) for cid, url in CHANNELS.items()]
    channel_ids = list(CHANNELS.keys())
    results_list = await asyncio.gather(*tasks)
    results = dict(zip(channel_ids, results_list))

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"RESULTS ({elapsed:.0f}s):")
    print("="*60)

    success_count = 0
    for channel_id, url in results.items():
        if url:
            print(f"✅ {channel_id}")
            success_count += 1
        else:
            print(f"❌ {channel_id}")

    print(f"\n{success_count}/{len(CHANNELS)} channels extracted")

    # Merge with existing — only update successful extractions
    try:
        with open("snrt_streams.json", 'r') as f:
            existing = json.load(f)
    except:
        existing = {}

    for channel_id, url in results.items():
        if url is not None:
            existing[channel_id] = url

    with open("snrt_streams.json", 'w') as f:
        json.dump(existing, f, indent=2)

    print(f"💾 Saved to snrt_streams.json\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
