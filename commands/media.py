import os
import re
import subprocess
import webbrowser
from pathlib import Path
import pywhatkit as kit
import yt_dlp
from commands.constants import Colors
from commands.voice import falar

# ========== YouTube e Pesquisa ==========

def tocar_musica_pywhatkit(match, username=None, modo='texto'):
    """Toca música no YouTube usando pywhatkit"""
    try:
        musica = None
        if hasattr(match, 'group'):
            try:
                musica = match.group(1).strip()
            except IndexError:
                pass
        elif isinstance(match, str) and match.strip():
            musica = match.strip()
        
        if not musica:
            return "Por favor, repita o comando informando o nome da música, senhor."
        
        msg = f"Abrindo '{musica}' no YouTube..."
        if modo == 'voz': falar(msg)
        print(msg)
        kit.playonyt(musica)
        return f"Reproduzindo '{musica}' no YouTube, senhor."
    except Exception as e:
        return f"Erro ao abrir YouTube: {e}"

def pesquisar_google_pywhatkit(match, username=None, modo='texto'):
    """Pesquisa no Google usando pywhatkit"""
    try:
        termo = None
        if hasattr(match, 'group'):
            if match.lastindex >= 2: termo = match.group(2).strip()
            elif match.lastindex >= 1: termo = match.group(1).strip()
        elif isinstance(match, str) and match.strip():
            termo = match.strip()
        
        if not termo:
            return "Por favor especifique o que deseja pesquisar no Google, senhor."
        
        msg = f"Pesquisando '{termo}' no Google..."
        if modo == 'voz': falar(msg)
        print(msg)
        kit.search(termo)
        return f"Mostrando resultados para '{termo}', senhor."
    except Exception as e:
        return f"Erro ao pesquisar: {e}"

# ========== Download de Vídeo/Áudio ==========

def converter_audio_para_aac(caminho_video: Path):
    """Fallback para converter áudio se necessário"""
    pass # Implementação dependente de ffmpeg no sistema

def limpar_nome_arquivo(nome):
    return re.sub(r'[\\/*?:"<>|]', "", nome)

def baixar_video_youtube(url, username, modo='texto'):
    try:
        output_path = Path.home() / "Downloads" / "JARVIS_Videos"
        output_path.mkdir(parents=True, exist_ok=True)
        
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': str(output_path / '%(title)s.%(ext)s'),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return f"🎥 Vídeo baixado com sucesso em: {output_path}"
    except Exception as e:
        return f"Erro ao baixar vídeo: {e}"

def baixar_audio_youtube(url, username, modo='texto'):
    try:
        output_path = Path.home() / "Downloads" / "JARVIS_Audio"
        output_path.mkdir(parents=True, exist_ok=True)
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(output_path / '%(title)s.%(ext)s'),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return f"🎵 Áudio baixado com sucesso em: {output_path}"
    except Exception as e:
        return f"Erro ao baixar áudio: {e}"

def abrir_site(match, username=None):
    """Abre um site no navegador padrão"""
    site = None
    if hasattr(match, 'group'):
        try:
            site = match.group(1).strip().lower()
        except IndexError:
            # Fallback para o texto completo se o grupo 1 não existir
            site = match.group(0).split()[-1].lower()
    else:
        site = str(match).lower()
    
    if not site:
        return "Não consegui identificar qual site abrir, senhor."
    
    sites_comuns = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "facebook": "https://www.facebook.com",
        "instagram": "https://www.instagram.com",
        "whatsapp": "https://web.whatsapp.com",
        "github": "https://www.github.com",
        "gmail": "https://mail.google.com",
        "netflix": "https://www.netflix.com",
        "twitter": "https://www.twitter.com",
        "linkedin": "https://www.linkedin.com"
    }
    
    url = sites_comuns.get(site)
    if not url:
        if "." in site: url = "https://" + site if not site.startswith("http") else site
        else: url = f"https://www.google.com/search?q={site}"
        
    try:
        webbrowser.open(url)
        return f"Abrindo {site} no seu navegador, senhor."
    except Exception as e:
        return f"Erro ao abrir site: {e}"
