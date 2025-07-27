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


# from langchain.chat_models import ChatOpenAI
# from langchain.prompts import PromptTemplate
# from langchain.schema import AIMessage, HumanMessage
# from langchain.memory import ConversationBufferMemory
# from difflib import SequenceMatcher

# llm = ChatOpenAI(model="gpt-4", temperature=0.7)

# memory = ConversationBufferMemory(memory_key="history", input_key="topic", return_messages=True)

# template = PromptTemplate(
#     input_variables=["topic"],
#     template="""
# You are a LinkedIn content writer for a sustainable packaging company.

# Topic: {topic}

# Write a professional, engaging LinkedIn post about this topic, tailored for industry professionals.
# Make it original and avoid repeating recent posts.
# """
# )

# def is_similar(new_post, past_posts, threshold=0.8):
#     for post in past_posts:
#         similarity = SequenceMatcher(None, new_post, post).ratio()
#         if similarity > threshold:
#             return True
#     return False

# def generate_post(topic):
#     chain = template | llm
#     response = chain.invoke({"topic": topic})
#     return response.content.strip()

# def update_memory(post):
#     memory.chat_memory.add_user_message("new_post_request")
#     memory.chat_memory.add_ai_message(post)

# def get_recent_posts(n=5):
#     messages = memory.chat_memory.messages
#     return [msg.content for msg in messages if isinstance(msg, AIMessage)][-n:]


import streamlit as st
from langchain.schema import SystemMessage, HumanMessage
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel
from difflib import SequenceMatcher
import openai
from openai import OpenAI
import requests


# --- Persona tanımı ---
class Analyst(BaseModel):
    affiliation: str
    name: str
    role: str
    description: str

    @property
    def persona(self):
        return f"Name: {self.name}\nRole: {self.role}\nAffiliation: {self.affiliation}\nDescription: {self.description}"

linkedin_analyst = Analyst(
    name="Elif Kara",
    role="LinkedIn Content Strategist",
    affiliation="Freelance Marketing Expert",
    description="Focuses on creating weekly LinkedIn posts that drive engagement, thought leadership, and highlight industry trends in flexible packaging."
)

# --- Prompt şablonu ---
post_instructions = """
You are a LinkedIn content strategist agent.

Your goal is to create **1 engaging post per week** for a professional audience in the flexible packaging industry.

The post must be:
- Professional but human
- Insightful (include trends, stats, or expert POV)
- Actionable (tips or questions to encourage interaction)
- No hashtags needed (optional)
- Avoid generic AI-sounding text

Persona:
{persona}

Output format:
POST (Text only, less than 300 words)
"""

# --- Benzerlik kontrolü ---
def is_similar(new_post, memory, threshold=0.8):
    for old in memory:
        if SequenceMatcher(None, new_post, old).ratio() > threshold:
            return True
    return False

# --- LLM post üretimi ---
def generate_linkedin_post(persona_agent: Analyst, topic: str) -> str:
    system_msg = post_instructions.format(persona=persona_agent.persona)
    messages = [
        SystemMessage(content=system_msg),
        HumanMessage(content=f"Create this week's LinkedIn post about: {topic}")
    ]
    response = llm.invoke(messages)
    return response.content

# --- Görsel üretimi (DALL·E 3) ---

client = OpenAI()

def generate_image(prompt: str) -> str:
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )
    return response.data[0].url

# --- Streamlit UI ---
st.title("📣 LinkedIn İçerik Ajanı")

if "past_posts" not in st.session_state:
    st.session_state.past_posts = []

topics = [
    "Latest bio-based films in flexible packaging",
    "How packaging design affects consumer choice",
    "Smart packaging & QR codes in FMCG",
    "Sustainability in supermarket shelf packaging"
]

selected_topic = st.selectbox("📌 Bu haftaki konu:", topics)

if st.button("🪄 İçeriği Oluştur"):
    post = generate_linkedin_post(linkedin_analyst, selected_topic)

    if is_similar(post, st.session_state.past_posts):
        st.warning("⚠️ Bu içerik önceki yazılara çok benziyor. Lütfen tekrar deneyin.")
    else:
        st.success("✅ İçerik başarıyla üretildi!")
        st.text_area("✏️ LinkedIn Postu", post, height=300)

        # Görsel üretimi
        image_url = generate_image(selected_topic)
        st.image(image_url, caption="📷 Otomatik oluşturulan görsel")

        # Görseli indirilebilir hale getir
        try:
            response = requests.get(image_url)
            if response.status_code == 200:
                st.download_button(
                    label="📥 Görseli İndir",
                    data=response.content,
                    file_name="linkedin_gorsel.png",
                    mime="image/png"
                )
            else:
                st.error("⚠️ Görsel indirilemedi.")
        except Exception as e:
            st.error(f"⚠️ Görsel indirme hatası: {str(e)}")

        # Geçmişe ekle
        st.session_state.past_posts.append(post)
        if len(st.session_state.past_posts) > 5:
            st.session_state.past_posts.pop(0)
