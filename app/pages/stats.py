import streamlit as st
import os
from pathlib import Path


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
