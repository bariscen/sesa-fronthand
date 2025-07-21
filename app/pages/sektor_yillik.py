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

if sektor is not None and not sektor.empty:
    # Ay sıralaması (Jan, Feb, ... Dec)
    month_order = pd.date_range(start='2000-01-01', periods=12, freq='MS').strftime('%b').tolist()
    sektor['Month_Name'] = pd.Categorical(sektor['Month_Name'], categories=month_order, ordered=True)

    st.subheader("📊 Aylık Satış Trendleri (Yıllar Bazında)")

    # FacetGrid: her kategori için ayrı grafik, 2 grafik / satır
    g = sns.FacetGrid(sektor, col='unique_id', col_wrap=2, height=4, aspect=1.4, sharey=False)

    # Yıllara göre farklı renklerle çizim
    g.map_dataframe(sns.lineplot, x='Month_Name', y='monthly_total', hue='Year', marker='o', palette='viridis')

    # Lejant ekle
    g.add_legend(title='Yıl')

    # Eksen ve başlıklar
    g.set_axis_labels("Ay", "Aylık Toplam Satış")
    g.set_titles("Kategori: {col_name}")
    plt.suptitle('Kategorilere Göre Aylık Satış Trendleri (Yıllar Arası Karşılaştırma)', y=1, fontsize=16)
    plt.figtext(0.5, 0.99, '2022: MOR, 2023: MAVİ, 2024: YEŞİL, 2025: SARI', ha='center', fontsize=12)
    plt.tight_layout(rect=[0, 0.03, 1, 0.975])

    # Streamlit'te göster
    st.pyplot(plt)
