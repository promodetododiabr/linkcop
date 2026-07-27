import streamlit as st
import yt_dlp
import os
import tempfile
import re
import time
import requests

# Configuração da página
st.set_page_config(page_title="Downloader Universal", page_icon="🎵", layout="centered")

# ============ VALIDAÇÃO ============
def validar_instagram(url):
    return re.match(r'https?://(www\.)?instagram\.com/(p|reel|reels|tv)/[A-Za-z0-9_-]+', url) is not None

def validar_youtube(url):
    return "youtube.com" in url or "youtu.be" in url

def validar_spotify(url):
    return "open.spotify.com" in url

# ============ INSTAGRAM ============
def baixar_instagram(url):
    pasta_temp = tempfile.mkdtemp()
    ydl_opts = {
        'outtmpl': os.path.join(pasta_temp, '%(id)s.%(ext)s'),
        'format': 'best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'username': st.secrets.get("INSTAGRAM_USER", ""),
        'password': st.secrets.get("INSTAGRAM_PASS", ""),
        'concurrent_fragment_downloads': 4,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'video')
    except Exception as e:
        return None, str(e)

# ============ YOUTUBE ============
def baixar_youtube(url, qualidade="720", apenas_audio=False):
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
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'web_creator', 'ios', 'android'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'nocheckcertificate': True,
        'retries': 3,
        'fragment_retries': 3,
        'http_chunk_size': '10485760',
        'buffersize': '2048K',
        'concurrent_fragment_downloads': 4,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'vídeo')
    except Exception as e:
        return None, str(e)

# ============ SPOTIFY (USANDO YT-DLP) ============
def baixar_spotify(url, apenas_audio=True):
    """
    O yt-dlp suporta Spotify nativamente!
    Ele extrai as informações do Spotify e busca o áudio correspondente no YouTube.
    """
    pasta_temp = tempfile.mkdtemp()
    
    ydl_opts = {
        'outtmpl': os.path.join(pasta_temp, '%(artist)s - %(track)s.%(ext)s'),
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'web_creator', 'ios', 'android'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'nocheckcertificate': True,
        'retries': 3,
        'fragment_retries': 3,
        'concurrent_fragment_downloads': 4,
        'buffersize': '2048K',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Se for playlist, retorna o primeiro arquivo
            if 'entries' in info:
                arquivos = [f for f in os.listdir(pasta_temp) if f.endswith(('.mp3', '.m4a', '.opus', '.webm'))]
                if arquivos:
                    return os.path.join(pasta_temp, arquivos[0]), f"Playlist: {info.get('title', 'Spotify')}"
                return None, "Nenhum arquivo baixado da playlist"
            
            return filename, info.get('title', 'música')
    except Exception as e:
        return None, str(e)

# ============ INTERFACE ============
st.title("🎵 Downloader Universal")
st.markdown("Baixe vídeos e músicas de **Instagram**, **YouTube** e **Spotify** ⚡")

plataforma = st.selectbox(
    "📱 Escolha a plataforma:",
    ["🎬 Instagram", "📺 YouTube", "🎵 Spotify"]
)

url = st.text_input("🔗 Cole o link aqui:", placeholder="https://...")

if "YouTube" in plataforma:
    qualidade = st.selectbox(
        "📺 Qualidade do vídeo:",
        ["1080p", "720p", "480p", "360p", "Apenas áudio (MP3)"]
    )
    apenas_audio = qualidade == "Apenas áudio (MP3)"
    qualidade_num = qualidade.replace("p", "") if not apenas_audio else "720"
else:
    qualidade = "Melhor qualidade"
    apenas_audio = True if "Spotify" in plataforma else False
    qualidade_num = "720"

if st.button("⬇️ BAIXAR", type="primary", use_container_width=True):
    if not url:
        st.warning("⚠️ Por favor, cole um link!")
    else:
        inicio = time.time()
        
        with st.spinner("🔄 Processando..."):
            arquivo = None
            titulo = ""
            info = ""
            
            if "Instagram" in plataforma:
                if not validar_instagram(url):
                    st.error("❌ Link inválido do Instagram!")
                    st.stop()
                arquivo, info = baixar_instagram(url)
                if arquivo:
                    titulo = info
                    
            elif "YouTube" in plataforma:
                if not validar_youtube(url):
                    st.error("❌ Link inválido do YouTube!")
                    st.stop()
                arquivo, info = baixar_youtube(url, qualidade_num, apenas_audio)
                if arquivo:
                    titulo = info
                    
            elif "Spotify" in plataforma:
                if not validar_spotify(url):
                    st.error("❌ Link inválido do Spotify!")
                    st.stop()
                st.info(" Buscando áudio correspondente no YouTube...")
                arquivo, info = baixar_spotify(url, apenas_audio)
                if arquivo:
                    titulo = info
            
            tempo_total = round(time.time() - inicio, 1)
            
            if arquivo and os.path.exists(arquivo):
                tamanho_mb = round(os.path.getsize(arquivo) / (1024 * 1024), 2)
                st.success(f"✅ Download concluído em **{tempo_total} segundos**! ({tamanho_mb} MB)")
                st.info(f"**Arquivo:** {titulo}")
                
                if "Spotify" in plataforma or apenas_audio:
                    tipo_mime = "audio/mpeg"
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
                if "403" in str(info):
                    st.error("🚫 O YouTube bloqueou. Tente novamente em alguns minutos.")

st.markdown("---")
st.caption("⚠️ Use apenas para conteúdos que você tem permissão. Respeite os direitos autorais.")
