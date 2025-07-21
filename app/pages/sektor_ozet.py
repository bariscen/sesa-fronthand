import streamlit as st
import numpy as np
import pandas as pd
import os
from pathlib import Path
import requests
import time
import pickle
import matplotlib.pyplot as plt
import seaborn as sns

# Bu dosyanın bulunduğu dizin (app.py'nin dizini)
current_dir = Path(__file__).parent.parent

# row-data yolunu oluştur
image_path_for_logo = current_dir.parent / "row-data" / "sesa-logo-80-new.png"

# Logoyu sakla
if 'logo_image_path' not in st.session_state:
    st.session_state.logo_image_path = str(image_path_for_logo)

st.image(st.session_state.logo_image_path, width=200)

st.markdown("""
    <style>
    .stApp {
        background-color: #d3d3d3;
    }
    </style>
    """, unsafe_allow_html=True)

API_BASE = "http://localhost:8000"
DATA_PATH = "data/sektor.pkl"

os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
st.header("📈 Sektörel Analiz")

# Veri yükleme
try:
    r = requests.get(f"{API_BASE}/sektor")
    r.raise_for_status()
    sektor = pd.DataFrame(r.json())

    with open(DATA_PATH, "wb") as f:
        pickle.dump(sektor, f)

    st.success("Veri başarıyla API'den alındı ve kaydedildi.")
except Exception as e:
    st.warning(f"API'den veri alınamadı, kayıtlı veriye dönülüyor: {e}")
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "rb") as f:
            sektor = pickle.load(f)
    else:
        st.error("Ne API verisi var ne de kayıtlı dosya. Gösterilecek veri yok.")
        sektor = None




# Grafik çiz
if sektor is not None and not sektor.empty:
    st.subheader("📊 3 Aylık Dönemlere Göre Sektörel Satış Trendleri")

    # Tarih formatını ve çeyrek bilgilerini hazırla
    sektor['month_start'] = pd.to_datetime(sektor['month_start'])
    sektor['Quarter_Start'] = sektor['month_start'].dt.to_period('Q').dt.to_timestamp()

    # Çeyrek bazlı toplamlar
    quarterly = sektor.groupby(['unique_id', 'Quarter_Start'])['monthly_total'].sum().reset_index()

    # Grafik oluştur
    g = sns.FacetGrid(quarterly, col='unique_id', col_wrap=2, height=4, aspect=1.3, sharey=False)
    g.map_dataframe(sns.lineplot, x='Quarter_Start', y='monthly_total', marker='o', color='royalblue')

    g.set_axis_labels("3 Aylık Dönem", "Toplam Satış")
    g.set_titles("Kategori: {col_name}")
    plt.suptitle('Kategorilere Göre 3 Aylık Satış Trendleri (2022–2025)', y=1.02, fontsize=16)

    for ax in g.axes.flatten():
        ax.tick_params(axis='x', rotation=45)

    plt.tight_layout(rect=[0, 0.03, 1, 0.98])

    # Streamlit'te göster
    st.pyplot(plt)

else:
    st.info("Henüz gösterilecek veri bulunamadı.")
