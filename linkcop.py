import streamlit as st
import yt_dlp
import os
import tempfile
import re
import time
import requests
import zipfile
import signal
from concurrent.futures import ThreadPoolExecutor, TimeoutError

st.set_page_config(page_title="Downloader Universal", page_icon="🎵", layout="centered")

# ============ VALIDAÇÃO ============
def validar_instagram(url):
    return re.match(r'https?://(www\.)?instagram\.com/(p|reel|reels|tv)/[A-Za-z0-9_-]+', url) is not None

def validar_youtube(url):
    return "youtube.com" in url or "youtu.be" in url

def eh_playlist(url):
    return "list=" in url or "/playlist" in url

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
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'video')
    except Exception as e:
        return None, str(e)

# ============ YOUTUBE VIA API (RÁPIDO, SEM BLOQUEIO) ============
def baixar_youtube_api(url, qualidade="720", apenas_audio=False):
    """API pública que não sofre bloqueio do YouTube"""
    try:
        # Usando API do cobalt (funciona bem)
        api_url = "https://api.cobalt.tools/api/json"
        
        payload = {
            "url": url,
            "vCodec": "h264",
            "vQuality": qualidade if not apenas_audio else "720",
            "aFormat": "mp3",
            "isAudioOnly": apenas_audio,
            "filenamePattern": "basic"
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") in ["stream", "redirect", "tunnel"]:
                file_url = data.get("url")
                
                if file_url:
                    pasta_temp = tempfile.mkdtemp()
                    ext = "mp3" if apenas_audio else "mp4"
                    arquivo_path = os.path.join(pasta_temp, f"video.{ext}")
                    
                    # Baixa o arquivo
                    file_response = requests.get(file_url, timeout=120)
                    with open(arquivo_path, 'wb') as f:
                        f.write(file_response.content)
                    
                    return arquivo_path, "download_sucesso"
        
        return None, "API não retornou dados válidos"
        
    except Exception as e:
        return None, f"Erro API: {str(e)}"

# ============ YOUTUBE VIA YT-DLP (COM TIMEOUT) ============
def baixar_youtube_ytdlp(url, qualidade="720", apenas_audio=False, timeout=60):
    """yt-dlp com timeout para não travar"""
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
        'retries': 2,
        'fragment_retries': 2,
    }
    
    def download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'vídeo')
    
    try:
        with ThreadPoolExecutor() as executor:
            future = executor.submit(download)
            resultado = future.result(timeout=timeout)
            return resultado[0], resultado[1]
    except TimeoutError:
        return None, "Timeout: download demorou muito"
    except Exception as e:
        return None, str(e)

# ============ CRIAR ZIP ============
def criar_zip(pasta_origem, nome_zip):
    zip_path = os.path.join(tempfile.mkdtemp(), nome_zip)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(pasta_origem):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, pasta_origem)
                zipf.write(file_path, arcname)
    return zip_path

# ============ INTERFACE ============
st.title("🎵 Downloader Universal")
st.markdown("Baixe vídeos e músicas de **Instagram** e **YouTube** ⚡")

plataforma = st.selectbox(
    "📱 Escolha a plataforma:",
    ["🎬 Instagram", " YouTube"]
)

url = st.text_input("🔗 Cole o link aqui:", placeholder="https://...")

if "YouTube" in plataforma:
    qualidade = st.selectbox(
        " Qualidade:",
        ["1080p", "720p", "480p", "360p", "Apenas MP3 (Áudio)"]
    )
    apenas_audio = qualidade == "Apenas MP3 (Áudio)"
    qualidade_num = qualidade.replace("p", "").replace(" (Áudio)", "") if not apenas_audio else "720"
else:
    qualidade = "Melhor"
    apenas_audio = False
    qualidade_num = "720"

if st.button("️ BAIXAR", type="primary", use_container_width=True):
    if not url:
        st.warning("⚠️ Cole um link!")
    else:
        inicio = time.time()
        
        if "Instagram" in plataforma:
            if not validar_instagram(url):
                st.error("❌ Link inválido!")
                st.stop()
            
            with st.spinner("🔄 Baixando do Instagram..."):
                arquivo, info = baixar_instagram(url)
            
            if arquivo and os.path.exists(arquivo):
                tempo_total = round(time.time() - inicio, 1)
                tamanho_mb = round(os.path.getsize(arquivo) / (1024 * 1024), 2)
                st.success(f"✅ Concluído em {tempo_total}s! ({tamanho_mb} MB)")
                
                with open(arquivo, "rb") as f:
                    st.download_button(
                        label="💾 Salvar vídeo",
                        data=f,
                        file_name=f"{info}.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )
            else:
                st.error(f"❌ Erro: {info}")
                
        elif "YouTube" in plataforma:
            if not validar_youtube(url):
                st.error("❌ Link inválido!")
                st.stop()
            
            # Tenta API primeiro (mais rápido)
            with st.spinner(" Tentando método rápido..."):
                arquivo, info = baixar_youtube_api(url, qualidade_num, apenas_audio)
            
            # Se API falhar, tenta yt-dlp com timeout
            if not arquivo:
                with st.spinner(" Método rápido falhou. Tentando alternativo (pode demorar)..."):
                    arquivo, info = baixar_youtube_ytdlp(url, qualidade_num, apenas_audio, timeout=45)
            
            tempo_total = round(time.time() - inicio, 1)
            
            if arquivo and os.path.exists(arquivo):
                tamanho_mb = round(os.path.getsize(arquivo) / (1024 * 1024), 2)
                st.success(f"✅ Concluído em {tempo_total}s! ({tamanho_mb} MB)")
                
                ext = ".mp3" if apenas_audio else ".mp4"
                mime = "audio/mpeg" if ext == ".mp3" else "video/mp4"
                
                with open(arquivo, "rb") as f:
                    st.download_button(
                        label="💾 Salvar arquivo",
                        data=f,
                        file_name=f"download{ext}",
                        mime=mime,
                        use_container_width=True
                    )
            else:
                st.error(f"❌ Erro: {info}")
                st.info(" **Soluções:**\n- Tente outro link\n- Aguarde alguns minutos e tente novamente\n- O vídeo pode ser privado ou ter restrição")

st.markdown("---")
st.caption("⚠️ Use apenas para conteúdos permitidos. Respeite direitos autorais.")
