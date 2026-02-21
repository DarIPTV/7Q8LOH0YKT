# SNRT Local Proxy - Manual Setup (Recommended)

## Why Manual Instead of Automated?

- Playwright has issues on macOS  
- SNRT's player uses complex JavaScript that blocks automation
- Manual extraction is 5 minutes, automation is 2 hours of debugging

**Once you extract the URLs once, they work for days/weeks.**

---

## Step-by-Step Setup

### 1. Extract Stream URLs (5 minutes, do once)

**For each channel you want:**

1. **Open in Chrome:** https://snrtlive.ma/fr/al-aoula
2. **Press F12** → **Network** tab
3. **Filter by:** `m3u8`
4. **Click play** on the video
5. **Look for URL** like:
   ```
   https://cdn.live.easybroadcast.io/.../playlist_dvr.m3u8?token=...
   ```
6. **Right-click → Copy → Copy URL**
7. **Paste it below** (we'll use it in next step)

**Repeat for:**
- Al Aoula: https://snrtlive.ma/fr/al-aoula
- Arriadia: https://snrtlive.ma/fr/arryadia  
- Assadissa: https://snrtlive.ma/fr/assadissa
- Al Maghribia: https://snrtlive.ma/fr/almaghribia

---

### 2. Create Re-Streaming Script

```bash
cd ~/.openclaw/workspace-dariptv/iptv-playlist
nano snrt_restream_simple.sh
```

**Paste this** (replace URLs with ones you extracted):

```bash
#!/bin/bash
# SNRT Re-Streaming Proxy
# Serves SNRT channels locally for TiviMate

# REPLACE THESE WITH YOUR EXTRACTED URLs:
AL_AOULA_URL="https://cdn.live.easybroadcast.io/...PASTE_YOUR_URL_HERE..."
ARRIADIA_URL="https://cdn.live.easybroadcast.io/...PASTE_YOUR_URL_HERE..."
ASSADISSA_URL="https://cdn.live.easybroadcast.io/...PASTE_YOUR_URL_HERE..."
ALMAGHRIBIA_URL="https://cdn.live.easybroadcast.io/...PASTE_YOUR_URL_HERE..."

echo "Starting SNRT Re-Streaming Proxy..."
echo "Local IP: 192.168.8.131"
echo ""

# Kill any existing streams
pkill -f "ffmpeg.*9001\|ffmpeg.*9002\|ffmpeg.*9003\|ffmpeg.*9004"

# Re-stream Al Aoula on port 9001
if [ -n "$AL_AOULA_URL" ] && [ "$AL_AOULA_URL" != "https://cdn.live.easybroadcast.io/...PASTE_YOUR_URL_HERE..." ]; then
    echo "✓ Starting Al Aoula on http://192.168.8.131:9001"
    ffmpeg -re -i "$AL_AOULA_URL" \
      -c copy -f hls \
      -hls_time 2 -hls_list_size 5 \
      -hls_flags delete_segments+append_list \
      -hls_segment_filename "/tmp/snrt_aoula_%03d.ts" \
      -method PUT -listen 1 \
      http://192.168.8.131:9001/stream.m3u8 > /tmp/snrt_aoula.log 2>&1 &
fi

# Re-stream Arriadia on port 9002
if [ -n "$ARRIADIA_URL" ] && [ "$ARRIADIA_URL" != "https://cdn.live.easybroadcast.io/...PASTE_YOUR_URL_HERE..." ]; then
    echo "✓ Starting Arriadia on http://192.168.8.131:9002"
    ffmpeg -re -i "$ARRIADIA_URL" \
      -c copy -f hls \
      -hls_time 2 -hls_list_size 5 \
      -hls_flags delete_segments+append_list \
      -hls_segment_filename "/tmp/snrt_arriadia_%03d.ts" \
      -method PUT -listen 1 \
      http://192.168.8.131:9002/stream.m3u8 > /tmp/snrt_arriadia.log 2>&1 &
fi

# Re-stream Assadissa on port 9003
if [ -n "$ASSADISSA_URL" ] && [ "$ASSADISSA_URL" != "https://cdn.live.easybroadcast.io/...PASTE_YOUR_URL_HERE..." ]; then
    echo "✓ Starting Assadissa on http://192.168.8.131:9003"
    ffmpeg -re -i "$ASSADISSA_URL" \
      -c copy -f hls \
      -hls_time 2 -hls_list_size 5 \
      -hls_flags delete_segments+append_list \
      -hls_segment_filename "/tmp/snrt_assadissa_%03d.ts" \
      -method PUT -listen 1 \
      http://192.168.8.131:9003/stream.m3u8 > /tmp/snrt_assadissa.log 2>&1 &
fi

# Re-stream Al Maghribia on port 9004
if [ -n "$ALMAGHRIBIA_URL" ] && [ "$ALMAGHRIBIA_URL" != "https://cdn.live.easybroadcast.io/...PASTE_YOUR_URL_HERE..." ]; then
    echo "✓ Starting Al Maghribia on http://192.168.8.131:9004"
    ffmpeg -re -i "$ALMAGHRIBIA_URL" \
      -c copy -f hls \
      -hls_time 2 -hls_list_size 5 \
      -hls_flags delete_segments+append_list \
      -hls_segment_filename "/tmp/snrt_maghribia_%03d.ts" \
      -method PUT -listen 1 \
      http://192.168.8.131:9004/stream.m3u8 > /tmp/snrt_maghribia.log 2>&1 &
fi

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "   SNRT Proxy Running - Add these URLs to TiviMate:"
echo "══════════════════════════════════════════════════════════════"
echo "http://192.168.8.131:9001/stream.m3u8  (Al Aoula)"
echo "http://192.168.8.131:9002/stream.m3u8  (Arriadia)"
echo "http://192.168.8.131:9003/stream.m3u8  (Assadissa)"
echo "http://192.168.8.131:9004/stream.m3u8  (Al Maghribia)"
echo "══════════════════════════════════════════════════════════════"
echo ""
echo "To check logs:  tail -f /tmp/snrt_*.log"
echo "To stop:        pkill -f 'ffmpeg.*9001'"
echo ""
```

**Save and make executable:**
```bash
chmod +x snrt_restream_simple.sh
```

---

### 3. Test It

```bash
./snrt_restream_simple.sh
```

**You should see:**
```
✓ Starting Al Aoula on http://192.168.8.131:9001
✓ Starting Arriadia on http://192.168.8.131:9002
...
```

**Test in VLC** (on your Mac):
```bash
open -a VLC http://192.168.8.131:9001/stream.m3u8
```

If it plays → SUCCESS! ✅

---

### 4. Add to TiviMate

On your Fire Stick in TiviMate:

**Settings → Playlists → Add Playlist → URL:**
```
http://192.168.8.131:9001/stream.m3u8
```

Or create a master playlist file and add that instead.

---

### 5. Auto-Start on Boot (Optional)

**Create LaunchAgent:**
```bash
nano ~/Library/LaunchAgents/com.dariptv.snrt.plist
```

**Paste:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.dariptv.snrt</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/Users/zak/.openclaw/workspace-dariptv/iptv-playlist/snrt_restream_simple.sh</string>
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

**Enable:**
```bash
launchctl load ~/Library/LaunchAgents/com.dariptv.snrt.plist
```

**Check status:**
```bash
launchctl list | grep dariptv
```

---

## When URLs Expire

If streams stop working (days/weeks later):
1. Extract fresh URLs again (repeat Step 1)
2. Edit `snrt_restream_simple.sh` with new URLs
3. Restart: `./snrt_restream_simple.sh`

**That's it!** Much simpler than fighting with browser automation.

---

## Create Master M3U Playlist (Optional)

```bash
cat > snrt_local.m3u << 'EOF'
#EXTM3U
#EXTINF:-1 tvg-logo="" group-title="SNRT Morocco",Al Aoula
http://192.168.8.131:9001/stream.m3u8
#EXTINF:-1 tvg-logo="" group-title="SNRT Morocco",Arriadia
http://192.168.8.131:9002/stream.m3u8
#EXTINF:-1 tvg-logo="" group-title="SNRT Morocco",Assadissa
http://192.168.8.131:9003/stream.m3u8
#EXTINF:-1 tvg-logo="" group-title="SNRT Morocco",Al Maghribia
http://192.168.8.131:9004/stream.m3u8
EOF
```

**Then in TiviMate, add:**
```
http://192.168.8.131:8000/snrt_local.m3u
```

(After starting a simple HTTP server: `python3 -m http.server 8000` in the playlist directory)

---

## Summary

✅ **Pros:**
- Works reliably
- 5-minute setup
- URLs valid for days/weeks
- No complex automation needed

⚠️ **Cons:**
- Manual URL refresh when tokens expire (rare)

This is the **pragmatic solution** that actually works!
