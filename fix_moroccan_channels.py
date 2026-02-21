#!/usr/bin/env python3
"""
Enhanced IPTV Fixer - Prioritizes official sources for Moroccan/Arabic channels
"""

import requests
import subprocess
from pathlib import Path
from typing import Optional
import sys

TIMEOUT = 8

# Official SNRT Morocco CDN URLs (from web search + testing variants)
OFFICIAL_SNRT_URLS = {
    "Al Aoula": [
        "https://cdnamd-hls-globecast.akamaized.net/live/ramdisk/al_aoula_inter/hls_snrt/al_aoula_inter.m3u8",
        "http://cdnamd-hls-globecast.akamaized.net/live/ramdisk/al_aoula_inter/hls_snrt/index.m3u8",
    ],
    "2M Monde": [
        "https://cdnamd-hls-globecast.akamaized.net/live/ramdisk/2m_monde/hls_video_ts/index.m3u8",
        "https://cdnamd-hls-globecast.akamaized.net/live/ramdisk/2m_monde/hls_video_ts_tuhawxpiemz257adfc/2m_monde.m3u8",
    ],
    "Arriadia": [
        "https://cdnamd-hls-globecast.akamaized.net/live/ramdisk/arriadia/hls_snrt/index.m3u8",
        "http://cdnamd-hls-globecast.akamaized.net/live/ramdisk/arriadia/hls_snrt/index.m3u8",
    ],
    "Assadissa": [
        "https://cdnamd-hls-globecast.akamaized.net/live/ramdisk/assadissa/hls_snrt/index.m3u8",
        "http://cdnamd-hls-globecast.akamaized.net/live/ramdisk/assadissa/hls_snrt/index.m3u8",
    ],
    "Al Maghribia": [
        "https://cdnamd-hls-globecast.akamaized.net/live/ramdisk/al_maghribia_snrt/hls_snrt/index.m3u8",
        "http://cdnamd-hls-globecast.akamaized.net/live/ramdisk/al_maghribia_snrt/hls_snrt/index.m3u8",
    ],
    "Attakafiya": [
        "https://cdnamd-hls-globecast.akamaized.net/live/ramdisk/arrabiaa/hls_snrt/index.m3u8",
        "http://cdnamd-hls-globecast.akamaized.net/live/ramdisk/arrabiaa/hls_snrt/index.m3u8",
    ],
    "Al Aoula Laayoune": [
        "https://cdnamd-hls-globecast.akamaized.net/live/ramdisk/al_aoula_laayoune/hls_snrt/index.m3u8",
    ],
}


def test_url(url: str) -> bool:
    """Test if URL is accessible"""
    try:
        response = requests.get(url, timeout=TIMEOUT, stream=True, headers={'Range': 'bytes=0-1024'})
        return response.status_code < 400
    except:
        return False


def find_working_variant(channel_name: str, urls: list) -> Optional[str]:
    """Test multiple URL variants and return first working one"""
    for url in urls:
        print(f"    Testing: {url[:60]}...")
        if test_url(url):
            print(f"      ✓ WORKING!")
            return url
        else:
            print(f"      ✗ Failed")
    return None


def search_alternative_repos(channel_name: str) -> Optional[str]:
    """Search Free-TV and other repos for alternative streams"""
    # Clone Free-TV IPTV repo (another major source)
    freetv_dir = Path("/tmp/freetv-iptv")
    if not freetv_dir.exists():
        print("  📥 Cloning Free-TV repo...")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", 
                 "https://github.com/Free-TV/IPTV.git", 
                 str(freetv_dir)],
                check=True, 
                capture_output=True
            )
        except:
            return None
    
    # Search in playlists
    search_files = list(freetv_dir.glob("**/*.m3u"))
    normalized_name = channel_name.lower()
    
    for m3u_file in search_files:
        try:
            with open(m3u_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                if line.startswith('#EXTINF') and normalized_name in line.lower():
                    # Get URL from next non-comment line
                    for j in range(i + 1, min(i + 5, len(lines))):
                        url = lines[j].strip()
                        if url and not url.startswith('#'):
                            # Test it
                            if test_url(url):
                                return url
        except:
            continue
    
    return None


def main():
    print("🇲🇦 Moroccan/Arabic Channel Fixer (Official Sources Priority)\n")
    
    fixes = {}
    
    print("🔍 Testing official SNRT Morocco channels...\n")
    for channel_name, url_variants in OFFICIAL_SNRT_URLS.items():
        print(f"📺 {channel_name}")
        working_url = find_working_variant(channel_name, url_variants)
        
        if working_url:
            fixes[channel_name] = working_url
        else:
            print(f"  ⚠️  All official URLs failed, searching alternatives...")
            alt_url = search_alternative_repos(channel_name)
            if alt_url:
                print(f"    ✓ Found alternative: {alt_url[:60]}")
                fixes[channel_name] = alt_url
            else:
                print(f"    ✗ No working alternative found")
        
        print()
    
    print(f"\n📊 Results: Found {len(fixes)}/{len(OFFICIAL_SNRT_URLS)} working Moroccan channels\n")
    
    if fixes:
        print("✅ Working URLs found:")
        for channel, url in fixes.items():
            print(f"  {channel}: {url}")
        
        print("\n💡 Run the full validate_and_fix.py to apply these and search for other broken channels")
    else:
        print("❌ No working official URLs found - networks may have changed their streaming infrastructure")


if __name__ == "__main__":
    main()
