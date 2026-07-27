import streamlit as st
import yt_dlp
import os
import tempfile
import re
import time

# Configuração da página
st.set_page_config(
    page_title="InstaSave Pro",
    page_icon="📸",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS personalizado - corrigido para legibilidade
st.markdown("""
<style>
    /* Fundo gradiente suave */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8eaf6 50%, #f3e5f5 100%);
        min-height: 100vh;
    }
    
    /* Título principal com gradiente Instagram */
    h1 {
        background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        font-size: 3em !important;
        font-weight: 800 !important;
        margin-bottom: 10px;
    }
    
    /* Subtítulo */
    .subtitle {
        text-align: center;
        color: #555 !important;
        font-size: 1.2em !important;
        margin-bottom: 30px;
        font-weight: 500;
    }
    
    /* Card principal branco */
    .main-card {
        background: white;
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin: 20px auto;
    }
    
    /* Botão principal estilizado */
    .stButton > button {
        background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
        color: white !important;
        border: none;
        border-radius: 50px;
        padding: 15px 40px;
        font-size: 1.2em;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 15px rgba(220, 39, 67, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(220, 39, 67, 0.5);
    }
    
    /* Campo de input */
    .stTextInput input {
        border-radius: 15px !important;
        border: 2px solid #e0e0e0 !important;
        padding: 15px !important;
        font-size: 1em !important;
        background: white !important;
        color: #333 !important;
    }
    
    .stTextInput input:focus {
        border-color: #dc2743 !important;
    }
    
    /* Alertas e mensagens */
    .stAlert {
        border-radius: 15px !important;
        padding: 15px !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #dc2743 !important;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
        border-radius: 50px;
        padding: 15px 40px;
        font-size: 1.1em;
        font-weight: bold;
        width: 100%;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
    }
    
    /* Cards de recursos */
    .feature-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: transform 0.3s;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
    }
    
    .feature-icon {
        font-size: 2.5em;
        margin-bottom: 10px;
    }
    
    .feature-title {
        color: #333 !important;
        font-weight: bold;
        font-size: 1.1em;
    }
    
    /* Rodapé */
    .footer {
        text-align: center;
        color: #666 !important;
        margin-top: 30px;
        font-size: 0.9em;
    }
    
    /* Esconder barra lateral vazia */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Função para validar link
def validar_instagram(url):
    padrao = r'https?://(www\.)?instagram\.com/(p|reel|reels|tv|stories)/[A-Za-z0-9_-]+'
    return re.match(padrao, url) is not None

# Função para baixar
def baixar_instagram(url):
    pasta_temp = tempfile.mkdtemp()
    ydl_opts = {
        'outtmpl': os.path.join(pasta_temp, '%(title)s.%(ext)s'),
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
            return filename, info.get('title', 'video'), info
    except Exception as e:
        return None, str(e), None

# Interface principal
st.markdown("<h1> InstaSave Pro</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">Baixe vídeos, reels e fotos do Instagram<br>de forma rápida e gratuita</p>', unsafe_allow_html=True)

# Card principal
st.markdown('<div class="main-card">', unsafe_allow_html=True)

# Campo de URL
url = st.text_input(
    "",
    placeholder="🔗 Cole o link do Instagram aqui...",
    label_visibility="collapsed"
)

# Botão de download
if st.button("⬇️ BAIXAR AGORA", use_container_width=True):
    if not url:
        st.error("⚠️ Por favor, cole um link do Instagram!")
    elif not validar_instagram(url):
        st.error("❌ Link inválido! Use links de posts, reels ou stories.")
    else:
        with st.spinner("⏳ Processando seu download..."):
            inicio = time.time()
            arquivo, info, dados = baixar_instagram(url)
            tempo_total = round(time.time() - inicio, 1)
            
            if arquivo and os.path.exists(arquivo):
                tamanho_mb = round(os.path.getsize(arquivo) / (1024 * 1024), 2)
                
                st.success(f"✅ Download concluído em **{tempo_total}s**! ({tamanho_mb} MB)")
                st.info(f"📄 **Arquivo:** {info}")
                
                # Determina tipo de arquivo
                if arquivo.endswith('.mp4'):
                    mime_type = "video/mp4"
                    emoji = "🎬"
                    label = "BAIXAR VÍDEO"
                elif arquivo.endswith('.jpg') or arquivo.endswith('.jpeg'):
                    mime_type = "image/jpeg"
                    emoji = "📷"
                    label = "BAIXAR FOTO"
                else:
                    mime_type = "video/mp4"
                    emoji = "📹"
                    label = "BAIXAR ARQUIVO"
                
                # Botão de download
                with open(arquivo, "rb") as f:
                    st.download_button(
                        label=f"{emoji} {label}",
                        data=f,
                        file_name=os.path.basename(arquivo),
                        mime=mime_type,
                        use_container_width=True
                    )
            else:
                st.error(f"❌ Erro no download: {info}")
                st.info("💡 **Dicas:**\n- Verifique se o link está correto\n- O post pode ser privado\n- Tente novamente em alguns minutos")

st.markdown('</div>', unsafe_allow_html=True)

# Seção de recursos
st.markdown("---")
st.markdown("<h3 style='text-align: center; color: #333;'>✨ O que você pode baixar?</h3>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🎬</div>
        <div class="feature-title">Reels</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📷</div>
        <div class="feature-title">Fotos</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📹</div>
        <div class="feature-title">Vídeos</div>
    </div>
    """, unsafe_allow_html=True)

# Rodapé
st.markdown("""
<div class="footer">
    <p>⚠️ Use apenas para conteúdos que você tem permissão</p>
    <p style="margin-top: 10px;">Feito com ❤️ | InstaSave Pro © 2026</p>
</div>
""", unsafe_allow_html=True)
