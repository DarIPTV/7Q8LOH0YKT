#!/usr/bin/env python3
"""
IPTV Channel Validator & Auto-Fixer
Checks channels in Arabic.m3u and replaces broken ones with working alternatives from iptv-org
"""

import re
import requests
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import sys

# Config
PLAYLIST_FILE = "Arabic.m3u"
IPTV_ORG_DIR = "/tmp/iptv-org/streams"
TIMEOUT = 10  # seconds for stream check
BACKUP_DIR = "backups"

# Arabic country codes to search for replacements
ARABIC_COUNTRIES = ["ma", "sa", "ae", "eg", "lb", "dz", "tn", "ly", "sd", "sy", "jo", "ye", "iq", "kw", "bh", "qa", "om"]


class Channel:
    def __init__(self, metadata: str, url: str):
        self.metadata = metadata  # Full #EXTINF line
        self.url = url
        self.name = self._extract_name()
        self.is_working = None
        
    def _extract_name(self) -> str:
        """Extract channel name from metadata"""
        # Pattern: last comma-separated value is the name
        match = re.search(r',\s*(.+?)$', self.metadata)
        if match:
            return match.group(1).strip()
        return "Unknown"
    
    def normalize_name(self) -> str:
        """Normalize name for matching (lowercase, remove special chars)"""
        name = self.name.lower()
        # Remove common words and normalize
        name = re.sub(r'\b(tv|hd|channel|arabic|arb|international|inter)\b', '', name)
        name = re.sub(r'[^a-z0-9\s]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        return name
    
    def check_status(self) -> bool:
        """Check if stream URL is accessible"""
        if not self.url or self.url.startswith('#') or 'git@' in self.url:
            self.is_working = False
            return False
            
        try:
            # Try HEAD request first (faster)
            response = requests.head(self.url, timeout=TIMEOUT, allow_redirects=True)
            if response.status_code < 400:
                self.is_working = True
                return True
            
            # If HEAD fails, try GET with range (streaming endpoints often don't support HEAD)
            response = requests.get(self.url, timeout=TIMEOUT, stream=True, headers={'Range': 'bytes=0-1024'})
            self.is_working = response.status_code < 400
            return self.is_working
            
        except Exception as e:
            print(f"  ✗ {self.name}: {str(e)[:50]}")
            self.is_working = False
            return False


def parse_m3u(file_path: Path) -> List[Channel]:
    """Parse M3U file into Channel objects"""
    channels = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('#EXTINF'):
            metadata = line
            # Next non-comment line should be the URL
            i += 1
            while i < len(lines) and (lines[i].strip().startswith('#') or not lines[i].strip()):
                i += 1
            
            if i < len(lines):
                url = lines[i].strip()
                channels.append(Channel(metadata, url))
        
        i += 1
    
    return channels


def search_iptv_org(channel_name: str) -> Optional[str]:
    """Search iptv-org streams for a replacement URL by channel name"""
    normalized_target = channel_name.lower()
    
    # Search Arabic country playlists
    for country_code in ARABIC_COUNTRIES:
        playlist_file = Path(IPTV_ORG_DIR) / f"{country_code}.m3u"
        if not playlist_file.exists():
            continue
        
        try:
            with open(playlist_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                if line.startswith('#EXTINF'):
                    # Extract name from this line
                    match = re.search(r',\s*(.+?)$', line)
                    if match:
                        name = match.group(1).strip().lower()
                        
                        # Simple fuzzy matching
                        if normalized_target in name or name in normalized_target:
                            # Get the URL from next non-comment line
                            for j in range(i + 1, min(i + 5, len(lines))):
                                url_line = lines[j].strip()
                                if url_line and not url_line.startswith('#'):
                                    return url_line
        except Exception as e:
            print(f"  Warning: Error reading {country_code}.m3u: {e}")
            continue
    
    return None


def create_backup(file_path: Path):
    """Create timestamped backup of playlist"""
    backup_dir = file_path.parent / BACKUP_DIR
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"{file_path.stem}_{timestamp}.m3u"
    
    with open(file_path, 'r', encoding='utf-8') as src:
        with open(backup_file, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    
    print(f"✓ Backup created: {backup_file}")
    return backup_file


def write_m3u(file_path: Path, channels: List[Channel]):
    """Write channels back to M3U file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U \n")
        for channel in channels:
            f.write(f"{channel.metadata}\n")
            f.write(f"{channel.url}\n")


def main():
    print("🔍 IPTV Channel Validator & Auto-Fixer\n")
    
    playlist_path = Path(PLAYLIST_FILE)
    if not playlist_path.exists():
        print(f"❌ Error: {PLAYLIST_FILE} not found")
        sys.exit(1)
    
    # Ensure iptv-org repo is available
    if not Path(IPTV_ORG_DIR).exists():
        print("📥 Cloning iptv-org repository...")
        subprocess.run(["git", "clone", "--depth", "1", 
                       "https://github.com/iptv-org/iptv.git", 
                       "/tmp/iptv-org"], check=True)
    
    # Parse playlist
    print(f"📋 Parsing {PLAYLIST_FILE}...")
    channels = parse_m3u(playlist_path)
    print(f"   Found {len(channels)} channels\n")
    
    # Validate channels
    print("🔎 Checking channel availability...")
    broken_channels = []
    working_channels = []
    
    for i, channel in enumerate(channels, 1):
        print(f"[{i}/{len(channels)}] {channel.name}...", end=" ")
        if channel.check_status():
            print("✓")
            working_channels.append(channel)
        else:
            print("✗ BROKEN")
            broken_channels.append(channel)
    
    print(f"\n📊 Results: {len(working_channels)} working, {len(broken_channels)} broken\n")
    
    if not broken_channels:
        print("✨ All channels are working! No fixes needed.")
        return
    
    # Try to fix broken channels
    print("🔧 Searching for replacements...\n")
    fixed_count = 0
    
    for channel in broken_channels:
        print(f"  Searching for: {channel.name}...")
        replacement_url = search_iptv_org(channel.normalize_name())
        
        if replacement_url:
            # Verify replacement works
            temp_channel = Channel(channel.metadata, replacement_url)
            if temp_channel.check_status():
                print(f"    ✓ Found working replacement")
                channel.url = replacement_url
                channel.is_working = True
                fixed_count += 1
            else:
                print(f"    ✗ Replacement also broken")
        else:
            print(f"    ✗ No replacement found")
    
    print(f"\n✨ Fixed {fixed_count}/{len(broken_channels)} broken channels\n")
    
    if fixed_count > 0:
        # Create backup
        create_backup(playlist_path)
        
        # Write updated playlist
        write_m3u(playlist_path, channels)
        print(f"✓ Updated {PLAYLIST_FILE}")
        
        # Show remaining issues
        still_broken = [ch for ch in channels if not ch.is_working]
        if still_broken:
            print(f"\n⚠️  {len(still_broken)} channels still broken:")
            for ch in still_broken:
                print(f"   - {ch.name}")
    else:
        print("⚠️  No fixes applied - no working replacements found")


if __name__ == "__main__":
    main()
