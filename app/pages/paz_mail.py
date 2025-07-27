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
from app.gpt import get_observation, extract_sector, rag, referans, generate_better_email, create_personalized_email


os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["LANGSMITH_API_KEY"] = st.secrets["LANGSMITH_API_KEY"]
os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
import PyPDF2

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = "langchain-academy"





sektor_ulke = read_gcs_blob_content("sesa1")

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

st.markdown("""
    <style>
    div[data-testid="pazarlama_button"] button {
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
    div[data-testid="pazarlama_button"] button:hover {
        background-color: #555555 !important;
        color: #FFBF00 !important;
    }
    </style>
""", unsafe_allow_html=True)

# SADECE bu button'a özel container (testid kullanılıyor)
with st.container():
    st.markdown('<div data-testid="pazarlama_button">', unsafe_allow_html=True)
    if st.button("Pazarlama Menüsüne Dön", key="pazarlama"):
        st.switch_page("pages/page2.py")
    st.markdown("</div>", unsafe_allow_html=True)

import streamlit as st

# Title
st.title("Cold Mail ve Cold Call Üreticisine Hoşgeldin")

# Create a form with a box layout
with st.form("Cold Mail Üreticisine Hoşgeldin"):
    st.subheader("Şirket Detayları")

    name = st.text_input("Name")
    company_name = st.text_input("Company Name")
    position = st.text_input("Position")
    state = st.selectbox("State", ['TR', 'NL', 'QA', 'SE', 'PL', 'CY', 'GB', 'TN', 'GR', 'FR', 'IL',
       'US', 'RO', 'BG', 'MA', 'DE', 'IT'])

    # Submit button
    submitted = st.form_submit_button("Submit")

    if submitted:
        st.success(f"Submitted: {name}, {position}, {state}")
        tavily_res = get_observation(company_name)
        #st.write(tavily_res)
        #st.write('----------🧭-------------')
        target_sector = extract_sector(tavily_res)
        #st.write(target_sector)
        st.write('----------🧭-------------')
        pdf_path = current_dir / "data" / "RAG-SESA.pdf"
        context = rag(pdf_path)
        referanslar = referans(sektor_ulke, target_sector, state)
        result = generate_better_email(tavily_res, position,target_sector , context, company_name, referanslar)
        st.session_state["generated_result"] = result
        st.session_state['name']=name
        st.session_state['language']=state
        st.write(result)

if st.button("Çeviri ve Mail Formu"):
    if "generated_result" in st.session_state:
        translated = create_personalized_email(st.session_state["generated_result"], st.session_state['name'],st.session_state['language'] )
        st.write('----------🧭-------------')
        st.write(translated)
        st.write('💫 Mailin hazır! İyi Şanslar!')
    else:
        st.warning("Please fill out and submit the form first.")

if st.button("Sadece Mail Formu"):
    if "generated_result" in st.session_state:
        translated = create_personalized_email(st.session_state["generated_result"], st.session_state['name'])
        st.write('----------🧭-------------')
        st.write(translated)
        st.write('💫 Mailin hazır! İyi Şanslar!')
    else:
        st.warning("Please fill out and submit the form first.")


if st.button("Çoklu Mail Üreticisine Git"):
        with st.spinner("Sayfa yükleniyor..."):
            st.switch_page("pages/paz_mail_coklu.py")
