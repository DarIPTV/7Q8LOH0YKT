#!/bin/bash
#
# SNRT FFmpeg Re-streaming Proxy
# Fetches SNRT streams and re-streams them locally for TiviMate
#

LOCAL_IP="192.168.8.131"
BASE_PORT=9001

# SNRT Channels (we'll need to manually get URLs for now)
declare -A CHANNELS
CHANNELS["al-aoula"]="https://cdn.live.easybroadcast.io/abr_corp/73_aloula_w1dqfwm/playlist_dvr.m3u8"
CHANNELS["arriadia"]="https://cdn.live.easybroadcast.io/abr_corp/73_arriadia_kxb1xd5/playlist_dvr.m3u8"
CHANNELS["assadissa"]="https://cdn.live.easybroadcast.io/abr_corp/73_assadissa_w6qjy65/playlist_dvr.m3u8"
CHANNELS["al-maghribia"]="https://cdn.live.easybroadcast.io/abr_corp/73_almaghribia_uynlwoe/playlist_dvr.m3u8"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          SNRT FFmpeg Proxy - Starting...                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Testing stream accessibility..."
echo ""

# Test if we can access the streams
test_url="${CHANNELS[al-aoula]}"
echo "Testing: $test_url"

# Try with different referer headers
curl -s -I -H "Referer: https://snrtlive.ma/" "$test_url" 2>&1 | grep -i "HTTP\|403\|200"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  SNRT streams are token-protected and currently blocked."
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Manual Token Extraction (for testing):"
echo "   • Open https://snrtlive.ma/fr/al-aoula in browser"
echo "   • Press F12 → Network tab → filter 'm3u8'"
echo "   • Play video → copy the M3U8 URL (includes token)"
echo "   • Paste it into this script to test re-streaming"
echo ""
echo "2. Automated Solution (recommended):"
echo "   • Set up browser automation with Playwright"
echo "   • Extract fresh tokens periodically"
echo "   • Re-stream via ffmpeg"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
