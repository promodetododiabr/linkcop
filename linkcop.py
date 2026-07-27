import streamlit as st
import yt_dlp
import os
import tempfile
import re
import subprocess
import time
import requests

# Configuração da página
st.set_page_config(page_title="Downloader Universal", page_icon="🎵", layout="centered")

# Headers para evitar bloqueio
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Função para validar links
def validar_link_instagram(url):
    return re.match(r'https?://(www\.)?instagram\.com/(p|reel|reels|tv)/[A-Za-z0-9_-]+', url) is not None

def validar_link_youtube(url):
    return "youtube.com" in url or "youtu.be" in url

def validar_link_spotify(url):
    return "open.spotify.com" in url

# ============ FUNÇÕES OTIMIZADAS ============

def baixar_instagram(url):
    ydl_opts = {
        'outtmpl': '%(id)s.%(ext)s',
        'format': 'best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': USER_AGENT,
        'username': st.secrets.get("INSTAGRAM_USER", ""),
        'password': st.secrets.get("INSTAGRAM_PASS", ""),
        # Otimizações de velocidade
        'concurrent_fragment_downloads': 4,  # Baixa 4 fragmentos em paralelo
        'buffersize': '1024K',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'video')
    except Exception as e:
        return None, str(e)

def baixar_youtube(url, pasta_temp, qualidade="Melhor qualidade"):
    # Configurar formato baseado na qualidade
    if qualidade == "Apenas áudio (MP3)":
        format_str = 'bestaudio/best'
    elif qualidade == "720p":
        format_str = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best[height<=720]'
    elif qualidade == "480p":
        format_str = 'bestvideo[height<=480]+bestaudio/best[height<=480]/best[height<=480]'
    else:
        format_str = 'best'
    
    ydl_opts = {
        'outtmpl': os.path.join(pasta_temp, '%(title)s.%(ext)s'),
        'format': format_str,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': USER_AGENT,
        'referer': 'https://www.youtube.com/',
        # 🚀 OTIMIZAÇÕES DE VELOCIDADE
        'concurrent_fragment_downloads': 4,  # Downloads paralelos
        'buffersize': '2048K',  # Buffer maior
        'http_chunk_size': '10485760',  # Chunk de 10MB
        # Burla o throttle do YouTube (muito importante!)
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'web_creator', 'ios', 'android'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'nocheckcertificate': True,
        'retries': 3,
        'fragment_retries': 3,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'vídeo')
    except Exception as e:
        return None, str(e)

def baixar_spotify(url, pasta_temp):
    try:
        process = subprocess.Popen(
            ['spotdl', url, '--output', pasta_temp, '--format', 'mp3', 
             '--bitrate', '320',  # Qualidade máxima
             '--threads', '4'],   # Threads paralelos
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

# ============ MANTER APP ACORDADO ============
def manter_app_acordado():
    """Faz um ping no próprio app para evitar que o Streamlit Cloud durma"""
    try:
        requests.get(st.runtime.get_instance()._server._base_url, timeout=5)
    except:
        pass

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
        "📺 Qualidade do vídeo:",
        ["Melhor qualidade", "720p", "480p", "Apenas áudio (MP3)"]
    )
else:
    qualidade = "Melhor qualidade"

# Botão de Download
if st.button("⬇️ BAIXAR", type="primary", use_container_width=True):
    if not url:
        st.warning("⚠️ Por favor, cole um link!")
    else:
        inicio = time.time()
        
        with st.spinner("🔄 Processando... Otimizando para máxima velocidade..."):
            pasta_temp = tempfile.mkdtemp()
            arquivo = None
            titulo = ""
            info = ""
            
            if "Instagram" in plataforma:
                if not validar_link_instagram(url):
                    st.error(" Link inválido do Instagram!")
                    st.stop()
                arquivo, info = baixar_instagram(url)
                if arquivo:
                    titulo = info
                    
            elif "YouTube" in plataforma:
                if not validar_link_youtube(url):
                    st.error("❌ Link inválido do YouTube!")
                    st.stop()
                arquivo, info = baixar_youtube(url, pasta_temp, qualidade)
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
                
                tipo_mime = "audio/mp3" if "Spotify" in plataforma or qualidade == "Apenas áudio (MP3)" else "video/mp4"
                
                with open(arquivo, "rb") as f:
                    st.download_button(
                        label=" Salvar arquivo",
                        data=f,
                        file_name=os.path.basename(arquivo),
                        mime=tipo_mime,
                        use_container_width=True
                    )
            else:
                st.error(f"❌ Erro no download: {info}")
                if "403" in str(info):
                    st.error("🚫 O YouTube bloqueou o download. Tente novamente em alguns minutos.")

# Rodapé
st.markdown("---")
st.caption("⚠️ Use apenas para conteúdos que você tem permissão. Respeite os direitos autorais.")
