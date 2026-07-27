import streamlit as st
import yt_dlp
import os
import tempfile
import re

# Configuração da página
st.set_page_config(page_title="Baixador Instagram", page_icon="📹", layout="centered")

# Função para validar o link
def validar_link(url):
    padrao = r'https?://(www\.)?instagram\.com/(p|reel|reels|tv)/[A-Za-z0-9_-]+'
    return re.match(padrao, url) is not None

# Função para baixar o vídeo
def baixar_video(url, pasta_temp, navegador):
    ydl_opts = {
        'outtmpl': os.path.join(pasta_temp, '%(id)s.%(ext)s'),
        'format': 'best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        # O PULO DO GATO: Usa os cookies do seu navegador para não precisar de senha
        'cookiesfrombrowser': (navegador,), 
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'video')
    except Exception as e:
        return None, str(e)

# --- Interface do Usuário ---
st.title("📹 Baixador de Vídeos do Instagram")
st.markdown("Cole o link e baixe direto. **Sem pedir senha.**")

# Campo para o link
url = st.text_input("🔗 Link do Instagram:", placeholder="https://www.instagram.com/reel/...")

# Escolha do navegador (apenas para pegar os cookies de login)
navegador = st.selectbox(" Qual navegador você usa para acessar o Instagram?", ["chrome", "edge", "firefox", "opera"])

# Botão de Download
if st.button("️ Baixar Vídeo", type="primary", use_container_width=True):
    if not url:
        st.warning("⚠️ Por favor, cole um link primeiro.")
    elif not validar_link(url):
        st.error("❌ Esse link não parece ser do Instagram.")
    else:
        with st.spinner("🔄 Processando o vídeo..."):
            pasta_temp = tempfile.mkdtemp()
            arquivo, info = baixar_video(url, pasta_temp, navegador)
            
            if arquivo and os.path.exists(arquivo):
                st.success("✅ Vídeo baixado com sucesso!")
                
                # Botão para salvar o arquivo no seu PC
                with open(arquivo, "rb") as f:
                    st.download_button(
                        label="💾 Clique aqui para salvar o vídeo",
                        data=f,
                        file_name=os.path.basename(arquivo),
                        mime="video/mp4",
                        use_container_width=True
                    )
            else:
                st.error(f"❌ Não foi possível baixar.\n\n**Motivo:** {info}")
                st.info("💡 **Dica:** Se der erro, **feche o seu navegador** e tente de novo (o app precisa acessar os cookies).")

# Rodapé
st.markdown("---")
st.caption("⚠️ Use apenas para baixar conteúdos que você tem permissão. Respeite os direitos autorais.")