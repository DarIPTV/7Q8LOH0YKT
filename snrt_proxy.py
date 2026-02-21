#!/usr/bin/env python3
"""
SNRT HLS Proxy Server
Proxies Easybroadcast streams with authentication, serves clean M3U8 to local network
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import re
from urllib.parse import urlparse, parse_qs
import threading
import time

PORT = 8080
HOST = "0.0.0.0"  # Listen on all interfaces

# SNRT channel configurations
CHANNELS = {
    "al-aoula": {
        "name": "Al Aoula",
        "url": "https://cdn.live.easybroadcast.io/abr_corp/73_aloula_w1dqfwm/playlist_dvr.m3u8",
        "referer": "https://snrt.player.easybroadcast.io/"
    },
    "arriadia": {
        "name": "Arriadia",
        "url": "https://cdn.live.easybroadcast.io/abr_corp/73_arriadia_kxb1xd5/playlist_dvr.m3u8",
        "referer": "https://snrt.player.easybroadcast.io/"
    },
    "assadissa": {
        "name": "Assadissa",
        "url": "https://cdn.live.easybroadcast.io/abr_corp/73_assadissa_w6qjy65/playlist_dvr.m3u8",
        "referer": "https://snrt.player.easybroadcast.io/"
    },
    "al-maghribia": {
        "name": "Al Maghribia",
        "url": "https://cdn.live.easybroadcast.io/abr_corp/73_almaghribia_uynlwoe/playlist_dvr.m3u8",
        "referer": "https://snrt.player.easybroadcast.io/"
    },
    "tamazight": {
        "name": "Tamazight",
        "url": "https://cdn.live.easybroadcast.io/abr_corp/73_tamazight_tccybxt/playlist_dvr.m3u8",
        "referer": "https://snrt.player.easybroadcast.io/"
    },
    "laayoune": {
        "name": "Al Aoula Laayoune",
        "url": "https://cdn.live.easybroadcast.io/abr_corp/73_laayoune_pgagr52/playlist_dvr.m3u8",
        "referer": "https://snrt.player.easybroadcast.io/"
    }
}


class SNRTProxyHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """Override to custom log format"""
        print(f"[{self.log_date_time_string()}] {format % args}")
    
    def do_GET(self):
        """Handle GET requests"""
        path = self.path.split('?')[0]
        
        # Root - show available channels
        if path == "/" or path == "/playlist.m3u":
            self.serve_master_playlist()
            return
        
        # Channel request
        channel_id = path.strip('/').split('.')[0]
        
        if channel_id in CHANNELS:
            self.proxy_channel(channel_id)
        else:
            self.send_error(404, f"Channel not found: {channel_id}")
    
    def serve_master_playlist(self):
        """Generate M3U8 playlist with all available channels"""
        local_ip = self.server.server_address[0]
        if local_ip == "0.0.0.0":
            local_ip = "192.168.8.131"  # Fallback to detected IP
        
        m3u_content = "#EXTM3U\n"
        
        for channel_id, config in CHANNELS.items():
            m3u_content += f'#EXTINF:-1 tvg-logo="" group-title="SNRT Morocco",{config["name"]}\n'
            m3u_content += f'http://{local_ip}:{PORT}/{channel_id}.m3u8\n'
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(m3u_content.encode('utf-8'))
    
    def proxy_channel(self, channel_id):
        """Proxy a specific channel's stream"""
        config = CHANNELS[channel_id]
        
        headers = {
            'Referer': config['referer'],
            'Origin': 'https://snrtlive.ma',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        try:
            # Fetch the M3U8 playlist
            response = requests.get(config['url'], headers=headers, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # Rewrite URLs in playlist to proxy through us
                content = self.rewrite_playlist(content, config['url'])
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            else:
                self.send_error(response.status_code, f"Upstream error: {response.reason}")
        
        except Exception as e:
            print(f"Error proxying {channel_id}: {e}")
            self.send_error(500, str(e))
    
    def rewrite_playlist(self, content, base_url):
        """Rewrite relative URLs in M3U8 to absolute with auth headers"""
        lines = content.split('\n')
        rewritten = []
        
        for line in lines:
            if line and not line.startswith('#'):
                # This is a URL line
                if line.startswith('http'):
                    # Already absolute - leave as-is (will be fetched by player with our headers)
                    rewritten.append(line)
                else:
                    # Relative URL - make absolute
                    base = '/'.join(base_url.split('/')[:-1])
                    absolute = f"{base}/{line}"
                    rewritten.append(absolute)
            else:
                rewritten.append(line)
        
        return '\n'.join(rewritten)


def run_server():
    """Start the proxy server"""
    server = HTTPServer((HOST, PORT), SNRTProxyHandler)
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          SNRT HLS Proxy Server - Running                    ║
╠══════════════════════════════════════════════════════════════╣
║  Local IP:  192.168.8.131                                   ║
║  Port:      {PORT}                                           ║
╠══════════════════════════════════════════════════════════════╣
║  Master Playlist (Add to TiviMate):                         ║
║  http://192.168.8.131:{PORT}/playlist.m3u                    ║
╠══════════════════════════════════════════════════════════════╣
║  Available Channels:                                         ║
║  • Al Aoula          http://192.168.8.131:{PORT}/al-aoula.m3u8
║  • Arriadia          http://192.168.8.131:{PORT}/arriadia.m3u8
║  • Assadissa         http://192.168.8.131:{PORT}/assadissa.m3u8
║  • Al Maghribia      http://192.168.8.131:{PORT}/al-maghribia.m3u8
║  • Tamazight         http://192.168.8.131:{PORT}/tamazight.m3u8
║  • Laayoune          http://192.168.8.131:{PORT}/laayoune.m3u8
╚══════════════════════════════════════════════════════════════╝

Press Ctrl+C to stop
""")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down proxy server...")
        server.shutdown()


if __name__ == "__main__":
    run_server()
