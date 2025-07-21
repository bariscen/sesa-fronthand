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
DATA_PATH = "data/gelecek.pkl"

os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
st.header("📈 Gelecek Müşteri Beklentisi")

# FastAPI'den veri çekmeyi dene
try:
    r = requests.get(f"{API_BASE}/gelecek")
    r.raise_for_status()  # Hata varsa tetikler
    gelecek_df = pd.DataFrame(r.json())

    # Gelen veriyi .pkl olarak kaydet
    with open(DATA_PATH, "wb") as f:
        pickle.dump(gelecek_df, f)

    st.success("Veri başarıyla API'den alındı ve kaydedildi.")
except Exception as e:
    st.warning(f"API'den veri alınamadı, kayıtlı veriye dönülüyor: {e}")

    # .pkl dosyası varsa onu oku
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "rb") as f:
            gelecek_df = pickle.load(f)
    else:
        st.error("Ne API verisi var ne de kayıtlı dosya. Gösterilecek veri yok.")
        gelecek_df = None

# Veriyi göster
if gelecek_df is not None:
    st.dataframe(gelecek_df)
