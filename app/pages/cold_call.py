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
from app.gpt import cold_call_cevir


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


# ... mevcut importlar ...
import io, datetime
import pandas as pd
import streamlit as st

@st.cache_data(show_spinner=False)
def df_to_xlsx_bytes(df_json: str) -> bytes:
    """DataFrame'i (JSON, orient='split') XLSX bayta çevirir. Rerun'larda cache kullanılır."""
    df = pd.read_json(df_json, orient="split")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Emails")
    return output.getvalue()




st.title("📂 CSV Dosyası Yükleme")

uploaded_file = st.file_uploader("CSV dosyanızı yükleyin", type=["csv"])

if uploaded_file is not None:
    state = st.text_input("State")
    try:
        df = pd.read_csv(uploaded_file)
        st.success(f"✅ Yüklenen dosya: {uploaded_file.name}")
        st.write("📊 Veri Önizlemesi:")
        st.dataframe(df)
    except Exception as e:
        st.error(f"❌ CSV okunurken hata oluştu: {e}")

# === ÜLKE SEÇİMİ (GENEL VARSAYILAN) ===
allowed = ["EN","FR","DE","UK","ES","IT","TR"]

country_box = st.selectbox("Ülke/Lokal (ara dili)", allowed, index=0,
                           help="Arama dili/ülke önceliği. EN=Genel İngilizce")

# Opsiyonel: serbest metinle kod girilirse map et
RAW = st.text_input("Ülke kodu (opsiyonel, örn: FR/DE/UK/ES/IT/TR/EN)")
MAP = {
    "fr":"FR","france":"FR",
    "de":"DE","germany":"DE","deutschland":"DE",
    "uk":"UK","united kingdom":"UK","gb":"UK",
    "es":"ES","spain":"ES","españa":"ES",
    "it":"IT","italy":"IT","italia":"IT",
    "tr":"TR","turkey":"TR","türkiye":"TR",
    "en":"EN","english":"EN"
}
country_code = country_box  # varsayılan
if RAW.strip():
    country_code = MAP.get(RAW.strip().lower(), RAW.strip().upper())
    if country_code not in allowed:
        st.warning(f"Geçersiz ülke kodu: {country_code}. EN kullanılacak.")
        country_code = "EN"

# İleride kullanmak için session_state'e koy
st.session_state["country_default"] = country_code


# --- ek importlar (YENİ) ---
import time, random
from pathlib import Path
import io

if uploaded_file is not None:
    # --- en üstlerde bir kere: ---


    # KeyError önlemek için:
    if 'cold_call' not in st.session_state:
        st.session_state['cold_call'] = None

    # --- senin bloğunun yerine: ---
    if uploaded_file is not None:
        if st.button("Mail Dönüşümü Başlat"):
            # Çıktı kolonlarını hazırla
            if 'report' not in df.columns:
                df['report'] = ""
            if 'score' not in df.columns:
                df['score'] = pd.NA

            companies = df['Company'].fillna("").astype(str)
            total = len(companies)

            # Görsel göstergeler
            header_ph = st.empty()
            row_msg_ph = st.empty()
            prog = st.progress(0, text="Başlıyor…")

            header_ph.info(f"Toplam {total} şirket işlenecek.")

            for i, (idx, company_name) in enumerate(companies.items(), start=1):
                if not company_name.strip():
                    df.at[idx, 'report'] = "Şirket adı boş"
                    df.at[idx, 'score'] = None
                else:
                    row_msg_ph.write(f"🔎 {i}/{total} — **{company_name}** işleniyor…")
                    try:
                        # satıra özel ülke kodu (CSV'de Country/State varsa oradan; yoksa genel seçim)
                        row_country = st.session_state.get("country_default", "EN")
                        for cand in ["Country","State","country","state"]:
                            if cand in df.columns:
                                raw = str(df.at[idx, cand] or "").strip()
                                if raw:
                                    rc = MAP.get(raw.lower(), raw.upper())
                                    if rc in allowed:
                                        row_country = rc
                                break

                        report, score = cold_call_cevir(company_name, country=row_country)

                    except Exception as e:
                        report, score = f"Hata: {e}", None

                    df.at[idx, 'report'] = report
                    df.at[idx, 'score'] = score

                prog.progress(i/total, text=f"{i}/{total} tamamlandı")
                st.toast(f"{company_name} ✓")
                # (Opsiyonel) hız çok yüksekse mini bekleme:
                # time.sleep(0.05)

            # Diğer kolonlar
            df['Soğuk Arama Gerçekleşti'] = pd.NaT
            df['linkedin Eklendi'] = pd.NaT

            # Session state'e yaz
            st.session_state['cold_call'] = df[['Country', 'Company', 'Website', 'Company Phone',
                                                'First Name', 'Last Name', 'Title', 'Departments',
                                                'Corporate Phone', 'Person Linkedin Url', 'Email',
                                                'report', 'score']]

    # Varsa göster (butona basmadan önce KeyError olmasın)
if st.session_state['cold_call'] is not None:
    st.dataframe(st.session_state['cold_call'])

# --- indirme bölümü aynı kalabilir, sadece korumalı erişim: ---
if st.session_state.get('cold_call') is not None:
# DF'i JSON'a çevir (cache için stabil girdi)
    df_json = st.session_state['cold_call'].to_json(orient="split")

    # Baytları sadece veri değişince üret (cache'li fonksiyon)
    xlsx_bytes = df_to_xlsx_bytes(df_json)

    # (Opsiyonel) session_state'te sakla
    st.session_state['xlsx_bytes'] = xlsx_bytes

    st.download_button(
        label="📥 Excel olarak indir",
        data=xlsx_bytes,
        file_name="kontakt_listesi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
