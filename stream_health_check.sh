#!/bin/bash
# Full playlist health check — parses Arabic.m3u, checks all streams in parallel
# Alerts via Matrix on new failures and recoveries. Runs every 5 min via LaunchAgent.

PLAYLIST="/Users/zak/.openclaw/workspace-dariptv/iptv-playlist/Arabic.m3u"
STATE_FILE="/tmp/stream-health-state.txt"
MATRIX_TARGET="@zdaraoui:matrix.org"
TIMEOUT=10
TMPDIR_CHECKS=$(mktemp -d)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# Load previous down-list (one channel name per line)
prev_down=""
[ -f "$STATE_FILE" ] && prev_down=$(cat "$STATE_FILE")

# --- Parse playlist: extract name→url pairs ---
names=()
urls=()
current_name=""

while IFS= read -r line; do
    line="${line%$'\r'}"  # strip Windows CR
    if [[ "$line" == "#EXTINF"* ]]; then
        # Extract display name: last comma-separated field
        current_name="${line##*,}"
        current_name="${current_name#"${current_name%%[![:space:]]*}"}"  # ltrim
    elif [[ "$line" == http* ]] && [ -n "$current_name" ]; then
        names+=("$current_name")
        urls+=("$line")
        current_name=""
    elif [[ "$line" == "#EXTVLCOPT"* ]]; then
        : # skip VLC options lines
    elif [[ -z "$line" ]] || [[ "$line" == "#"* ]]; then
        : # skip other comments/blanks
    fi
done < "$PLAYLIST"

log "Checking ${#names[@]} streams in parallel..."

# --- Run all curl checks in parallel ---
# Each check writes "200" or "000" to a temp file named by index
for i in "${!urls[@]}"; do
    url="${urls[$i]}"
    (
        code=$(curl -sL --max-time "$TIMEOUT" -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
        echo "$code" > "$TMPDIR_CHECKS/$i"
    ) &
done

# Wait for all background jobs
wait

# --- Collect results ---
failed=()
recovered=()
new_down=()

for i in "${!names[@]}"; do
    name="${names[$i]}"
    code="000"
    [ -f "$TMPDIR_CHECKS/$i" ] && code=$(cat "$TMPDIR_CHECKS/$i")

    if [ "$code" = "200" ] || [ "$code" = "204" ] || [ "$code" = "206" ]; then
        log "✅ $name ($code)"
        if echo "$prev_down" | grep -qF "$name"; then
            recovered+=("$name")
        fi
    else
        log "❌ $name ($code)"
        new_down+=("$name")
        if ! echo "$prev_down" | grep -qF "$name"; then
            failed+=("$name")
        fi
    fi
done

rm -rf "$TMPDIR_CHECKS"

# --- Send alerts ---
if [ ${#failed[@]} -gt 0 ]; then
    names_str=$(printf "%s, " "${failed[@]}"); names_str="${names_str%, }"
    msg="📺 Stream alert: ❌ DOWN (${#failed[@]}) — $names_str"
    log "Alerting: $msg"
    openclaw message send --channel matrix --target "$MATRIX_TARGET" --message "$msg"
fi

if [ ${#recovered[@]} -gt 0 ]; then
    names_str=$(printf "%s, " "${recovered[@]}"); names_str="${names_str%, }"
    msg="📺 Stream alert: ✅ RECOVERED (${#recovered[@]}) — $names_str"
    log "Recovery: $msg"
    openclaw message send --channel matrix --target "$MATRIX_TARGET" --message "$msg"
fi

# --- Save state ---
printf "%s\n" "${new_down[@]}" > "$STATE_FILE"
log "Done. Down: ${#new_down[@]}/${#names[@]}"
