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

# CSS personalizado
st.markdown("""
<style>
    /* Fundo gradiente suave */
    .stApp {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        min-height: 100vh;
    }
    
    /* Título principal com gradiente Instagram */
    .main-title {
        background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        font-size: 3.5em !important;
        font-weight: 800 !important;
        margin-bottom: 10px;
        letter-spacing: -1px;
    }
    
    /* Subtítulo */
    .subtitle {
        text-align: center;
        color: #555 !important;
        font-size: 1.2em !important;
        margin-bottom: 40px;
        font-weight: 400;
        line-height: 1.6;
    }
    
    /* Card principal branco */
    .main-card {
        background: white;
        border-radius: 24px;
        padding: 40px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.08);
        margin: 0 auto 40px auto;
        max-width: 700px;
    }
    
    /* TRUQUE: Esconde a label do text_input mas mantém o input */
    [data-testid="stTextInput"] label {
        display: none !important;
    }
    
    /* Campo de input */
    [data-testid="stTextInput"] input {
        border-radius: 15px !important;
        border: 2px solid #e0e0e0 !important;
        padding: 18px 20px !important;
        font-size: 1.05em !important;
        background: #fafafa !important;
        color: #333 !important;
        transition: all 0.3s ease;
    }
    
    [data-testid="stTextInput"] input:focus {
        border-color: #dc2743 !important;
        background: white !important;
        box-shadow: 0 0 0 4px rgba(220, 39, 67, 0.1);
    }
    
    [data-testid="stTextInput"] input::placeholder {
        color: #999 !important;
    }
    
    /* Botão principal estilizado */
    .stButton > button {
        background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
        color: white !important;
        border: none;
        border-radius: 50px;
        padding: 18px 40px;
        font-size: 1.15em;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 6px 20px rgba(220, 39, 67, 0.35);
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(220, 39, 67, 0.5);
    }
    
    .stButton > button:active {
        transform: translateY(-1px);
    }
    
    /* Alertas e mensagens */
    .stAlert {
        border-radius: 15px !important;
        padding: 15px 20px !important;
        margin: 15px 0 !important;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
        border-radius: 50px;
        padding: 18px 40px;
        font-size: 1.15em;
        font-weight: bold;
        width: 100%;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.35);
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.5);
    }
    
    /* Cards de recursos */
    .feature-card {
        background: white;
        padding: 30px 20px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .feature-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.12);
    }
    
    .feature-icon {
        font-size: 3em;
        margin-bottom: 15px;
    }
    
    .feature-title {
        color: #333 !important;
        font-weight: 700;
        font-size: 1.15em;
    }
    
    /* Título da seção */
    .section-title {
        text-align: center;
        color: #333 !important;
        font-size: 1.8em !important;
        font-weight: 700 !important;
        margin-bottom: 30px;
    }
    
    /* Rodapé */
    .footer {
        text-align: center;
        color: #888 !important;
        margin-top: 40px;
        font-size: 0.9em;
        line-height: 1.8;
    }
    
    /* Esconder menu e footer padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #dc2743 !important;
    }
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
st.markdown('<h1 class="main-title">InstaSave Pro</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Baixe vídeos, reels e fotos do Instagram<br>de forma rápida e gratuita</p>', unsafe_allow_html=True)

# Card principal
st.markdown('<div class="main-card">', unsafe_allow_html=True)

# Campo de URL (sem label visível e sem barra branca)
url = st.text_input(
    "url_input",
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
                    emoji = ""
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
st.markdown("<h2 class='section-title'>✨ O que você pode baixar?</h2>", unsafe_allow_html=True)

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
    <p>Feito com ❤️ | InstaSave Pro © 2026</p>
</div>
""", unsafe_allow_html=True)
