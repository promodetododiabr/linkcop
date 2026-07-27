import streamlit as st
import yt_dlp
import os
import tempfile
import re
import subprocess
import sys

# Configuração da página
st.set_page_config(page_title="Downloader Universal", page_icon="🎵", layout="centered")

# Headers para evitar bloqueio do YouTube
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

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

# Função para baixar YouTube (CORRIGIDA)
def baixar_youtube(url, pasta_temp):
    ydl_opts = {
        'outtmpl': os.path.join(pasta_temp, '%(title)s.%(ext)s'),
        'format': 'best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        # Headers para evitar bloqueio 403
        'user_agent': USER_AGENT,
        'referer': 'https://www.youtube.com/',
        # Ignorar erros de geo-restriction
        'ignoreerrors': False,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'vídeo')
    except Exception as e:
        return None, str(e)

# Função para baixar Spotify
def baixar_spotify(url, pasta_temp):
    try:
        process = subprocess.Popen(
            ['spotdl', url, '--output', pasta_temp, '--format', 'mp3'],
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

# --- INTERFACE DO USUÁRIO ---
st.title("🎵 Downloader Universal")
st.markdown("Baixe vídeos e músicas de **Instagram**, **YouTube** e **Spotify**")

# Menu de seleção
plataforma = st.selectbox(
    "📱 Escolha a plataforma:",
    ["🎬 Instagram", "📺 YouTube", "🎵 Spotify"]
)

# Campo de URL
url = st.text_input("🔗 Cole o link aqui:", placeholder="https://...")

# Opções adicionais para YouTube
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
        with st.spinner("🔄 Processando download... Aguarde..."):
            pasta_temp = tempfile.mkdtemp()
            arquivo = None
            titulo = ""
            
            if "Instagram" in plataforma:
                if not validar_link_instagram(url):
                    st.error("❌ Link inválido do Instagram!")
                    st.stop()
                st.info("🔄 Conectando ao Instagram...")
                arquivo, info = baixar_instagram(url)
                if arquivo:
                    titulo = info
                    
            elif "YouTube" in plataforma:
                if not validar_link_youtube(url):
                    st.error("❌ Link inválido do YouTube!")
                    st.stop()
                
                # Configurar qualidade
                if qualidade == "Apenas áudio (MP3)":
                    ydl_opts_teste = {'format': 'bestaudio/best'}
                elif qualidade == "720p":
                    ydl_opts_teste = {'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]'}
                elif qualidade == "480p":
                    ydl_opts_teste = {'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]'}
                else:
                    ydl_opts_teste = {'format': 'best'}
                
                ydl_opts = {
                    'outtmpl': os.path.join(pasta_temp, '%(title)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'user_agent': USER_AGENT,
                    'referer': 'https://www.youtube.com/',
                    **ydl_opts_teste
                }
                
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        filename = ydl.prepare_filename(info)
                        arquivo = filename
                        titulo = info.get('title', 'vídeo')
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
                    st.info(" **Dica:** O vídeo pode ser privado, ter restrição de idade ou de região.")
                    st.stop()
                    
            elif "Spotify" in plataforma:
                if not validar_link_spotify(url):
                    st.error("❌ Link inválido do Spotify!")
                    st.stop()
                st.info("🎵 Processando com SpotDL...")
                arquivo, info = baixar_spotify(url, pasta_temp)
                if arquivo:
                    titulo = info
            
            # Resultado
            if arquivo and os.path.exists(arquivo):
                st.success("✅ Download concluído!")
                st.info(f"**Arquivo:** {titulo}")
                
                # Determinar tipo de arquivo
                tipo_mime = "audio/mp3" if "Spotify" in plataforma or qualidade == "Apenas áudio (MP3)" else "video/mp4"
                
                with open(arquivo, "rb") as f:
                    st.download_button(
                        label=" Salvar arquivo",
                        data=f,
                        file_name=os.path.basename(arquivo),
                        mime=tipo_mime,
                        use_container_width=True
                    )
            elif arquivo is None:
                st.error(f"❌ Erro no download: {info}")
                if "403" in str(info):
                    st.error("🚫 O YouTube bloqueou o download. Tente novamente em alguns minutos.")

# Rodapé
st.markdown("---")
st.caption("⚠️ Use apenas para conteúdos que você tem permissão. Respeite os direitos autorais.")
