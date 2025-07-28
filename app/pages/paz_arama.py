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

        import streamlit as st
        from langchain.chat_models import ChatOpenAI
        from langchain.schema import HumanMessage
        from langchain.tools.tavily_search import TavilySearchResults

        # OpenAI ve Tavily ayarları
        llm = ChatOpenAI(model="gpt-4", temperature=0.5)
        tavily_search = TavilySearchResults(max_results=3, api_key="YOUR_TAVILY_API_KEY")

        # Web'den bilgi çekme fonksiyonu
        def search_web(company_info):
            query = f"Recent or notable details about {company_info}"
            tavily_results = tavily_search.run(query.strip())
            return tavily_results

        # LLM'e gönderilecek mesajı oluştur
        def llm_search(company_info, web_data):
            prompt = f"""
            You're a B2B sales researcher preparing for a cold call.
            Use the following data to create a short company profile.

            Company Name: {company_info}

            Web Search Results:
            {web_data}

            Please summarize in the following structure:
            1. Company Description
            2. Sector & Offerings
            3. Digital Footprint
            4. Potential Pain Points or Needs
            5. Cold Call Talking Points
            """
            messages = [HumanMessage(content=prompt)]
            response = llm(messages)
            return response.content.strip()

        # Streamlit UI
        if 'company' not in st.session_state:
            st.session_state['company'] = ''

        st.title("Cold Call Company Profiler")
        company_input = st.text_input("Enter company name", value=st.session_state['company'])

        if st.button("Get Info"):
            st.session_state['company'] = company_input
            with st.spinner("Searching the web and generating summary..."):
                tavily_data = search_web(company_input)
                result = llm_search(company_input, tavily_data)
                st.markdown("### Company Profile")
                st.write(result)







                prompt_template = ChatPromptTemplate.from_template("""ds
                                    {company_name}
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
