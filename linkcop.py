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

# CSS personalizado para estilo Instagram
st.markdown("""
<style>
    /* Fundo gradiente */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f09433 100%);
        min-height: 100vh;
    }
    
    /* Container principal */
    .main-container {
        background: white;
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        margin: 40px auto;
        max-width: 600px;
    }
    
    /* Título principal */
    .main-title {
        font-size: 3em;
        font-weight: bold;
        background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 10px;
        animation: gradient 3s ease infinite;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Subtítulo */
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.1em;
        margin-bottom: 30px;
    }
    
    /* Botão estilizado */
    .stButton > button {
        background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 15px 40px;
        font-size: 1.2em;
        font-weight: bold;
        cursor: pointer;
        transition: transform 0.3s, box-shadow 0.3s;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(220, 39, 67, 0.4);
    }
    
    /* Campo de input */
    .stTextInput > div > input {
        border-radius: 15px;
        border: 2px solid #e0e0e0;
        padding: 15px;
        font-size: 1em;
        transition: border-color 0.3s;
    }
    
    .stTextInput > div > input:focus {
        border-color: #dc2743;
    }
    
    /* Cards de sucesso */
    .success-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        text-align: center;
    }
    
    /* Ícones */
    .icon {
        font-size: 4em;
        text-align: center;
        margin-bottom: 20px;
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
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Título estiloso
st.markdown('<div class="icon">📸</div>', unsafe_allow_html=True)
st.markdown('<h1 class="main-title">InstaSave Pro</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Baixe vídeos, reels e fotos do Instagram<br>de forma rápida e gratuita</p>', unsafe_allow_html=True)

st.markdown("---")

# Campo de URL
url = st.text_input(
    "",
    placeholder="🔗 Cole o link do Instagram aqui...",
    label_visibility="collapsed"
)

# Botão de download
if st.button("️ BAIXAR AGORA", use_container_width=True):
    if not url:
        st.error("⚠️ Por favor, cole um link do Instagram!")
    elif not validar_instagram(url):
        st.error("❌ Link inválido! Use links de posts, reels ou stories.")
    else:
        with st.spinner(" Processando..."):
            inicio = time.time()
            arquivo, info, dados = baixar_instagram(url)
            tempo_total = round(time.time() - inicio, 1)
            
            if arquivo and os.path.exists(arquivo):
                tamanho_mb = round(os.path.getsize(arquivo) / (1024 * 1024), 2)
                
                st.markdown(f"""
                <div class="success-card">
                    <h2>✅ Download Concluído!</h2>
                    <p>Tempo: {tempo_total}s | Tamanho: {tamanho_mb} MB</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.info(f"📄 **Arquivo:** {info}")
                
                # Determina tipo de arquivo
                if arquivo.endswith('.mp4'):
                    mime_type = "video/mp4"
                    emoji = ""
                elif arquivo.endswith('.jpg'):
                    mime_type = "image/jpeg"
                    emoji = "📷"
                else:
                    mime_type = "video/mp4"
                    emoji = "📹"
                
                # Botão de download estilizado
                with open(arquivo, "rb") as f:
                    st.download_button(
                        label=f"{emoji} BAIXAR ARQUIVO",
                        data=f,
                        file_name=os.path.basename(arquivo),
                        mime=mime_type,
                        use_container_width=True,
                        type="primary"
                    )
                
                # Botão para abrir pasta
                if st.button("📁 Abrir Local", use_container_width=True):
                    st.info(f"Arquivo salvo em: {os.path.dirname(arquivo)}")
            else:
                st.error(f"❌ Erro no download: {info}")
                st.info("💡 **Dicas:**\n- Verifique se o link está correto\n- O post pode ser privado\n- Tente novamente em alguns minutos")

st.markdown("---")

# Recursos
st.markdown("""
<div style="text-align: center; margin-top: 30px;">
    <h3 style="color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">✨ Recursos</h3>
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-top: 20px;">
        <div style="background: white; padding: 15px; border-radius: 10px;">
            <div style="font-size: 2em;">🎬</div>
            <div style="color: #333; font-weight: bold;">Reels</div>
        </div>
        <div style="background: white; padding: 15px; border-radius: 10px;">
            <div style="font-size: 2em;">📷</div>
            <div style="color: #333; font-weight: bold;">Fotos</div>
        </div>
        <div style="background: white; padding: 15px; border-radius: 10px;">
            <div style="font-size: 2em;"></div>
            <div style="color: #333; font-weight: bold;">Vídeos</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Rodapé
st.markdown("""
<div style="text-align: center; margin-top: 30px; color: white; font-size: 0.9em;">
    <p>⚠️ Use apenas para conteúdos que você tem permissão</p>
    <p style="margin-top: 10px; font-size: 0.8em;">
        Feito com ❤️ | InstaSave Pro © 2026
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Sidebar com informações
with st.sidebar:
    st.markdown("""
    <div style="text-align: center;">
        <h2>ℹ️ Como Usar</h2>
        <ol style="text-align: left; line-height: 2;">
            <li>Abra o Instagram</li>
            <li>Copie o link do post/reel</li>
            <li>Cole no campo acima</li>
            <li>Clique em "Baixar Agora"</li>
            <li>Salve o arquivo!</li>
        </ol>
        
        <div style="margin-top: 30px; padding: 20px; background: #f0f0f0; border-radius: 10px;">
            <h3>📱 Tipos Suportados</h3>
            <ul style="text-align: left;">
                <li>✅ Posts com vídeo</li>
                <li>✅ Reels</li>
                <li>✅ IGTV</li>
                <li>✅ Stories (se público)</li>
                <li>✅ Fotos</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
