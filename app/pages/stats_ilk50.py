

import streamlit as st
import numpy as np
import pandas as pd
import os
from pathlib import Path
import requests
import time
import pickle
import streamlit as st
from app.function import read_gcs_blob_content
import json

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



gunler = read_gcs_blob_content("stat")

if gunler is not None:
    st.write("Veri Seti Yüklendi. ✅")

else:
    st.error("Dikkat verisi çekilemedi.")



if gunler is not None:
    df_gecen = gunler["Geçen Seneki İlk 50 Müşteri (Günümüze kadar)"]
    df_gecen.columns = ["Musteri", "kg_2024"]

    df_bu = gunler["Bu Seneki İlk 50 Müşteri (Günümüze kadar)"]
    df_bu.columns = ['Musteri', "kg_2025"]


    comp_df = gunler["Geçen Sene ve Bu Sene İlk 50 Müşteri Karşılaştırma (Günümüze kadar)"]['Geçen Seneki ve Bu Seneki İlk 50 Müşterinin Karşılaştırması: ']

    st.subheader("📆 2024 - İlk 50 Müşteri")
    st.dataframe(df_gecen)

    st.subheader("📆 2025 - İlk 50 Müşteri")
    st.dataframe(df_bu)

    st.subheader("📊 2024 ile 2025 ilk 50 Müşteri Karşılaştırma (Günümüze kadar)")
    st.dataframe(comp_df)

    stat = gunler["Geçen Sene ve Bu Sene İlk 50 Müşteri Karşılaştırma (Günümüze kadar)"]

    st.write(f"📦 Toplam kg 2024: {round(stat['Geçen Seneki ilk 50 Müşterinin toplam KG (Günümüze kadar): '])}")
    st.write(f"📦 Toplam kg 2025: {round(stat['Bu Seneki ilk 50 Müşterinin toplam KG: '])}")
else:
    st.write("Gösterilecek İlk 50 gün karşılaştırma verisi yok.")
