import streamlit as st
import yt_dlp
import os
import tempfile
import re
import subprocess
import sys

# Configuração da página
st.set_page_config(page_title="Downloader Universal", page_icon="", layout="centered")

# Função para validar links
def validar_link_instagram(url):
    padrao = r'https?://(www\.)?instagram\.com/(p|reel|reels|tv)/[A-Za-z0-9_-]+'
    return re.match(padrao, url) is not None

def validar_link_youtube(url):
    return "youtube.com" in url or "youtu.be" in url

def validar_link_spotify(url):
    return "open.spotify.com" in url

# Função para baixar Instagram
def baixar_instagram(url):
    ydl_opts = {
        'outtmpl': '%(id)s.%(ext)s',
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

# Função para baixar YouTube
def baixar_youtube(url, pasta_temp):
    ydl_opts = {
        'outtmpl': os.path.join(pasta_temp, '%(title)s.%(ext)s'),
        'format': 'best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'video')
    except Exception as e:
        return None, str(e)

# Função para baixar Spotify
def baixar_spotify(url, pasta_temp):
    try:
        # Executa o spotdl
        process = subprocess.Popen(
            ['spotdl', url, '--output', pasta_temp, '--format', 'mp3'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=pasta_temp
        )
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            # Encontra o arquivo baixado
            arquivos = [f for f in os.listdir(pasta_temp) if f.endswith('.mp3')]
            if arquivos:
                arquivo_path = os.path.join(pasta_temp, arquivos[0])
                return arquivo_path, arquivos[0]
        
        return None, stderr.decode('utf-8') if stderr else "Erro desconhecido"
    except Exception as e:
        return None, str(e)

# --- INTERFACE DO USUÁRIO ---
st.title("🎵 Downloader Universal")
st.markdown("Baixe vídeos e músicas de **Instagram**, **YouTube** e **Spotify**")

# Menu de seleção
plataforma = st.selectbox(
    "📱 Escolha a plataforma:",
    ["🎬 Instagram", "📺 YouTube", "🎵 Spotify"]
)

# Campo de URL
url = st.text_input(" Cole o link aqui:", placeholder="https://...")

# Botão de Download
if st.button("⬇️ BAIXAR", type="primary", use_container_width=True):
    if not url:
        st.warning("️ Por favor, cole um link!")
    else:
        with st.spinner("🔄 Processando download..."):
            pasta_temp = tempfile.mkdtemp()
            arquivo = None
            titulo = ""
            
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
                arquivo, info = baixar_youtube(url, pasta_temp)
                if arquivo:
                    titulo = info
                    
            elif "Spotify" in plataforma:
                if not validar_link_spotify(url):
                    st.error("❌ Link inválido do Spotify!")
                    st.stop()
                arquivo, info = baixar_spotify(url, pasta_temp)
                if arquivo:
                    titulo = info
            
            # Resultado
            if arquivo and os.path.exists(arquivo):
                st.success("✅ Download concluído!")
                st.info(f"**Arquivo:** {titulo}")
                
                with open(arquivo, "rb") as f:
                    st.download_button(
                        label="💾 Salvar arquivo",
                        data=f,
                        file_name=os.path.basename(arquivo),
                        mime="audio/mp3" if "Spotify" in plataforma else "video/mp4",
                        use_container_width=True
                    )
            else:
                st.error(f"❌ Erro no download: {info if 'info' in locals() else 'Erro desconhecido'}")

# Rodapé
st.markdown("---")
st.caption("⚠️ Use apenas para conteúdos que você tem permissão. Respeite os direitos autorais.")
