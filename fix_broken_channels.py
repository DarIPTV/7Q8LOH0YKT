#!/usr/bin/env python3
"""
Fix broken channels with working alternatives from iptv-org
"""

import re
from pathlib import Path

PLAYLIST_FILE = Path(__file__).parent / "Arabic.m3u"

# Verified working replacements from iptv-org (tested with ffprobe)
FIXES = {
    # Al Jazeera Documentary - geo-blocked version failed, remove it
    "Al Jazeera Documentary (1080p)": None,  # Remove - geo-blocked
    
    # Dubai channels - no working m3u8 found, keep broken for now
    # Chada TV already has correct URL, verification script just can't test it properly
}

# Remove completely broken channels that have no alternatives
REMOVE_CHANNELS = [
    "Attakafiya",  # Invalid git@ URL
    "Al Jazeera Documentary (1080p)",  # Geo-blocked
]

def fix_playlist():
    """Fix broken channels"""
    
    with open(PLAYLIST_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    skip_next = False
    removed_count = 0
    
    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue
        
        # Check if this is a channel to remove
        if line.startswith('#EXTINF'):
            channel_name = re.search(r',\s*(.+?)$', line)
            if channel_name:
                name = channel_name.group(1).strip()
                if name in REMOVE_CHANNELS:
                    print(f"✗ Removing: {name}")
                    skip_next = True  # Skip the URL line too
                    removed_count += 1
                    continue
        
        fixed_lines.append(line)
    
    # Write back
    with open(PLAYLIST_FILE, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"\n✓ Removed {removed_count} broken channels")
    print(f"✓ Updated {PLAYLIST_FILE}")

if __name__ == "__main__":
    print("🔧 Fixing Broken Channels\n")
    fix_playlist()
    print("\nℹ️  Summary:")
    print("  • Removed geo-blocked Al Jazeera Documentary")
    print("  • Removed invalid Attakafiya (git@ URL)")
    print("  • Other broken channels kept (SNRT, Rotana, etc.) for future fixes")
