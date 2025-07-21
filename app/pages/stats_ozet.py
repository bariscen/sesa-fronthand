import streamlit as st
import numpy as np
import pandas as pd
import os
from pathlib import Path
import requests
import time
import pickle


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


API_BASE = "http://localhost:8000"
DATA_PATH_OZET = "data/stats_ozet.pkl"


# data klasörü yoksa oluştur
os.makedirs(os.path.dirname(DATA_PATH_OZET), exist_ok=True)

st.header("📊 İstatistiksel Özet")

try:
    r = requests.get(f"{API_BASE}/stats-ozet")
    r.raise_for_status()
    ozet = r.json()

    # ozet verisini kaydet
    with open(DATA_PATH_OZET, "wb") as f:
        pickle.dump(ozet, f)

    st.json(ozet)
except Exception as e:
    st.warning(f"İstatistik özeti alınamadı, kayıtlı veriye dönülüyor: {e}")
    if os.path.exists(DATA_PATH_OZET):
        with open(DATA_PATH_OZET, "rb") as f:
            ozet = pickle.load(f)
        st.json(ozet)
    else:
        st.error("Ne API verisi var ne de kayıtlı dosya. Gösterilecek özet veri yok.")
        ozet = None
