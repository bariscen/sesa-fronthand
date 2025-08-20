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
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.function import read_gcs_blob_content
from app.gpt import get_observation, extract_sector, rag, referans, generate_better_email, create_personalized_email, extract_state


openai_api_key = st.secrets.get("OPENAI_API_KEY")
langsmith_api_key = st.secrets.get("LANGSMITH_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["LANGSMITH_API_KEY"] = langsmith_api_key
os.environ["TAVILY_API_KEY"] = tavily_api_key

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
import PyPDF2

llm = ChatOpenAI(model="gpt-4o", temperature=0)
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


st.title("📂 CSV Dosyası Yükleme")

uploaded_file = st.file_uploader("CSV dosyanızı yükleyin", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.success(f"✅ Yüklenen dosya: {uploaded_file.name}")
        st.write("📊 Veri Önizlemesi:")
        st.dataframe(df)
    except Exception as e:
        st.error(f"❌ CSV okunurken hata oluştu: {e}")
# --- ek importlar (YENİ) ---
import time, random
from pathlib import Path

# --- hafif throttle (YENİ) ---
def _throttle(calls_per_minute=12):
    key = "_last_llm_ts"
    interval = 60.0 / calls_per_minute
    last = st.session_state.get(key, 0.0)
    now = time.time()
    wait = (last + interval) - now
    if wait > 0:
        time.sleep(wait)
    st.session_state[key] = time.time()

# --- basit backoff sarmalayıcı (YENİ) ---
def _backoff_call(fn, *args, **kwargs):
    for i in range(6):  # max 6 deneme
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            msg = str(e).lower()
            if "rate limit" in msg or "429" in msg or "rate_limit_exceeded" in msg:
                time.sleep(min(2**i, 30) + random.random())  # üstel + jitter
            else:
                raise
    raise RuntimeError("Rate limit denemeleri tükendi")

# --- caching (YENİ): aynı inputta yeniden çalışmasın ---
@st.cache_data(show_spinner=False)
def _rag_cached(pdf_path_str: str):
    return rag(Path(pdf_path_str))

@st.cache_data(show_spinner=False)
def _observation_cached(company_name: str):
    return get_observation(company_name)

def email(company_name, state, position, name):
        tavily_res = _observation_cached(company_name)
        #st.write(tavily_res)
        target_sector = extract_sector(tavily_res)
        ulke_kodu = extract_state(state)
        #st.write(target_sector)

        pdf_path = current_dir / "data" / "RAG-SESA.pdf"
        context =  _rag_cached(str(pdf_path))
        referanslar = referans(sektor_ulke, target_sector, ulke_kodu)
        _throttle(12)
        result = _backoff_call(
            generate_better_email,tavily_res, position, target_sector, context, company_name, referanslar)

        final = create_personalized_email(result, name)
        st.write('----------🧭 TAMAMLANDI, SIRADAKİNE GEÇİLİYOR -------------')
        return final

if uploaded_file is not None:
    if st.button("Mail Dönüşümü Başlat"):

        df['Email_icerik'] = df.apply(lambda row: email(row['Company'], row['Country'], row['Title'], row['First Name']), axis=1)
        df['Email Atıldı'] = pd.NaT
        df['Soğuk Arama Gerçekleşti'] = pd.NaT
        df['linkedin Eklendi'] = pd.NaT

        st.session_state['email_df'] = df[['Country', 'Company', 'Website', 'Company Phone', 'First Name', 'Last Name', 'Title', 'Departments', 'Corporate Phone', 'Person Linkedin Url',  'Email', 'Email_icerik', 'Email Atıldı',  'Soğuk Arama Gerçekleşti', 'linkedin Eklendi']]

    st.dataframe(st.session_state['email_df'])

    import io

if 'email_df' in st.session_state:
    #st.dataframe(st.session_state['email_df'])

    # Excel'e yazmak için BytesIO buffer oluştur
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state['email_df'].to_excel(writer, index=False, sheet_name='Emails')
    output.seek(0)

    # Excel indirme butonu
    st.download_button(
        label="📥 Excel olarak indir",
        data=output,
        file_name="kontakt_listesi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
