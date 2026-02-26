#!/bin/bash
#
# SNRT Token Auto-Refresh
# Runs token extractor every hour and reloads proxy
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     SNRT Token Auto-Refresh Service                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Activate venv
source venv/bin/activate

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔄 Extracting fresh tokens (all channels)..."
    
    # Extract all channels in parallel (~36s total)
    python3 extract_all_snrt_channels.py
    
    # Reload proxy immediately after extraction
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📡 Reloading proxy..."
    curl -s http://localhost:9000/reload > /dev/null
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Proxy reloaded"
    
    # Count how many channels have fresh tokens (>2 min remaining)
    FRESH=$(python3 -c "
import json, time, re
with open('snrt_streams.json') as f:
    data = json.load(f)
now = int(time.time())
count = 0
for ch, url in data.items():
    if url:
        m = re.search(r'expires=(\d+)', url)
        if m and int(m.group(1)) > now + 120:
            count += 1
        elif not m:
            count += 1
print(count)
" 2>/dev/null)
    
    TOTAL=$(python3 -c "import json; d=json.load(open('snrt_streams.json')); print(len(d))" 2>/dev/null)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📊 Fresh tokens: $FRESH/$TOTAL channels"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⏰ Next refresh in 2 minutes..."
    echo ""
    
    sleep 120
done
