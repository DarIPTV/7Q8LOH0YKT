#!/usr/bin/env python3
"""
Minimal SNRT + Header Proxy - Raw socket implementation
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
    "attakafiya": "https://cdn.live.easybroadcast.io/abr_corp/73_arrabia_hthcj4p/playlist_dvr.m3u8"
}

# Static channels that need custom headers (proxied fully — playlists + segments)
STATIC_CHANNELS = {
    "2m": {
        "master_url": "https://stream-lb.livemediama.com/2m/hls/master.m3u8",
        "base_url":   "https://stream-lb.livemediama.com/2m/hls/",
        "headers": {}
    }
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
    """Fetch M3U8 playlist with SNRT headers"""
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


def send_response(sock, status, content_type, body_bytes):
    response = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body_bytes)}\r\n"
        f"Access-Control-Allow-Origin: *\r\n"
        f"\r\n"
    )
    sock.sendall(response.encode('utf-8') + body_bytes)


def handle_static_channel(client_socket, path, channel_id):
    """Handle a fully-proxied static channel (e.g. 2M) — adds required headers"""
    config = STATIC_CHANNELS[channel_id]
    headers = config['headers']
    base_url = config['base_url']

    # /2m.m3u8         → master playlist
    # /2m/<subpath>    → variant playlist or TS segment (subpath may include subdirs)
    parts = path.strip('/').split('/', 1)
    if len(parts) == 1:
        upstream_url = config['master_url']
        filename = None
        # Effective proxy directory for relative URL resolution in master
        proxy_dir = f"/{channel_id}/"
    else:
        filename = parts[1]
        upstream_url = base_url + filename
        # Preserve subdirectory context (e.g. /2m/stream_2/ for variant playlists)
        proxy_dir = path.rsplit('/', 1)[0] + '/'

    try:
        r = requests.get(upstream_url, headers=headers, timeout=15)
        if r.status_code != 200:
            body = f"Upstream {r.status_code}".encode()
            send_response(client_socket, "503 Service Unavailable", "text/plain", body)
            print(f"  ❌ {channel_id}/{filename}: upstream {r.status_code}", flush=True)
            return

        content_type = r.headers.get('content-type', 'application/octet-stream')
        is_m3u8 = '.m3u8' in (filename or 'master.m3u8') or 'mpegurl' in content_type

        if is_m3u8:
            # Rewrite all relative URLs in the playlist to go back through this proxy.
            # proxy_dir is already set above based on whether this is master or sub-resource.
            lines = r.text.split('\n')
            rewritten = []
            for line in lines:
                line = line.rstrip('\r')
                if line.startswith('#') or not line.strip():
                    rewritten.append(line)
                else:
                    if line.startswith('http'):
                        # Absolute CDN URL — map to proxy path by stripping base_url prefix
                        if line.startswith(base_url):
                            sub = line[len(base_url):]
                            rewritten.append(f"/{channel_id}/{sub}")
                        else:
                            leaf = line.split('/')[-1]
                            rewritten.append(f"/{channel_id}/{leaf}")
                    elif line.startswith('/'):
                        # Root-relative — keep as-is (shouldn't happen but just in case)
                        rewritten.append(line)
                    else:
                        # Relative to current directory — resolve properly
                        rewritten.append(proxy_dir + line)
            body = '\n'.join(rewritten).encode('utf-8')
            send_response(client_socket, "200 OK", "application/vnd.apple.mpegurl", body)
            print(f"  ✅ {channel_id}/{filename or 'master'} ({len(body)}b, rewritten)", flush=True)
        else:
            # Binary (TS segment) — pass straight through
            body = r.content
            send_response(client_socket, "200 OK", content_type, body)
            print(f"  ✅ {channel_id}/{filename} ({len(body)}b, passthrough)", flush=True)

    except Exception as e:
        body = str(e).encode()
        send_response(client_socket, "503 Service Unavailable", "text/plain", body)
        print(f"  ❌ {channel_id}/{filename}: {e}", flush=True)


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

        # --- Static / header-proxied channels (e.g. /2m.m3u8, /2m/<file>) ---
        # Determine channel prefix: /2m.m3u8 → "2m", /2m/foo.ts → "2m"
        path_clean = path.strip('/')
        static_channel_id = path_clean.split('/')[0].replace('.m3u8', '')
        if static_channel_id in STATIC_CHANNELS:
            handle_static_channel(client_socket, path, static_channel_id)
            return
        
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
        
        # SNRT channel request
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
    print("🚀 Starting SNRT + Header Proxy...", flush=True)
    
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
║          SNRT + Header Proxy - Running                      ║
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
