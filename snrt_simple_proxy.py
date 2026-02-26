#!/usr/bin/env python3
"""
Minimal SNRT Proxy - Raw socket implementation
"""
import socket
import threading
import requests
import re
import sys
import json
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse

PORT = 9000
TOKEN_FILE = "snrt_streams.json"

# Default fallback URLs (without tokens)
DEFAULT_CHANNELS = {
    "al-aoula": "https://cdn.live.easybroadcast.io/abr_corp/73_aloula_w1dqfwm/playlist_dvr.m3u8",
    "arriadia": "https://cdn.live.easybroadcast.io/abr_corp/73_arryadia_k2tgcj0/playlist_dvr.m3u8",
    "assadissa": "https://cdn.live.easybroadcast.io/abr_corp/73_assadissa_7b7u5n1/playlist_dvr.m3u8",
    "al-maghribia": "https://cdn.live.easybroadcast.io/abr_corp/73_almaghribia_83tz85q/playlist_dvr.m3u8",
    "tamazight": "https://cdn.live.easybroadcast.io/abr_corp/73_tamazight_tccybxt/playlist_dvr.m3u8",
    "laayoune": "https://cdn.live.easybroadcast.io/abr_corp/73_laayoune_pgagr52/playlist_dvr.m3u8",
    # 2M Maroc — static CloudFront URL (no token needed)
    "2m": "https://d2qh3gh0k5vp3v.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-n6pess5lwbghr/2M_ES.m3u8",
    "attakafiya": "https://cdn.live.easybroadcast.io/abr_corp/73_arrabia_hthcj4p/playlist_dvr.m3u8"
}

def load_channels():
    """Load channels from token file or use defaults"""
    channels = DEFAULT_CHANNELS.copy()
    
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                token_data = json.load(f)
            
            # Update channels with tokenized URLs
            for channel_id, url in token_data.items():
                if url and url.strip():
                    channels[channel_id] = url
            
            # Get file modification time
            mtime = os.path.getmtime(TOKEN_FILE)
            age = datetime.now().timestamp() - mtime
            age_hours = age / 3600
            
            print(f"📥 Loaded tokens from {TOKEN_FILE} (age: {age_hours:.1f}h)", flush=True)
        except Exception as e:
            print(f"⚠️  Error loading tokens: {e}, using defaults", flush=True)
    else:
        print(f"⚠️  No token file found, using default URLs (will likely be blocked)", flush=True)
    
    return channels

CHANNELS = load_channels()

def fetch_m3u8(url):
    """Fetch M3U8 playlist with proper headers"""
    headers = {
        'Referer': 'https://snrt.player.easybroadcast.io/',
        'Origin': 'https://snrtlive.ma',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.text
        return None
    except:
        return None

def rewrite_m3u8(content, base_url):
    """Rewrite relative URLs in m3u8 to absolute CDN URLs with token params"""
    # Extract token query string from base URL
    parsed = urlparse(base_url)
    token_params = parsed.query  # "token=X&expires=Y&token_path=Z"

    # Base directory (strip filename)
    base_dir = base_url.split('?')[0].rsplit('/', 1)[0] + '/'

    lines = content.split('\n')
    rewritten = []
    for line in lines:
        line = line.rstrip('\r')
        if line.startswith('#') or not line.strip():
            rewritten.append(line)
        else:
            if line.startswith('http'):
                # Already absolute — append token if missing
                if '?' not in line and token_params:
                    rewritten.append(f"{line}?{token_params}")
                else:
                    rewritten.append(line)
            else:
                # Relative URL — resolve against base directory and add token
                abs_url = urljoin(base_dir, line)
                if token_params:
                    rewritten.append(f"{abs_url}?{token_params}")
                else:
                    rewritten.append(abs_url)
    return '\n'.join(rewritten)


def reload_channels():
    """Reload channels from token file"""
    global CHANNELS
    CHANNELS = load_channels()

def handle_client(client_socket, addr):
    """Handle incoming client connection"""
    try:
        request = client_socket.recv(4096).decode('utf-8')
        lines = request.split('\r\n')
        if not lines:
            client_socket.close()
            return
        
        # Parse GET request
        request_line = lines[0]
        if not request_line.startswith('GET'):
            client_socket.close()
            return
        
        path = request_line.split()[1]
        
        # Reload tokens endpoint
        if path == "/reload":
            reload_channels()
            content = "Tokens reloaded"
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(content)}\r\n\r\n{content}"
            client_socket.sendall(response.encode('utf-8'))
        
        # Root - show playlist
        elif path == "/" or path == "/playlist.m3u":
            content = "#EXTM3U\n"
            for channel_id, _ in CHANNELS.items():
                content += f'#EXTINF:-1 group-title="SNRT Morocco",{channel_id.title()}\n'
                content += f'http://192.168.8.131:{PORT}/{channel_id}.m3u8\n'
            
            response = f"HTTP/1.1 200 OK\r\nContent-Type: application/vnd.apple.mpegurl\r\nContent-Length: {len(content)}\r\n\r\n{content}"
            client_socket.sendall(response.encode('utf-8'))
        
        # Channel request
        else:
            channel_id = path.strip('/').replace('.m3u8', '')
            if channel_id in CHANNELS:
                cdn_url = CHANNELS[channel_id]
                m3u8_data = fetch_m3u8(cdn_url)
                if m3u8_data:
                    # Rewrite relative URLs to absolute CDN URLs with token
                    m3u8_data = rewrite_m3u8(m3u8_data, cdn_url)
                    encoded = m3u8_data.encode('utf-8')
                    response = f"HTTP/1.1 200 OK\r\nContent-Type: application/vnd.apple.mpegurl\r\nContent-Length: {len(encoded)}\r\n\r\n"
                    client_socket.sendall(response.encode('utf-8') + encoded)
                    print(f"  ✅ Served {channel_id} ({len(encoded)}b, rewritten)", flush=True)
                else:
                    error = "Stream unavailable"
                    response = f"HTTP/1.1 503 Service Unavailable\r\nContent-Length: {len(error)}\r\n\r\n{error}"
                    client_socket.sendall(response.encode('utf-8'))
                    print(f"  ❌ {channel_id}: upstream 403/timeout", flush=True)
            else:
                error = "Not found"
                response = f"HTTP/1.1 404 Not Found\r\nContent-Length: {len(error)}\r\n\r\n{error}"
                client_socket.sendall(response.encode('utf-8'))
    
    except Exception as e:
        print(f"Error handling {addr}: {e}", file=sys.stderr)
    finally:
        client_socket.close()

def auto_reload_tokens():
    """Background thread to periodically check and reload tokens"""
    import time
    while True:
        time.sleep(300)  # Check every 5 minutes
        if os.path.exists(TOKEN_FILE):
            try:
                # Check if file was modified
                mtime = os.path.getmtime(TOKEN_FILE)
                if not hasattr(auto_reload_tokens, 'last_mtime'):
                    auto_reload_tokens.last_mtime = mtime
                
                if mtime > auto_reload_tokens.last_mtime:
                    print(f"\n🔄 Token file updated, reloading...", flush=True)
                    reload_channels()
                    auto_reload_tokens.last_mtime = mtime
            except Exception as e:
                print(f"⚠️  Auto-reload error: {e}", flush=True)

def main():
    print("🚀 Starting SNRT Simple Proxy...", flush=True)
    
    # Create socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    print(f"🔧 Binding to 0.0.0.0:{PORT}...", flush=True)
    server.bind(('0.0.0.0', PORT))
    
    print("📡 Listening for connections...", flush=True)
    server.listen(5)
    
    # Start auto-reload thread
    reload_thread = threading.Thread(target=auto_reload_tokens, daemon=True)
    reload_thread.start()
    print("🔄 Auto-reload thread started", flush=True)
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          SNRT Simple Proxy - Running                        ║
╠══════════════════════════════════════════════════════════════╣
║  Port:      {PORT}                                           ║
║  Playlist:  http://192.168.8.131:{PORT}/playlist.m3u         ║
║  Reload:    http://192.168.8.131:{PORT}/reload              ║
╚══════════════════════════════════════════════════════════════╝

Press Ctrl+C to stop
""", flush=True)
    
    try:
        while True:
            client, addr = server.accept()
            print(f"📥 Connection from {addr}", flush=True)
            # Handle in thread so we can serve multiple clients
            threading.Thread(target=handle_client, args=(client, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...", flush=True)
    finally:
        server.close()

if __name__ == "__main__":
    main()
