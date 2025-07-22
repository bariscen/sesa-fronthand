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



yillar = read_gcs_blob_content("stat")

if yillar is not None:
    st.write("Veri Seti Yüklendi. ✅")

else:
    st.error("Dikkat verisi çekilemedi.")





if yillar is not None:
    st.subheader("📊 2024 te olan 2025 te Olmayan Müşteriler(Günümüze kadar)")
    st.write(yillar['2024 te olan 2025 te Olmayan Müşteriler(Günümüze kadar)'])


else:
    st.write("Gösterilecek Yıllar Karşılaştırması verisi yok.")
