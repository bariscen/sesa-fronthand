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
DATA_PATH_ILK50 = "data/stats_ilk50.pkl"

# data klasörü yoksa oluştur
os.makedirs(os.path.dirname(DATA_PATH_ILK50), exist_ok=True)

st.header("📅 İlk 50 Gün Karşılaştırmaları")

try:
    r = requests.get(f"{API_BASE}/stats-ilk50ler")
    r.raise_for_status()
    gunler = r.json()

    # Veriyi pickle olarak kaydet
    with open(DATA_PATH_ILK50, "wb") as f:
        pickle.dump(gunler, f)

except Exception as e:
    st.warning(f"İlk 50 gün karşılaştırma verisi alınamadı, kayıtlı veriye dönülüyor: {e}")
    if os.path.exists(DATA_PATH_ILK50):
        with open(DATA_PATH_ILK50, "rb") as f:
            gunler = pickle.load(f)
    else:
        st.error("Ne API verisi var ne de kayıtlı dosya. Gösterilecek veri yok.")
        gunler = None

if gunler is not None:
    df_gecen = pd.DataFrame.from_dict(
        gunler["Geçen Seneki İlk 50 Müşteri (Günümüze kadar)"],
        orient="index", columns=["kg_2024"]
    ).reset_index().rename(columns={"index": "Musteri"})

    df_bu = pd.DataFrame.from_dict(
        gunler["Bu Seneki İlk 50 Müşteri (Günümüze kadar)"],
        orient="index", columns=["kg_2025"]
    ).reset_index().rename(columns={"index": "Musteri"})

    stats = gunler["Geçen Sene ve Bu Sene İlk 50 Müşteri Karşılaştırma (Günümüze kadar)"]
    comp = stats["Geçen Seneki ve Bu Seneki İlk 50 Müşterinin Karşılaştırması: "]
    comp_df = pd.DataFrame({
        "Musteri": list(comp["Musteri"].values()),
        "2024": list(comp["2024"].values()),
        "2025": list(comp["2025"].values()),
        "2024-KG": list(comp["kg_2024"].values()),
        "2025-KG": list(comp["kg_2025"].values()),
        "FARKLARI-KG": list(comp["kg_difference"].values())
    })

    st.subheader("📆 2024 - İlk 50 Müşteri")
    st.dataframe(df_gecen)

    st.subheader("📆 2025 - İlk 50 Müşteri")
    st.dataframe(df_bu)

    st.subheader("📊 2024 te Olup 2025 te Olmayan Müşteriler")
    st.dataframe(comp_df)

    st.write(f"📦 Toplam kg 2024: {stats['Geçen Seneki ilk 50 Müşterinin toplam KG (Günümüze kadar): ']}")
    st.write(f"📦 Toplam kg 2025: {stats['Bu Seneki ilk 50 Müşterinin toplam KG: ']}")
else:
    st.write("Gösterilecek İlk 50 gün karşılaştırma verisi yok.")
