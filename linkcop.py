import streamlit as st
import yt_dlp
import os
import tempfile
import re
import subprocess
import time
import requests
import json

# Configuração da página
st.set_page_config(page_title="Downloader Universal", page_icon="", layout="centered")

# ============ FUNÇÕES DE VALIDAÇÃO ============
def validar_link_instagram(url):
    return re.match(r'https?://(www\.)?instagram\.com/(p|reel|reels|tv)/[A-Za-z0-9_-]+', url) is not None

def validar_link_youtube(url):
    return "youtube.com" in url or "youtu.be" in url

def validar_link_spotify(url):
    return "open.spotify.com" in url

# ============ DOWNLOAD YOUTUBE - MÉTODO 1: API YTMP3 ============
def baixar_youtube_api_ytmp3(url, apenas_audio=False):
    """API alternativa 1"""
    try:
        if apenas_audio:
            api_url = f"https://yt1s.com/api/ajaxSearch/index?vid={url}&q=mp3"
        else:
            api_url = f"https://yt1s.com/api/ajaxSearch/index?vid={url}&q=mp4"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://yt1s.com/"
        }
        
        response = requests.get(api_url, headers=headers, timeout=15)
        data = response.json()
        
        if data.get("status") == "ok":
            # Pega o link de download
            if apenas_audio:
                links = data.get("links", {})
                mp3_links = links.get("mp3", {})
                if mp3_links:
                    download_key = list(mp3_links.keys())[0]
                    download_url = mp3_links[download_key].get("u")
                    titulo = data.get("title", "audio")
            else:
                links = data.get("links", {})
                mp4_links = links.get("mp4", {})
                if mp4_links:
                    download_key = list(mp4_links.keys())[0]
                    download_url = mp4_links[download_key].get("u")
                    titulo = data.get("title", "video")
            
            if download_url:
                pasta_temp = tempfile.mkdtemp()
                ext = "mp3" if apenas_audio else "mp4"
                arquivo_path = os.path.join(pasta_temp, f"video.{ext}")
                
                file_response = requests.get(download_url, timeout=60)
                with open(arquivo_path, 'wb') as f:
                    f.write(file_response.content)
                
                return arquivo_path, titulo
        
        return None, "API não retornou dados válidos"
        
    except Exception as e:
        return None, str(e)

# ============ DOWNLOAD YOUTUBE - MÉTODO 2: YT-DLP OTIMIZADO ============
def baixar_youtube_ytdlp(url, qualidade="720", apenas_audio=False):
    """Fallback usando yt-dlp com configurações anti-bloqueio"""
    try:
        pasta_temp = tempfile.mkdtemp()
        
        if apenas_audio:
            format_str = 'bestaudio/best'
            ext = 'mp3'
        elif qualidade == "1080p":
            format_str = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
            ext = 'mp4'
        elif qualidade == "720p":
            format_str = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
            ext = 'mp4'
        elif qualidade == "480p":
            format_str = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
            ext = 'mp4'
        else:
            format_str = 'best'
            ext = 'mp4'
        
        ydl_opts = {
            'outtmpl': os.path.join(pasta_temp, '%(title)s.' + ext),
            'format': format_str,
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            # Configurações anti-bloqueio
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'web_creator', 'ios', 'android'],
                    'player_skip': ['webpage', 'configs']
                }
            },
            'nocheckcertificate': True,
            'retries': 2,
            'fragment_retries': 2,
            'http_chunk_size': '10485760',
            'buffersize': '1048576',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'vídeo')
        
    except Exception as e:
        return None, str(e)

# ============ DOWNLOAD INSTAGRAM ============
def baixar_instagram(url):
    ydl_opts = {
        'outtmpl': '%(id)s.%(ext)s',
        'format': 'best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'username': st.secrets.get("INSTAGRAM_USER", ""),
        'password': st.secrets.get("INSTAGRAM_PASS", ""),
        'concurrent_fragment_downloads': 4,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'video')
    except Exception as e:
        return None, str(e)

# ============ DOWNLOAD SPOTIFY ============
def baixar_spotify(url, pasta_temp):
    try:
        process = subprocess.Popen(
            ['spotdl', url, '--output', pasta_temp, '--format', 'mp3', 
             '--bitrate', '320', '--threads', '4'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=pasta_temp
        )
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            arquivos = [f for f in os.listdir(pasta_temp) if f.endswith('.mp3')]
            if arquivos:
                arquivo_path = os.path.join(pasta_temp, arquivos[0])
                return arquivo_path, arquivos[0]
        
        return None, stderr.decode('utf-8') if stderr else "Erro desconhecido"
    except Exception as e:
        return None, str(e)

# ============ INTERFACE ============
st.title("🎵 Downloader Universal")
st.markdown("Baixe vídeos e músicas de **Instagram**, **YouTube** e **Spotify** ⚡")

# Menu de seleção
plataforma = st.selectbox(
    "📱 Escolha a plataforma:",
    ["🎬 Instagram", "📺 YouTube", "🎵 Spotify"]
)

# Campo de URL
url = st.text_input("🔗 Cole o link aqui:", placeholder="https://...")

# Opções para YouTube
if "YouTube" in plataforma:
    qualidade = st.selectbox(
        " Qualidade do vídeo:",
        ["1080p", "720p", "480p", "360p", "Apenas áudio (MP3)"]
    )
    apenas_audio = qualidade == "Apenas áudio (MP3)"
    qualidade_num = qualidade.replace("p", "") if not apenas_audio else "720"
else:
    qualidade = "Melhor qualidade"
    apenas_audio = False
    qualidade_num = "720"

# Botão de Download
if st.button("⬇️ BAIXAR", type="primary", use_container_width=True):
    if not url:
        st.warning("⚠️ Por favor, cole um link!")
    else:
        inicio = time.time()
        
        with st.spinner("🔄 Processando..."):
            pasta_temp = tempfile.mkdtemp()
            arquivo = None
            titulo = ""
            info = ""
            
            if "Instagram" in plataforma:
                if not validar_link_instagram(url):
                    st.error("❌ Link inválido do Instagram!")
                    st.stop()
                arquivo, info = baixar_instagram(url)
                if arquivo:
                    titulo = info
                    
            elif "YouTube" in plataforma:
                if not validar_link_youtube(url):
                    st.error("❌ Link inválido do YouTube!")
                    st.stop()
                
                # Tenta API primeiro (mais rápido)
                st.info("🔄 Tentando API rápida...")
                arquivo, info = baixar_youtube_api_ytmp3(url, apenas_audio)
                
                # Se API falhar, tenta yt-dlp
                if not arquivo:
                    st.info("🔄 API indisponível, tentando método alternativo...")
                    arquivo, info = baixar_youtube_ytdlp(url, qualidade_num, apenas_audio)
                
                if arquivo:
                    titulo = info
                    
            elif "Spotify" in plataforma:
                if not validar_link_spotify(url):
                    st.error("❌ Link inválido do Spotify!")
                    st.stop()
                arquivo, info = baixar_spotify(url, pasta_temp)
                if arquivo:
                    titulo = info
            
            tempo_total = round(time.time() - inicio, 1)
            
            # Resultado
            if arquivo and os.path.exists(arquivo):
                tamanho_mb = round(os.path.getsize(arquivo) / (1024 * 1024), 2)
                st.success(f"✅ Download concluído em **{tempo_total} segundos**! ({tamanho_mb} MB)")
                st.info(f"**Arquivo:** {titulo}")
                
                if "Spotify" in plataforma or apenas_audio:
                    tipo_mime = "audio/mp3"
                    extensao = ".mp3"
                else:
                    tipo_mime = "video/mp4"
                    extensao = ".mp4"
                
                with open(arquivo, "rb") as f:
                    st.download_button(
                        label="💾 Salvar arquivo",
                        data=f,
                        file_name=f"download{extensao}",
                        mime=tipo_mime,
                        use_container_width=True
                    )
            else:
                st.error(f"❌ Erro no download: {info}")
                st.info("💡 **Dica:** O vídeo pode ser privado, ter restrição de idade ou estar indisponível.")

# Rodapé
st.markdown("---")
st.caption("⚠️ Use apenas para conteúdos que você tem permissão. Respeite os direitos autorais.")
