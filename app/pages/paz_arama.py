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


from typing import List
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from IPython.display import Image, display
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import operator
from typing import  Annotated
from langgraph.graph import MessagesState
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.document_loaders import WikipediaLoader
from IPython.display import Markdown
import operator
from typing import List, Annotated
from typing_extensions import TypedDict
import operator
from typing import List, Annotated
from typing_extensions import TypedDict
import time
from openai import RateLimitError


openai_api_key = st.secrets.get("OPENAI_API_KEY")
langsmith_api_key = st.secrets.get("LANGSMITH_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["LANGSMITH_API_KEY"] = langsmith_api_key
os.environ["TAVILY_API_KEY"] = tavily_api_key
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults


llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = "langchain-academy"



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

from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain


with st.form("Cold Call için Firma Bilgileri"):
    st.subheader("Şirket Detayları")

    company_name = st.text_input("Company Name")
    position = st.text_input("Position")

    st.session_state['company']= company_name
    st.session_state['position']= position

    # Submit button
    submitted = st.form_submit_button("Submit")

    if submitted:


        prompt_template = ChatPromptTemplate.from_template("""
        Sen deneyimli bir B2B satış temsilcisisin. Aşağıdaki firma hakkında soğuk arama yapmadan önce bilgi topluyorsun.
        Firma adı: {company_name}
        İlgili kişi pozisyonu: {contact_role}

        {company_name} bunları cevaplandır:
        1. Şirket Tanımı
        2. Sektör & Faaliyet Alanları
        3. Sattığı ürünler
        4. Plastik ambalaj kullanımı
        5. Sürdürebilirlik politikaları
        6. Dijital Varlıklar
        7. Muhtemel İhtiyaçlar / Ağrı Noktaları
        8. Soğuk Arama İçin Notlar
        """)

        # Zincir oluştur
        company_profile_chain = LLMChain(
            llm=llm,
            prompt=prompt_template
        )

        # Fonksiyonel hale getir
        def get_company_profile(company_name, contact_role=""):
            return company_profile_chain.run({
                "company_name": company_name,
                "contact_role": contact_role
            })

st.write(get_company_profile(st.session_state['company'], st.session_state['position']))
