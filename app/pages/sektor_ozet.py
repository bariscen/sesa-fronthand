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
from google.cloud import storage
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
