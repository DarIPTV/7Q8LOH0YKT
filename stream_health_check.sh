#!/bin/bash
# Stream Health Check - every 5 mins, alerts on new failures and recoveries
# Compatible with macOS bash 3.x (no associative arrays)

PROXY="http://localhost:9000"
STATE_FILE="/tmp/stream-health-state.txt"
MATRIX_TARGET="@zdaraoui:matrix.org"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# Load previous down-list (one channel name per line)
prev_down=""
[ -f "$STATE_FILE" ] && prev_down=$(cat "$STATE_FILE")

# Channel names and URLs (parallel arrays)
NAMES=("2M Maroc" "Al Aoula" "Arriadia" "Assadissa" "Tamazight" "Laayoune" "Attakafiya" "Al Maghribia")
URLS=(
    "$PROXY/2m.m3u8"
    "$PROXY/al-aoula.m3u8"
    "$PROXY/arriadia.m3u8"
    "$PROXY/assadissa.m3u8"
    "$PROXY/tamazight.m3u8"
    "$PROXY/laayoune.m3u8"
    "$PROXY/attakafiya.m3u8"
    "$PROXY/al-maghribia.m3u8"
)

failed=()
recovered=()
new_down=()

for i in "${!NAMES[@]}"; do
    name="${NAMES[$i]}"
    url="${URLS[$i]}"

    # Use GET (not HEAD) — proxy only handles GET requests
    resp=$(curl -s --max-time 8 -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    if [ "$resp" = "200" ]; then
        log "✅ $name OK"
        if echo "$prev_down" | grep -qF "$name"; then
            recovered+=("$name")
        fi
    else
        log "❌ $name FAILED"
        new_down+=("$name")
        if ! echo "$prev_down" | grep -qF "$name"; then
            failed+=("$name")
        fi
    fi
done

# Send failure alert (only for newly failed channels)
if [ ${#failed[@]} -gt 0 ]; then
    names=$(printf "%s, " "${failed[@]}"); names="${names%, }"
    msg="📺 Stream alert: ❌ DOWN — $names"
    log "Alerting: $msg"
    openclaw message send --channel matrix --target "$MATRIX_TARGET" --message "$msg"
fi

# Send recovery alert
if [ ${#recovered[@]} -gt 0 ]; then
    names=$(printf "%s, " "${recovered[@]}"); names="${names%, }"
    msg="📺 Stream alert: ✅ RECOVERED — $names"
    log "Recovery: $msg"
    openclaw message send --channel matrix --target "$MATRIX_TARGET" --message "$msg"
fi

# Write new state (one name per line)
printf "%s\n" "${new_down[@]}" > "$STATE_FILE"
log "State: ${new_down[*]:-all clear}"
