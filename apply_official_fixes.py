#!/usr/bin/env python3
"""
Apply official working URLs for Moroccan/Arabic channels
Based on latest iptv-org repo + verified sources
"""

import re
import requests
from pathlib import Path
from datetime import datetime

TIMEOUT = 8
PLAYLIST_FILE = Path(__file__).parent / "Arabic.m3u"

# Official working URLs (tested from iptv-org ma.m3u8 + search results)
OFFICIAL_FIXES = {
    # Moroccan channels - verified URLs
    "Al Maghribia": "https://viamotionhsi.netplus.ch/live/eds/almaghribia/browser-HLS8/almaghribia.m3u8",
    "Medi 1 TV Arabic": "https://streaming2.medi1tv.com/live/smil:medi1ar.smil/playlist.m3u8",
    
    # Easybroadcast URLs (from search results - newer SNRT CDN)
    "Al Aoula": "https://cdn.live.easybroadcast.io/ts_corp/73_aloula_w1dqfwm/playlist_dvr.m3u8",
    
    # Alternative sources from iptv-org
    "2M Monde": "https://d2qh3gh0k5vp3v.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-n6pess5lwbghr/2M_ES.m3u8",
}


def test_url(url: str, referer: str = None) -> bool:
    """Test if URL works"""
    headers = {'Range': 'bytes=0-1024'}
    if referer:
        headers['Referer'] = referer
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/134.0'
    
    try:
        response = requests.get(url, timeout=TIMEOUT, stream=True, headers=headers)
        return response.status_code < 400
    except:
        return False


def parse_and_fix_m3u():
    """Parse M3U, apply fixes, return fixed content"""
    with open(PLAYLIST_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    fixes_applied = 0
    
    while i < len(lines):
        line = lines[i]
        
        if line.startswith('#EXTINF'):
            # Extract channel name
            match = re.search(r',\s*(.+?)$', line)
            channel_name = match.group(1).strip() if match else ""
            
            # Keep metadata line
            fixed_lines.append(line)
            i += 1
            
            # Find URL line
            while i < len(lines) and (lines[i].strip().startswith('#') or not lines[i].strip()):
                fixed_lines.append(lines[i])
                i += 1
            
            if i < len(lines):
                current_url = lines[i].strip()
                
                # Check if we have an official fix for this channel
                if channel_name in OFFICIAL_FIXES:
                    new_url = OFFICIAL_FIXES[channel_name]
                    
                    # Test it
                    print(f"Testing {channel_name}...", end=" ")
                    if test_url(new_url):
                        print(f"✓ Working!")
                        fixed_lines.append(new_url)
                        fixes_applied += 1
                    else:
                        print(f"✗ Failed, keeping original")
                        fixed_lines.append(current_url)
                else:
                    fixed_lines.append(current_url)
                
                i += 1
        else:
            fixed_lines.append(line)
            i += 1
    
    return '\n'.join(fixed_lines), fixes_applied


def create_backup():
    """Backup current playlist"""
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"Arabic_{timestamp}.m3u"
    
    with open(PLAYLIST_FILE, 'r') as src:
        with open(backup_file, 'w') as dst:
            dst.write(src.read())
    
    print(f"✓ Backup: {backup_file}\n")


def main():
    print("🔧 Applying Official Fixes for Moroccan/Arabic Channels\n")
    
    create_backup()
    
    print("Testing and applying fixes...\n")
    fixed_content, count = parse_and_fix_m3u()
    
    if count > 0:
        with open(PLAYLIST_FILE, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"\n✅ Applied {count} official fixes to {PLAYLIST_FILE}")
    else:
        print("\n⚠️  No fixes applied (channels either working or no verified replacements)")


if __name__ == "__main__":
    main()
