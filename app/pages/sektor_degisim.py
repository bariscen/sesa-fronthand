import streamlit as st
import numpy as np
import pandas as pd
import os
from pathlib import Path
import requests
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
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
    # Tarih ve yıl ayırımı
    sektor['month_start'] = pd.to_datetime(sektor['month_start'])
    sektor['Year'] = sektor['month_start'].dt.year
    sektor['Month'] = sektor['month_start'].dt.month
    sektor['Month_Name'] = sektor['month_start'].dt.strftime('%b')

    st.header("📈 Önümüzdeki Ayın Geçen Senelerdeki Performansı")

    # --- Analiz Edilecek Hedef Ayı Belirleme ---
    last_data_month = sektor['month_start'].max()
    target_month_date = last_data_month + pd.DateOffset(months=1)
    target_month_num = target_month_date.month
    target_month_name = target_month_date.strftime('%b')

    #st.write(f"**Analiz edilecek hedef ay:** {target_month_name} (Ay Numarası: {target_month_num})")

    # Hedef aya ait veriler
    df_target_month = sektor[sektor['Month'] == target_month_num]

    # Pivot tablo oluştur
    df_pivot = df_target_month.pivot_table(index='unique_id', columns='Year', values='monthly_total')

    st.write("Önümüzdeki Ayın Geçen Senelerde ki Kiloları:")
    st.dataframe(df_pivot)
