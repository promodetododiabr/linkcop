import streamlit as st
import yt_dlp
import os
import tempfile
import re
import time
import requests
import json

st.set_page_config(page_title="Downloader Universal", page_icon="🎵", layout="centered")

# ============ VALIDAÇÃO ============
def validar_instagram(url):
    return re.match(r'https?://(www\.)?instagram\.com/(p|reel|reels|tv)/[A-Za-z0-9_-]+', url) is not None

def validar_youtube(url):
    return "youtube.com" in url or "youtu.be" in url

# ============ INSTAGRAM (FUNCIONA) ============
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

# ============ YOUTUBE VIA API (SEM BLOQUEIO) ============
def baixar_youtube_api(url, qualidade="720"):
    """Usa API pública que não sofre bloqueio"""
    try:
        # API alternativa 1: Y2Mate
        api_url = "https://www.y2mate.com/mates/analyze"
        payload = {
            'ajax': 1,
            'qw': url,
            'site': 'youtube.com',
            'tLang': 'en'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.y2mate.com/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        response = requests.post(api_url, data=payload, headers=headers, timeout=15)
        data = response.json()
        
        if data.get('status') == 'ok':
            titulo = data.get('title', 'video')
            
            # Seleciona qualidade
            videos = data.get('videos', {})
            mp4_videos = videos.get('mp4', {})
            
            # Ordena por qualidade
            qualidades_disponiveis = {
                '1080': [], '720': [], '480': [], '360': []
            }
            
            for q, info in mp4_videos.items():
                if isinstance(info, dict):
                    q_num = info.get('q', '')
                    if q_num in qualidades_disponiveis:
                        qualidades_disponiveis[q_num].append(info)
            
            # Pega a qualidade desejada ou a melhor disponível
            video_escolhido = None
            for q in [qualidade, '720', '480', '360', '1080']:
                if qualidades_disponiveis.get(q):
                    video_escolhido = qualidades_disponiveis[q][0]
                    break
            
            if video_escolhido:
                download_url = video_escolhido.get('url')
                
                # Baixa o arquivo
                pasta_temp = tempfile.mkdtemp()
                arquivo_path = os.path.join(pasta_temp, f"{titulo}.mp4")
                
                file_response = requests.get(download_url, timeout=120)
                with open(arquivo_path, 'wb') as f:
                    f.write(file_response.content)
                
                return arquivo_path, titulo
        
        return None, "API não retornou dados"
        
    except Exception as e:
        return None, f"Erro API Y2Mate: {str(e)}"

# ============ YOUTUBE AUDIO APENAS ============
def baixar_youtube_audio_api(url):
    """Baixa apenas áudio do YouTube via API"""
    try:
        api_url = "https://www.y2mate.com/mates/analyze"
        payload = {
            'ajax': 1,
            'qw': url,
            'site': 'youtube.com',
            'tLang': 'en'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.y2mate.com/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        response = requests.post(api_url, data=payload, headers=headers, timeout=15)
        data = response.json()
        
        if data.get('status') == 'ok':
            titulo = data.get('title', 'audio')
            audios = data.get('audios', {})
            mp3_audios = audios.get('mp3', {})
            
            if mp3_audios:
                # Pega o primeiro MP3 disponível
                audio_info = list(mp3_audios.values())[0]
                download_url = audio_info.get('url')
                
                pasta_temp = tempfile.mkdtemp()
                arquivo_path = os.path.join(pasta_temp, f"{titulo}.mp3")
                
                file_response = requests.get(download_url, timeout=120)
                with open(arquivo_path, 'wb') as f:
                    f.write(file_response.content)
                
                return arquivo_path, titulo
        
        return None, "API não retornou áudio"
        
    except Exception as e:
        return None, str(e)

# ============ INTERFACE ============
st.title(" Downloader Universal")
st.markdown("Baixe vídeos e músicas de **Instagram** e **YouTube** ⚡")

plataforma = st.selectbox(
    "📱 Escolha a plataforma:",
    ["🎬 Instagram", " YouTube"]
)

url = st.text_input("🔗 Cole o link aqui:", placeholder="https://...")

if "YouTube" in plataforma:
    qualidade = st.selectbox(
        "📺 Qualidade:",
        ["1080p", "720p", "480p", "360p", "Apenas MP3"]
    )
else:
    qualidade = "Melhor"

if st.button("⬇️ BAIXAR", type="primary", use_container_width=True):
    if not url:
        st.warning("⚠️ Cole um link!")
    else:
        inicio = time.time()
        
        with st.spinner("🔄 Processando..."):
            arquivo = None
            titulo = ""
            info = ""
            
            if "Instagram" in plataforma:
                if not validar_instagram(url):
                    st.error("❌ Link inválido!")
                    st.stop()
                arquivo, info = baixar_instagram(url)
                if arquivo:
                    titulo = info
                    
            elif "YouTube" in plataforma:
                if not validar_youtube(url):
                    st.error("❌ Link inválido!")
                    st.stop()
                
                if qualidade == "Apenas MP3":
                    st.info("🎵 Extraindo áudio...")
                    arquivo, info = baixar_youtube_audio_api(url)
                else:
                    q_num = qualidade.replace("p", "")
                    st.info(f"📹 Baixando em {qualidade}...")
                    arquivo, info = baixar_youtube_api(url, q_num)
                
                if arquivo:
                    titulo = info
            
            tempo_total = round(time.time() - inicio, 1)
            
            if arquivo and os.path.exists(arquivo):
                tamanho_mb = round(os.path.getsize(arquivo) / (1024 * 1024), 2)
