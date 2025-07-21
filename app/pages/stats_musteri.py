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
DATA_PATH_YILLAR = "data/stats_yillar.pkl"

os.makedirs(os.path.dirname(DATA_PATH_YILLAR), exist_ok=True)

st.header("📈 Yıllar Karşılaştırması ve Müşteri Kayıpları")

try:
    r = requests.get(f"{API_BASE}/stats-karsilastirma")
    r.raise_for_status()
    yillar = r.json()

    # Veriyi pickle olarak kaydet
    with open(DATA_PATH_YILLAR, "wb") as f:
        pickle.dump(yillar, f)

except Exception as e:
    st.warning(f"Yıl karşılaştırmaları alınamadı, kayıtlı veriye dönülüyor: {e}")
    if os.path.exists(DATA_PATH_YILLAR):
        with open(DATA_PATH_YILLAR, "rb") as f:
            yillar = pickle.load(f)
    else:
        st.error("Ne API verisi var ne de kayıtlı dosya. Gösterilecek veri yok.")
        yillar = None

if yillar is not None:
    st.write(yillar['Yılların Karşılaştırması'])

    comp = yillar["2024 te olan 2025 te Olmayan Müşteriler(Günümüze kadar)"]
    comp_df = pd.DataFrame({
        "Musteri": list(comp["Musteri"].values()),
        "Sektor": list(comp["Sektor"].values()),
        "Satisci": list(comp["Satisci"].values()),
        "KG": list(comp["kg"].values()),
    })

    st.subheader("📊 Karşılaştırma")
    st.dataframe(comp_df)
else:
    st.write("Gösterilecek Yıllar Karşılaştırması verisi yok.")
