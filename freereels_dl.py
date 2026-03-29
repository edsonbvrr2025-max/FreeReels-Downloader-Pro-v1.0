#!/usr/bin/env python3
"""
FreeReels Downloader Pro v2.0 - RESOLVE REDIRECTS
===========================
Analisa redirects → extrai player real → baixa sem watermark.
Compatível MyDramaWave + todos players.
"""

import re
import requests
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import subprocess
import time

console = Console()

class FreeReelsUltimateDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Referer': 'https://apiv2.free-reels.com/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site'
        })
    
    def follow_all_redirects(self, url: str) -> str:
        """Segue TODOS redirects até player final"""
        console.print(f"🔗 Seguindo redirects de: {url}")
        
        try:
            resp = self.session.get(url, allow_redirects=True, timeout=15)
            final_url = resp.url
            console.print(f"✅ Player final: {final_url}", style="green")
            return final_url
        except Exception as e:
            console.print(f"❌ Erro redirect: {e}", style="red")
            return url
    
    def extract_video_from_html(self, url: str):
        """Extrai URLs de vídeo direto do HTML/player"""
        console.print("🔍 Analisando HTML do player...")
        
        resp = self.session.get(url, timeout=15)
        html = resp.text
        
        # Patterns profissionais para vídeos
        video_patterns = [
            r'"(https?://[^"]+\.mp4[^"]*)"',
            r"'(https?://[^']+\.mp4[^']*)'",
            r'src["\']?\s*:\s*["\']([^"\']+\.mp4)',
            r'file["\']?\s*:\s*["\']([^"\']+\.mp4)',
            r'"url"["\']?\s*:\s*["\']([^"\']+\.mp4)',
            # HLS/M3U8
            r'(\.m3u8[^"\',\s]+)'
        ]
        
        for pattern in video_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for video_url in matches:
                if 'watermark' not in video_url.lower():
                    console.print(f"✅ Vídeo encontrado: {video_url[:80]}...", style="green")
                    return video_url
        
        return None
    
    def yt_dlp_universal(self, url: str, video_id: str):
        """yt-dlp com todas opções PRO"""
        Path("downloads").mkdir(exist_ok=True)
        
        cmd = [
            'yt-dlp',
            '--output', f'downloads/freereels_%(title)s_%(id)s.%(ext)s',
            '--format', 'best[height<=1080][ext=mp4]/best[ext=mp4]/best',
            '-f', 'bestvideo[height<=1080]+bestaudio/best',
            '--no-playlist',
            '--embed-subs',
            '--add-metadata',
            '--write-thumbnail',
            url
        ]
        
        console.print("🎥 yt-dlp Universal Mode", style="cyan")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("🎉 DOWNLOAD CONCLUÍDO!", style="bold green")
        else:
            console.print("❌ Erro yt-dlp:", result.stderr, style="red")
    
    def process(self, original_url: str):
        console.print("🚀 FreeReels Ultimate v2.0", style="bold magenta")
        console.print("=" * 60)
        
        # 1. Resolve TODOS redirects
        final_url = self.follow_all_redirects(original_url)
        
        # 2. Tenta extrair direto do HTML
        video_url = self.extract_video_from_html(final_url)
        
        if video_url:
            # Download direto
            filename = f"downloads/direct_{int(time.time())}.mp4"
            self.download_raw(video_url, filename)
            return
        
        # 3. yt-dlp universal no player final
        video_id = final_url.split('/')[-1].split('?')[0][:12]
        self.yt_dlp_universal(final_url, video_id)
    
    def download_raw(self, url: str, filename: str):
        """Download direto sem watermark"""
        resp = self.session.get(url, stream=True)
        total = int(resp.headers.get('content-length', 0))
        
        with open(filename, 'wb') as f, Progress(
            SpinnerColumn(), TextColumn("[green]📥 Baixando vídeo raw..."), console=console
        ) as progress:
            task = progress.add_task("Download", total=total)
            for chunk in resp.iter_content(8192):
                f.write(chunk)
                progress.update(task, advance=len(chunk))
        
        console.print(f"✅ Salvo: {filename}", style="bold green")

def main():
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else input("🔗 Cole o link FreeReels: ")
    
    downloader = FreeReelsUltimateDownloader()
    downloader.process(url)

if __name__ == "__main__":
    main()
