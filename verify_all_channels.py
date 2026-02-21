#!/usr/bin/env python3
"""
Comprehensive channel verification - actually tests stream data, not just HTTP status
"""

import re
import subprocess
import requests
from pathlib import Path
from typing import Optional

TIMEOUT = 15
PLAYLIST_FILE = Path(__file__).parent / "Arabic.m3u"


def test_stream_with_ffprobe(url: str) -> bool:
    """Use ffprobe to verify stream is actually playable"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', 
             '-read_intervals', '%+#1', '-timeout', '10000000', url],
            capture_output=True,
            timeout=TIMEOUT
        )
        # If ffprobe can read stream info, it's valid
        return result.returncode == 0 and len(result.stdout) > 10
    except:
        return False


def test_stream_http(url: str) -> bool:
    """Fallback HTTP test"""
    try:
        response = requests.get(url, timeout=TIMEOUT, stream=True, 
                              headers={'Range': 'bytes=0-8192'})
        if response.status_code >= 400:
            return False
        
        # Try to read some actual data
        data = next(response.iter_content(8192), None)
        return data is not None and len(data) > 0
    except:
        return False


def parse_and_test_all():
    """Parse M3U and test every channel"""
    with open(PLAYLIST_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    channels = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('#EXTINF'):
            match = re.search(r',\s*(.+?)$', line)
            channel_name = match.group(1).strip() if match else "Unknown"
            
            # Find URL
            i += 1
            while i < len(lines) and (lines[i].strip().startswith('#') or not lines[i].strip()):
                i += 1
            
            if i < len(lines):
                url = lines[i].strip()
                channels.append((channel_name, url))
        
        i += 1
    
    print(f"📋 Testing {len(channels)} channels...\n")
    
    working = []
    broken = []
    
    for name, url in channels:
        print(f"🔍 {name}...", end=" ", flush=True)
        
        # Skip obviously broken
        if not url or url.startswith('#') or 'git@' in url:
            print("✗ Invalid URL")
            broken.append((name, url, "Invalid URL"))
            continue
        
        # Try ffprobe first (most reliable)
        if test_stream_with_ffprobe(url):
            print("✅ WORKING (verified with ffprobe)")
            working.append((name, url))
        elif test_stream_http(url):
            print("⚠️  HTTP OK (couldn't verify stream data)")
            working.append((name, url))
        else:
            print("✗ BROKEN")
            broken.append((name, url, "Connection failed"))
    
    return working, broken


def main():
    print("🔬 Comprehensive Channel Verification\n")
    print("This will take a few minutes - testing actual stream playback...\n")
    
    working, broken = parse_and_test_all()
    
    print(f"\n{'='*60}")
    print(f"📊 RESULTS: {len(working)} working, {len(broken)} broken")
    print(f"{'='*60}\n")
    
    if working:
        print("✅ WORKING CHANNELS:")
        for name, url in working:
            print(f"  • {name}")
            print(f"    {url[:80]}...")
    
    if broken:
        print(f"\n❌ BROKEN CHANNELS ({len(broken)}):")
        for name, url, reason in broken[:10]:  # Show first 10
            print(f"  • {name}: {reason}")
        if len(broken) > 10:
            print(f"  ... and {len(broken) - 10} more")
    
    print(f"\n💡 Recommendation: {len(working)}/{len(working)+len(broken)} channels working")


if __name__ == "__main__":
    main()
