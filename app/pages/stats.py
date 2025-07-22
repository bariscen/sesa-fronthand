import streamlit as st
import os
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

# Bu dosyanın bulunduğu dizin
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
    except Exception as e:
        st.warning("Logo yüklenemedi.")
else:
    st.warning("Logo dosyası bulunamadı.")

# Arka plan rengi
st.markdown("""
    <style>
    .stApp {
        background-color: #d3d3d3; /* Açık gri */
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
    if st.button("📊 Sipariş Özetleri"):
        with st.spinner("Sayfa yükleniyor..."):
            st.switch_page("pages/stats_ozet.py")

with col2:
    if st.button("👥 İlk 50 Müşteri Karşılaştırma"):
        with st.spinner("Sayfa yükleniyor..."):
            st.switch_page("pages/stats_ilk50.py")

# --- 1 Buton Altta Ortalanmış ---
col_left, col_center, col_right = st.columns([1, 2, 1])

with col_center:
    if st.button("📉 Giden Müşteri Karşılaştırma"):
        with st.spinner("Sayfa yükleniyor..."):
            st.switch_page("pages/stats_musteri.py")


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
    clicked = st.button("Satış Menüsüne Dön", key="back_to_sales", help="Satış sayfasına dön",
                        args=None, kwargs=None)
    # Yukarıdaki button normal görünüyor, şimdi butona CSS sınıfını JavaScript ile ekleyelim
    # Çünkü Streamlit doğrudan class parametre almıyor

    st.markdown("""
    <script>
    const btn = window.parent.document.querySelector('button[kind="primary"][data-testid^="stButton"][aria-label="Satış Menüsüne Dön"]');
    if(btn){
        btn.classList.add("fixed-button");
    }
    </script>
    """, unsafe_allow_html=True)

if clicked:
    st.switch_page("pages/page1.py")
