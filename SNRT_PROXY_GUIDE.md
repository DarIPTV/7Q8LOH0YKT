# SNRT Local Proxy Guide

## The Problem

SNRT Morocco streams are **token-protected** and **geo-restricted** by Easybroadcast CDN. Direct M3U8 URLs return `403 Forbidden`.

## The Solution: Local Re-Streaming Proxy

Run a proxy on your Mac mini that:
1. Fetches SNRT streams with valid authentication  
2. Re-streams them locally at `http://192.168.8.131:PORT`
3. TiviMate connects to local proxy (no auth needed)

---

## Quick Test (Manual Token Extraction)

**Good for:** Testing if the concept works

### Step 1: Extract Stream URL with Token

1. Open https://snrtlive.ma/fr/al-aoula in **Chrome/Firefox**
2. Press `F12` → **Network** tab
3. Filter by typing: `m3u8`
4. Click play on the video
5. Look for a URL like:
   ```
   https://cdn.live.easybroadcast.io/.../playlist_dvr.m3u8?token=...
   ```
6. **Right-click** → Copy URL

### Step 2: Test Re-Streaming with FFmpeg

```bash
# Replace URL_WITH_TOKEN with the URL you copied
ffmpeg -i "URL_WITH_TOKEN" \
  -c copy -f hls \
  -hls_time 2 -hls_list_size 5 \
  -hls_flags delete_segments \
  http://192.168.8.131:9001/al-aoula.m3u8
```

### Step 3: Test in TiviMate

Add playlist URL: `http://192.168.8.131:9001/al-aoula.m3u8`

**Limitation:** Token expires in a few hours/days - you'd need to repeat extraction.

---

## Full Automated Solution

**Good for:** Production use (set and forget)

### Requirements

```bash
# Install dependencies
pip3 install playwright requests
playwright install chromium
brew install ffmpeg  # Already installed
```

### Components

1. **Token Extractor** (`snrt_token_extractor.py`)
   - Uses headless browser to visit snrtlive.ma
   - Captures real m3u8 URLs with tokens from network traffic
   - Refreshes tokens periodically

2. **FFmpeg Re-Streamer** (automated)
   - Takes extracted URLs
   - Re-streams locally without auth requirements
   - Handles stream restarts on token expiry

3. **LaunchD Service** (keeps it running)
   - Starts on boot
   - Restarts on failure
   - Runs in background

### Architecture

```
SNRT Website
  snrtlive.ma
      ↓
Headless Browser (Playwright)
  - Loads page
  - Extracts m3u8 + token
      ↓
FFmpeg Re-Streamer
  - Fetches authenticated stream
  - Serves locally: 192.168.8.131:9001-9006
      ↓
TiviMate (on Fire Stick)
  - Connects to local proxy
  - No authentication needed
```

### Setup

```bash
cd ~/.openclaw/workspace-dariptv/iptv-playlist

# Test token extraction
python3 snrt_token_extractor.py

# If successful, you'll see:
#   ✅ al-aoula: https://cdn.live.easybroadcast.io/.../playlist_dvr.m3u8?...
#   📥 Saved to snrt_streams.json
```

### Create Master Re-Streaming Script

```bash
nano snrt_restream.sh
```

```bash
#!/bin/bash
# SNRT Re-Streaming Service

while true; do
    # Extract fresh tokens
    python3 snrt_token_extractor.py
    
    # Read extracted URLs
    AL_AOULA=$(jq -r '.["al-aoula"]' snrt_streams.json)
    ARRIADIA=$(jq -r '.arriadia' snrt_streams.json)
    ASSADISSA=$(jq -r '.assadissa' snrt_streams.json)
    
    # Start ffmpeg re-streamers in background
    if [ "$AL_AOULA" != "null" ]; then
        ffmpeg -i "$AL_AOULA" -c copy -f hls \
          -hls_time 2 -hls_list_size 5 \
          -hls_flags delete_segments \
          -listen 1 http://192.168.8.131:9001/stream.m3u8 &
    fi
    
    # Refresh tokens every 6 hours
    sleep 21600
    
    # Kill old ffmpeg processes
    pkill -f "ffmpeg.*easybroadcast"
done
```

```bash
chmod +x snrt_restream.sh
```

### Create LaunchD Service

```bash
nano ~/Library/LaunchAgents/com.dariptv.snrt-proxy.plist
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.dariptv.snrt-proxy</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/Users/zak/.openclaw/workspace-dariptv/iptv-playlist/snrt_restream.sh</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>/tmp/snrt-proxy.log</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/snrt-proxy-error.log</string>
</dict>
</plist>
```

```bash
# Load service
launchctl load ~/Library/LaunchAgents/com.dariptv.snrt-proxy.plist

# Check status
launchctl list | grep dariptv

# View logs
tail -f /tmp/snrt-proxy.log
```

### TiviMate Playlist

Once running, add to TiviMate:

```m3u
#EXTM3U
#EXTINF:-1 group-title="SNRT Morocco",Al Aoula
http://192.168.8.131:9001/stream.m3u8
#EXTINF:-1 group-title="SNRT Morocco",Arriadia
http://192.168.8.131:9002/stream.m3u8
#EXTINF:-1 group-title="SNRT Morocco",Assadissa
http://192.168.8.131:9003/stream.m3u8
```

---

## Troubleshooting

### Token Extraction Fails
- SNRT changed their player structure
- Update `snrt_token_extractor.py` with new selectors
- Check browser console for errors

### Stream Cuts Out
- Token expired → extractor should refresh
- Check logs: `tail -f /tmp/snrt-proxy.log`
- Manually restart: `launchctl kickstart gui/$(id -u)/com.dariptv.snrt-proxy`

### 403 Forbidden
- Easybroadcast blocking automation
- Try adding delays/user-agent spoofing
- May need to rotate IPs or use residential proxy

---

## Alternative: Just Use SNRT App

If the proxy is too complex:
- Install **SNRT Live app** on Fire Stick
- Use it alongside TiviMate
- You get: Official SNRT channels
- You keep: TiviMate for other 34 channels

**Simplest solution for your mother!**

---

## Current Status

- ✅ Mac mini IP: 192.168.8.131
- ✅ FFmpeg installed
- ✅ Python scripts created
- ⏳ Playwright installation needed
- ⏳ Token extraction to be tested
- ⏳ LaunchD service to be configured

**Next Steps:** You decide:
1. Quick manual test (5 min setup, tokens expire)
2. Full automation (30 min setup, maintenance-free)
3. Use SNRT app alongside TiviMate (easiest)
