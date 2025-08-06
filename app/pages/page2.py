import streamlit as st
from pathlib import Path

### SIDE BAR KAPAMA BASLIYOR

st.set_page_config(initial_sidebar_state="collapsed")

st.markdown(
    """
<style>
    [data-testid="collapsedControl"] {
        display: none
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("""
    <style>
    /* Menü (sidebar navigation) gizle */
    section[data-testid="stSidebarNav"] {
        display: none;
    }
    /* Sağ üstteki hamburger menü gizle */
    button[title="Toggle sidebar"] {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)


### SIDE BAR KAPAMA BİTTİ

# Bu dosyanın bulunduğu dizin (örneğin: pages/page1.py)
current_dir = Path(__file__).parent.parent

# row-data yolunu oluştur
image_path_for_logo = current_dir.parent / "row-data" / "sesa-logo-80-new.png"

# Logonun her sayfada gösterilmesi için session_state'e kaydet
if 'logo_image_path' not in st.session_state:
    if image_path_for_logo.exists():
        st.session_state.logo_image_path = str(image_path_for_logo)
    else:
        st.session_state.logo_image_path = None

# Logoyu göster
if st.session_state.logo_image_path:
    try:
        st.image(st.session_state.logo_image_path, width=200)
    except:
        st.warning("Logo yüklenemedi.")
else:
    st.warning("Logo dosyası bulunamadı.")

# Sayfa arka planını ayarla
st.markdown("""
    <style>
    .stApp {
        background-color: #d3d3d3;
    }
    </style>
    """, unsafe_allow_html=True)

# Buton stilini ayarla
st.markdown("""
<style>
div.stButton > button {
    font-size: 24px;
    padding: 20px 40px;
    border-radius: 10px;
    background-color: #FFBF00;
    color: black;
    border: 2px solid #444;
    margin: 5px;
}
</style>
""", unsafe_allow_html=True)

# --- 2 Buton Üstte ---
col1, col2 = st.columns(2)

with col1:
    if st.button("🧬 Cold Email ve Cold Call Oluştur"):
        with st.spinner("Sayfa yükleniyor..."):
            st.switch_page("pages/paz_mail.py")

with col2:
    if st.button("📿 Çoklu Cold Email ve Cold Call Oluştur"):
        with st.spinner("Sayfa yükleniyor..."):
            st.switch_page("pages/paz_mail_coklu.py")
# --- 2 Buton Altta ---
col3, col4 = st.columns(2)

with col3:
    if st.button("📬 Gazete"):
        with st.spinner("Sayfa yükleniyor..."):
            st.switch_page("pages/paz_ic_gazete.py")

with col4:
    if st.button("💾 Likedin İçerik Üretimi"):
        with st.spinner("Sayfa yükleniyor..."):
            st.switch_page("pages/paz_ic_linkedin.py")





st.markdown("""
    <style>
    /* Sadece fixed-button sınıfına sahip buttona uygulanır */
    .fixed-button {
        position: fixed !important;
        top: 30px !important;
        right: 10px !important;
        background-color: #444444 !important;
        color: #FFBF00 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 12px 24px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        cursor: pointer !important;
        z-index: 9999 !important;
        transition: background-color 0.3s ease !important;
    }
    .fixed-button:hover {
        background-color: #555555 !important;
        color: #FFBF00 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Özel stil için butonu container içine al ve sınıfı ver
button_placeholder = st.empty()
with button_placeholder.container():
    # Butonun key parametresi önemli, her butonun unique olmalı
    clicked = st.button("Ana Sayfaya Dön", key="back_to_main", help="Menüye dön",
                        args=None, kwargs=None)
    # Yukarıdaki button normal görünüyor, şimdi butona CSS sınıfını JavaScript ile ekleyelim
    # Çünkü Streamlit doğrudan class parametre almıyor

    st.markdown("""
    <script>
    const btn = window.parent.document.querySelector('button[kind="primary"][data-testid^="stButton"][aria-label="Menüye Dön"]');
    if(btn){
        btn.classList.add("fixed-button");
    }
    </script>
    """, unsafe_allow_html=True)

if clicked:
    st.switch_page("main.py")
