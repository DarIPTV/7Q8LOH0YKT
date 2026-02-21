# DarIPTV - Moroccan/Arabic IPTV Playlist

## 📺 TiviMate Setup

### Playlist URL (Always Fresh - No Cache)

Use this URL in TiviMate - it bypasses GitHub's cache:

**Latest commit URL:**
```
https://raw.githubusercontent.com/DarIPTV/7Q8LOH0YKT/4d5082b5bf199550c25443c3a7bdd917eb6b32ce/Arabic.m3u
```

**Main branch URL (may cache for 5 min):**
```
https://raw.githubusercontent.com/DarIPTV/7Q8LOH0YKT/main/Arabic.m3u
```

### Cache Busting

If TiviMate shows old channels after updates:

1. **In TiviMate:**
   - Settings → Playlists → Select playlist → **Update**
   - Or set Auto-update to 1-6 hours

2. **Force fresh from GitHub:**
   - Add `?t=TIMESTAMP` to URL
   - Or use commit SHA URL (above)

## 📊 Current Status

**Working Channels: 34 total**

### Moroccan (3 channels)
- 2M Monde ✅
- Medi 1 TV Arabic ✅
- Chada TV ✅

### Arabic News (9 channels)
- Al Jazeera Arabic, Mubasher, Documentary ✅
- Al Arabiya, Al Hadath, Business ✅
- BBC Arabic, France 24 Arabic, DW Arabic ✅

### MBC Network (7 channels)
- MBC 1, 4, 5 ✅
- MBC Drama, Bollywood, Wanasah, Masr 2 ✅

### Entertainment (8 channels)
- CBC, CBC Drama ✅
- Dubai TV, Dubai One, Sama Dubai ✅
- Nat Geo Abu Dhabi, Abu Dhabi TV ✅
- Spacetoon (kids) ✅

### UK (7 channels)
- BBC Two/Three/News/Four HD ✅
- CBBC, CBeebies ✅

## ❌ Missing (SNRT Morocco Blocked)

These channels **do not have public M3U8 URLs**:
- Al Aoula
- Arriadia (sports)
- Assadissa
- Al Maghribia
- Attakafiya

**Why:** SNRT Morocco switched to app-only streaming (2024-2025). Streams are geo-blocked and token-protected.

**Alternative:** Use SNRT Live app alongside TiviMate for these channels.

## 🛠️ Scripts

- `validate_and_fix.py` - Check all channels, replace broken ones
- `verify_all_channels.py` - Comprehensive ffprobe verification
- `add_arabic_alternatives.py` - Add Al Jazeera, Al Arabiya, etc.

## 📅 Last Updated

2026-02-21 - Added 15 Arabic alternatives (Al Jazeera, Al Arabiya, Dubai TV)

## 🔄 Auto-Update

Playlist updates automatically pushed to GitHub main branch.

For questions: Contact repo owner
