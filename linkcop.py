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
st.set_page_config(page_title="Downloader Universal", page_icon="🎵", layout="centered")

# ============ FUNÇÕES DE VALIDAÇÃO ============
def validar_link_instagram(url):
    return re.match(r'https?://(www\.)?instagram\.com/(p|reel|reels|tv)/[A-Za-z0-9_-]+', url) is not None

def validar_link_youtube(url):
    return "youtube.com" in url or "youtu.be" in url

def validar_link_spotify(url):
    return "open.spotify.com" in url

# ============ DOWNLOAD VIA API COBALT (YouTube - sem erro de bot) ============
def baixar_youtube_api(url, qualidade="720", apenas_audio=False):
    """Usa a API pública do cobalt para baixar do YouTube sem precisar de login"""
    try:
        api_url = "https://co.wuk.sh/api/json"
        
        payload = {
            "url": url,
            "vCodec": "h264",
            "vQuality": qualidade,
            "aFormat": "mp3",
            "isAudioOnly": apenas_audio,
            "filenamePattern": "basic"
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        data = response.json()
        
        if data.get("status") == "stream" or data.get("status") == "redirect":
            # Baixa o arquivo
            file_url = data.get("url")
            if file_url:
                # Determina a extensão
                ext = "mp3" if apenas_audio else "mp4"
                pasta_temp = tempfile.mkdtemp()
                arquivo_path = os.path.join(pasta_temp, f"video.{ext}")
                
                # Download do arquivo
                file_response = requests.get(file_url, timeout=60, stream=True)
                with open(arquivo_path, 'wb') as f:
                    for chunk in file_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                return arquivo_path, "download_sucesso"
        
        return None, data.get("text", "Erro na API")
        
    except Exception as e:
        return None, str(e)

# ============ DOWNLOAD INSTAGRAM (yt-dlp com login) ============
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

# ============ DOWNLOAD SPOTIFY (spotdl) ============
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
    " Escolha a plataforma:",
    ["🎬 Instagram", "📺 YouTube", "🎵 Spotify"]
)

# Campo de URL
url = st.text_input("🔗 Cole o link aqui:", placeholder="https://...")

# Opções para YouTube
if "YouTube" in plataforma:
    qualidade = st.selectbox(
        "📺 Qualidade do vídeo:",
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
                arquivo, info = baixar_youtube_api(url, qualidade_num, apenas_audio)
                if arquivo:
                    titulo = "Vídeo do YouTube"
                    
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

# Rodapé
st.markdown("---")
st.caption("⚠️ Use apenas para conteúdos que você tem permissão. Respeite os direitos autorais.")
