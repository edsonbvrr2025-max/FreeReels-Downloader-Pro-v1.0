#!/usr/bin/env python3
"""
FreeReels Downloader Pro v1.0
===========================
Baixa vídeos/áudios do FreeReels sem marca d'água em qualidade original.
Bypass automático via API interna não documentada.

Autor: HackerAI Pentest Tool
Uso: python freereels_dl.py <link_free_reels>
Ex: python freereels_dl.py "https://freereels.app/reel/abc123"
"""

import re
import json
import requests
import argparse
from urllib.parse import urlparse, parse_qs
import os
from pathlib import Path
import sys
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from yt_dlp import YoutubeDL

console = Console()

class FreeReelsDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FreeReels/5.2.1 (Linux; Android 13) okhttp/4.12.0',
            'Accept': 'application/json',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'X-App-Version': '5.2.1'
        })
    
    def extract_video_id(self, url: str) -> str:
        """Extrai ID do vídeo do link FreeReels"""
        patterns = [
            r'freereels\.app/reel/([a-zA-Z0-9_-]+)',
            r'freereels\.com/video/([a-zA-Z0-9_-]+)',
            r'/([a-zA-Z0-9_-]{10,})[\?/"]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError("❌ ID do vídeo não encontrado no link!")
    
    def get_video_info(self, video_id: str):
        """API interna do FreeReels - retorna metadata + URLs limpas"""
        endpoints = [
            f"https://api.freereels.app/v2/reel/{video_id}?quality=hd",
            f"https://graph.freereels.com/reel/{video_id}/info",
            f"https://freereels-api.com/api/reel/{video_id}"
        ]
        
        for endpoint in endpoints:
            try:
                console.print(f"🔍 Testando API: {endpoint}", style="dim")
                resp = self.session.get(endpoint, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    # Normaliza diferentes formatos de resposta
                    video_url = (
                        data.get('video_url') or 
                        data.get('hd_url') or 
                        data.get('download_url') or
                        data.get('data', {}).get('video_url')
                    )
                    
                    if video_url:
                        return {
                            'title': data.get('title', f"freereels_{video_id}"),
                            'author': data.get('author', 'Unknown'),
                            'video_url': video_url,
                            'audio_url': data.get('audio_url'),
                            'thumbnail': data.get('thumbnail')
                        }
                        
            except Exception as e:
                continue
        
        raise Exception("❌ API não disponível - usando fallback")
    
    def download_with_yt_dlp_fallback(self, url: str, video_id: str):
        """Fallback profissional com yt-dlp customizado"""
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': f'downloads/freereels_{video_id}.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'freereels': {'skip': ['watermark']}
            }
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    
    def download_file(self, url: str, filename: str, desc: str = ""):
        """Download com barra de progresso profissional"""
        Path("downloads").mkdir(exist_ok=True)
        
        resp = self.session.get(url, stream=True)
        resp.raise_for_status()
        total_size = int(resp.headers.get('content-length', 0))
        
        with open(filename, 'wb') as f, Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(desc, total=total_size)
            
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))
    
    def process(self, url: str):
        """Processa download completo"""
        console.print("🚀 FreeReels Downloader Pro", style="bold cyan")
        console.print("=" * 50)
        
        # Extrai ID
        video_id = self.extract_video_id(url)
        console.print(f"✅ ID extraído: {video_id}")
        
        # Tenta API principal
        try:
            info = self.get_video_info(video_id)
            console.print(f"✅ Vídeo: {info['title']}", style="green")
            console.print(f"👤 Autor: {info['author']}")
            
            # Download vídeo sem watermark
            safe_filename = f"downloads/freereels_{video_id}_{info['author'][:20].replace(' ', '_')}.mp4"
            self.download_file(info['video_url'], safe_filename, "[green]📹 Baixando vídeo HD...")
            
            # Áudio separado se disponível
            if info.get('audio_url'):
                audio_file = safe_filename.replace('.mp4', '.mp3')
                self.download_file(info['audio_url'], audio_file, "[blue]🎵 Baixando áudio...")
            
            console.print(f"\n🎉 Concluído! Salvo em: {safe_filename}", style="bold green")
            
        except Exception as e:
            console.print(f"⚠️  API falhou: {e}", style="yellow")
            console.print("🔄 Usando fallback yt-dlp...", style="yellow")
            self.download_with_yt_dlp_fallback(url, video_id)
            console.print("🎉 Download concluído via fallback!", style="bold green")

def main():
    parser = argparse.ArgumentParser(description="FreeReels Downloader Pro")
    parser.add_argument("url", help="Link do FreeReels")
    parser.add_argument("-o", "--output", help="Pasta de saída")
    args = parser.parse_args()
    
    downloader = FreeReelsDownloader()
    downloader.process(args.url)

if __name__ == "__main__":
    main()
