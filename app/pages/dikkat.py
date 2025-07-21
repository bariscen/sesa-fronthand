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
DATA_PATH = "data/dikkat.pkl"

# 'data' klasörü yoksa oluştur
os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

st.markdown("<h2 style='color: #444;'>🚨 Dikkat Edilmesi Gereken Müşteriler</h2>", unsafe_allow_html=True)

try:
    r = requests.get(f"{API_BASE}/dikkat")
    r.raise_for_status()
    data = r.json()

    # Gelen veri içerisinden DataFrame'leri oluştur
    df1 = pd.DataFrame(data["df1"])
    df2 = pd.DataFrame(data["df2"])

    # DataFrame'leri birlikte pickle dosyasına kaydet
    with open(DATA_PATH, "wb") as f:
        pickle.dump({"df1": df1, "df2": df2}, f)

    st.success("Veri başarıyla API'den alındı ve kaydedildi.")
except Exception as e:
    st.warning(f"API'den veri alınamadı, kayıtlı veriye dönülüyor: {e}")

    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "rb") as f:
            data = pickle.load(f)
            df1 = data.get("df1", pd.DataFrame())
            df2 = data.get("df2", pd.DataFrame())
    else:
        st.error("Ne API verisi var ne de kayıtlı dosya. Gösterilecek veri yok.")
        df1 = pd.DataFrame()
        df2 = pd.DataFrame()

if not df1.empty:
    st.subheader("1️⃣ Geçtiğimiz 3 Haftada Kesin Sipariş Vermesi Beklenen ama Vermeyen")
    st.dataframe(df1)
else:
    st.write("Gösterilecek veri yok: 1️⃣")

if not df2.empty:
    st.subheader("2️⃣ Geçtiğimiz 3 Haftada Sipariş Vermesi Beklenen ama Vermeyen")
    st.dataframe(df2)
else:
    st.write("Gösterilecek veri yok: 2️⃣")
