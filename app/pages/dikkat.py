import streamlit as st
import numpy as np
import pandas as pd
import os
from pathlib import Path
import requests
import time
import pickle
import streamlit as st
import sys

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

# Projenin kök dizinini (sesa_front) Python'ın arama yoluna ekle.
# gelecek.py dosyası 'app/pages' klasörünün içinde olduğu için,
# Path(__file__).resolve().parent -> app/pages
# .parent.parent -> app
# .parent.parent.parent -> sesa_front (projenin kökü)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Şimdi 'function.py' dosyasını doğrudan projenin kökünden import edebiliriz.
from function import read_gcs_blob_content





# Bu dosyanın bulunduğu dizin (app.py'nin dizini)
current_dir = Path(__file__).parent.parent

# row-data yolunu oluştur
image_path_for_logo = current_dir.parent / "row-data" / "sesa-logo-80-new.png"

# Logonun her sayfada gösterilmesi için session_state'e kaydet
if 'logo_image_path' not in st.session_state:
    st.session_state.logo_image_path = str(image_path_for_logo)

# Ana sayfada logoyu göster (isteğe bağlı, sayfalarda da gösterebilirsin)
st.image(st.session_state.logo_image_path, width=200)

st.markdown("""
    <style>
    .stApp {
        background-color: #d3d3d3; /* 1 ton açık gri */
    }
    </style>
    """, unsafe_allow_html=True)


st.markdown("""
    <style>
    div.stButton > button {
        position: fixed !important;
        top: 10px !important;
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
    div.stButton > button:hover {
        background-color: #555555 !important;
        color: #FFBF00 !important;
    }
    </style>
""", unsafe_allow_html=True)

if st.button("Satış Menüsüne Dön"):
    st.switch_page("pages/page1.py")



data = read_gcs_blob_content("dikkat")

if data is not None:
    st.write("Veri Seti Yüklendi. ✅")

else:
    st.error("Dikkat verisi çekilemedi.")


if data is not None:

    df1 = data[0]
    df2 = data[1]

else:
    st.error("Ne API verisi var ne de kayıtlı dosya. Gösterilecek veri yok.")
    df1 = pd.DataFrame()
    df2 = pd.DataFrame()

if not df1.empty:
    st.subheader("1️⃣ Geçtiğimiz 3 Haftada Kesin Sipariş Vermesi Beklenen ama Vermeyen Müşteriler")
    st.dataframe(df1)
else:
    st.write("Gösterilecek veri yok: 1️⃣")

if not df2.empty:
    st.subheader("2️⃣ Geçtiğimiz 3 Haftada Sipariş Vermesi Beklenen ama Vermeyen Müşteriler")
    st.dataframe(df2)
else:
    st.write("Gösterilecek veri yok: 2️⃣")




#gcloud auth login bariscen36@gmail.com
#gcloud config set project <PROJE_IDNIZ> # Proje ID'nizi buraya yazın (örn: linen-mason-456813-v6 veya kendi projeniz)
#gcloud auth application-default login
