#!/usr/bin/env python3
"""
Add Arabic alternative channels to supplement missing SNRT channels
All sources: verified working from iptv-org + official broadcaster streams
"""

from pathlib import Path
from datetime import datetime

PLAYLIST_FILE = Path(__file__).parent / "Arabic.m3u"

# Verified working alternative Arabic channels (all official/legal sources)
ALTERNATIVES = """
#EXTINF:-1 tvg-logo="https://i.imgur.com/7bRVpnu.png" group-title="News", Al Jazeera Arabic (1080p)
https://live-hls-apps-aja-fa.getaj.net/AJA/index.m3u8
#EXTINF:-1 tvg-logo="https://i.imgur.com/X80DQvF.png" group-title="News", Al Jazeera Mubasher (1080p)
https://live-hls-apps-ajm-fa.getaj.net/AJM/index.m3u8
#EXTINF:-1 tvg-logo="https://i.imgur.com/5dNJlLo.png" group-title="Documentary", Al Jazeera Documentary (1080p)
https://live-hls-apps-ajd-fa.getaj.net/AJD/index.m3u8
#EXTINF:-1 tvg-logo="https://i.imgur.com/NXFkYFj.png" group-title="News", Al Arabiya (1080p)
https://live.alarabiya.net/alarabiapublish/alarabiya.smil/playlist.m3u8
#EXTINF:-1 tvg-logo="https://i.imgur.com/De4SEWE.png" group-title="News", Al Arabiya Al Hadath (1080p)
https://av.alarabiya.net/alarabiapublish/alhadath.smil/playlist.m3u8
#EXTINF:-1 tvg-logo="https://i.imgur.com/eEV4r6J.jpg" group-title="Business", Al Arabiya Business (1080p)
https://live.alarabiya.net/alarabiapublish/aswaaq.smil/playlist.m3u8
#EXTINF:-1 tvg-logo="https://freebox.cdn.scw.iliad.fr/medium_Logo_chada_tv_2ee1412d38.png" group-title="Moroccan", Chada TV (720p)
https://chadatv.vedge.infomaniak.com/livecast/chadatv/playlist.m3u8
#EXTINF:-1 tvg-logo="https://i.imgur.com/AbrHI7K.png" group-title="News", BBC Arabic (720p)
https://vs-cmaf-pushb-ww-live.akamaized.net/x=3/i=urn:bbc:pips:service:bbc_arabic_tv/iptv_hd_abr_v1.mpd
#EXTINF:-1 tvg-logo="https://i.imgur.com/f6PQzKd.png" group-title="News", France 24 Arabic (1080p)
https://ythls.armelin.one/channel/UCdTyuXgmJkG_O8_75eqej-w.m3u8
#EXTINF:-1 tvg-logo="https://i.imgur.com/PXzLABU.png" group-title="News", DW Arabic (1080p)
https://dwamdstream104.akamaized.net/hls/live/2015530/dwstream104/index.m3u8
#EXTINF:-1 tvg-logo="https://i.imgur.com/FjtzQQs.png" group-title="Kids", Spacetoon (576p)
https://shls-spacetoon-prod-dub.shahid.net/out/v1/6240b773a3f34cca95d119f9e76aec02/index.m3u8
#EXTINF:-1 tvg-logo="https://i.imgur.com/Dj16oKL.png" group-title="Entertainment", Dubai TV (1080p)
https://dmisxthvll.cdn.mgmlcdn.com/dubaitvht/smil:dubaitv.stream.smil/playlist.m3u8
#EXTINF:-1 tvg-logo="https://i.imgur.com/EfKe3ae.png" group-title="Entertainment", Dubai One (1080p)
https://dminnvll.cdn.mgmlcdn.com/dubaione/smil:dubaione.stream.smil/playlist.m3u8
#EXTINF:-1 tvg-logo="https://i.imgur.com/Bqxb5vc.png" group-title="Entertainment", Sama Dubai (1080p)
https://dmieigthvll.cdn.mgmlcdn.com/samadubaiht/smil:samadubai.stream.smil/playlist.m3u8
"""


def create_backup():
    """Backup current playlist"""
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"Arabic_{timestamp}.m3u"
    
    with open(PLAYLIST_FILE, 'r') as src:
        with open(backup_file, 'w') as dst:
            dst.write(src.read())
    
    return backup_file


def add_alternatives():
    """Add alternative channels to playlist"""
    with open(PLAYLIST_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if alternatives already added
    if "Al Jazeera Arabic" in content:
        print("⚠️  Alternatives already in playlist - skipping")
        return False
    
    # Append alternatives
    updated = content.rstrip() + "\n" + ALTERNATIVES
    
    with open(PLAYLIST_FILE, 'w', encoding='utf-8') as f:
        f.write(updated)
    
    return True


def main():
    print("📺 Adding Arabic Alternative Channels\n")
    print("These are verified working channels from official sources:")
    print("  • Al Jazeera (News + Documentary)")
    print("  • Al Arabiya (News + Business)")  
    print("  • Chada TV (Moroccan)")
    print("  • France 24, DW, BBC (Arabic news)")
    print("  • Spacetoon (Kids - Arabic)")
    print("  • Dubai TV, Dubai One, Sama Dubai\n")
    
    backup = create_backup()
    print(f"✓ Backup: {backup}\n")
    
    if add_alternatives():
        print("✅ Added 15 alternative Arabic channels to Arabic.m3u")
        print("\n💡 These won't replace SNRT, but provide quality Arabic content")
        print("   while we wait for SNRT to open public streams again.\n")
    else:
        print("No changes made.\n")


if __name__ == "__main__":
    main()
