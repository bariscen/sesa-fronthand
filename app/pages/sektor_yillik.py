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
import streamlit as st
from app.function import read_gcs_blob_content

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
if st.button("Sektöre Git", key="btn_sector"):
    st.switch_page("pages/sektor.py")


sektor = read_gcs_blob_content("sektor")

if sektor is not None:
    st.write("Veri Seti Yüklendi. ✅")

else:
    st.error("verisi çekilemedi.")


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
