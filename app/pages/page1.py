import streamlit as st
from pathlib import Path

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Bu sayfaya erişmek için giriş yapmalısınız.")
    st.stop()

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
    if st.button("📈 Sipariş Tahminleri"):
        with st.spinner("Sayfa yükleniyor..."):
            st.switch_page("pages/gelecek.py")

with col2:
    if st.button("🕵️‍♀️ Beklenen ama Gelmeyen Siparişler"):
        with st.spinner("Sayfa yükleniyor..."):
            st.switch_page("pages/dikkat.py")

# --- 2 Buton Altta ---
col3, col4 = st.columns(2)

with col3:
    if st.button("📊 İstatistikler"):
        with st.spinner("Sayfa yükleniyor..."):
            st.switch_page("pages/stats.py")

with col4:
    if st.button("🏭 Sektörel Değişimler"):
        with st.spinner("Sayfa yükleniyor..."):
            st.switch_page("pages/sektor.py")
