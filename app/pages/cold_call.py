# streamlit_app.py

import os, io, datetime, tempfile
from pathlib import Path
from typing import List
import pandas as pd
import streamlit as st
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

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = "langchain-academy"

import google.generativeai as genai
os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

gemini_key = st.secrets["GEMINI_API_KEY"]
model_gemini = genai.GenerativeModel('gemini-1.5-pro-latest')




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


# ====== Ortam/anahtarlar (varsa diğer sayfalarda kullanılıyor) ======
openai_api_key = st.secrets.get("OPENAI_API_KEY")
langsmith_api_key = st.secrets.get("LANGSMITH_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")
if openai_api_key: os.environ["OPENAI_API_KEY"] = openai_api_key
if langsmith_api_key: os.environ["LANGSMITH_API_KEY"] = langsmith_api_key
if tavily_api_key: os.environ["TAVILY_API_KEY"] = tavily_api_key

# --- OpenAI tarafını kullanan kendi fonksiyonun ---
from app.gpt import cold_call_cevir

# ===================== Session State INIT =====================
if 'cold_call' not in st.session_state:
    st.session_state['cold_call'] = None
if 'progress_i' not in st.session_state:
    st.session_state['progress_i'] = 0
if 'country_default' not in st.session_state:
    st.session_state['country_default'] = "EN"
if 'cc_cache' not in st.session_state:
    st.session_state['cc_cache'] = {}

# ===================== Autosave Yolları =====================
AUTO_CSV  = Path(tempfile.gettempdir()) / "cold_call_autosave.csv"
AUTO_XLSX = Path(tempfile.gettempdir()) / "cold_call_autosave.xlsx"

# ===================== Yardımcılar =====================
allowed = ["EN","FR","DE","UK","ES","IT","TR"]
MAP = {
    "fr":"FR","france":"FR",
    "de":"DE","germany":"DE","deutschland":"DE",
    "uk":"UK","united kingdom":"UK","gb":"UK",
    "es":"ES","spain":"ES","españa":"ES",
    "it":"IT","italy":"IT","italia":"IT",
    "tr":"TR","turkey":"TR","türkiye":"TR",
    "en":"EN","english":"EN"
}

def normalize_country_code(raw: str) -> str:
    if not raw:
        return ""
    cand = MAP.get(raw.strip().lower(), raw.strip().upper())
    return cand if cand in allowed else ""

def resolve_row_country(df: pd.DataFrame, idx, default_code: str) -> str:
    for cand in ["Country","State","country","state"]:
        if cand in df.columns:
            raw = str(df.at[idx, cand] or "").strip()
            rc = normalize_country_code(raw)
            if rc:
                return rc
    return default_code

def safe_subset(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    present = [c for c in cols if c in df.columns]
    return df[present]


def call_with_cache(name: str, country: str, website: str = None, sector: str = None):
    key = (name.strip().lower(), country, (website or "").strip().lower(), (sector or "").strip().lower())
    if key in st.session_state['cc_cache']:
        return st.session_state['cc_cache'][key]
    out = cold_call_cevir(name, country=country, website=website, sector=sector)
    st.session_state['cc_cache'][key] = out
    return out


@st.cache_data(show_spinner=False)
def df_to_xlsx_bytes(df_json: str) -> bytes:
    """DataFrame'i (JSON, orient='split') XLSX bayta çevirir; veri aynıysa cache'den verir."""
    df = pd.read_json(df_json, orient="split")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Emails")
    return output.getvalue()

def _merge_autosave_into_df(df: pd.DataFrame, saved: pd.DataFrame):
    """Autosave içeriğini aktif df'ye bindir. Başlangıç indexini (işlenmiş satır sayısı) döndürür."""
    df = df.copy()
    if len(saved) == len(df):
        for col in ["report","score"]:
            if col in saved.columns:
                df[col] = saved[col]
    elif "Company" in saved.columns and "Company" in df.columns:
        carry_cols = ["Company"] + [c for c in ["report","score"] if c in saved.columns]
        carry = saved[carry_cols].drop_duplicates("Company")
        df = df.merge(carry, on="Company", how="left", suffixes=("", "_saved"))
        if "report_saved" in df.columns:
            df["report"] = df["report"].where(df["report"].notna(), df["report_saved"])
            df.drop(columns=["report_saved"], inplace=True)
        if "score_saved" in df.columns:
            df["score"] = df["score"].where(df["score"].notna(), df["score_saved"])
            df.drop(columns=["score_saved"], inplace=True)
    # kaç satır işlenmiş?
    processed = df.get("report")
    if processed is None:
        start_i = 0
    else:
        start_i = int(processed.astype(str).str.strip().str.len().gt(0).sum())
    return df, start_i


# streamlit_app.py (SEKTÖR EKLENDİ)

# ... (diğer importlar ve ayarlar aynı kalır)


# === GÜNCELLENEN TEK FİRMA TEST FORMU ===
import openai, inspect

st.subheader("🔍 Tek Firma Hızlı Test")
with st.form("single_company_test"):
    c1, c2, c3 = st.columns([3,2,3])
    with c1:
        single_name = st.text_input("Firma adı", placeholder="Örn: Daco France")
    with c2:
        single_country = st.selectbox(
            "Ülke/Lokal (ara dili)",
            allowed,
            index=allowed.index(st.session_state.get('country_default', 'EN'))
        )
    with c3:
        single_website = st.text_input("Web sitesi (opsiyonel)", placeholder="https://example.com")

    single_sector = st.text_input("Sektör (opsiyonel)", placeholder="Gıda, Kozmetik, vb.")
    run_single = st.form_submit_button("Çalıştır (tek firma)")

if run_single:
    if not single_name.strip():
        st.warning("Firma adını gir.")
    else:
        with st.spinner("Araştırılıyor…"):
            try:
                report, score = call_with_cache(single_name, single_country, single_website, single_sector)
                st.session_state['single_report']  = report
                st.session_state['single_score']   = score
                st.session_state['single_name']    = single_name
                st.session_state['single_country'] = single_country
                st.session_state['single_website'] = single_website
                st.session_state['single_sector']  = single_sector
            except Exception as e:
                st.session_state['single_report']  = f"Hata: {e}"
                st.session_state['single_score']   = None
                st.session_state['single_name']    = single_name
                st.session_state['single_country'] = single_country
                st.session_state['single_website'] = single_website
                st.session_state['single_sector']  = single_sector

# Sonucu göster + indirme seçenekleri
if st.session_state.get('single_report'):
    nm = st.session_state.get('single_name', 'Firma')
    cc = st.session_state.get('single_country', 'EN')
    sc = st.session_state.get('single_score', None)
    wb = st.session_state.get('single_website', '')

    st.markdown("**Skor:**")
    st.metric(label=f"{nm} · {cc}", value=f"{sc if sc is not None else '—'}/10")

    if wb:
        st.caption(f"Web sitesi: {wb}")

    st.text_area("Rapor (7 blok)", st.session_state['single_report'], height=420)

    # TXT indirme
    st.download_button(
        label="📄 TXT indir (tek firma)",
        data=st.session_state['single_report'].encode("utf-8"),
        file_name=f"{nm.replace(' ','_')}_report.txt",
        mime="text/plain",
        key="single_txt_dl",
    )

    # Excel indirme (tek satır)
    single_df = pd.DataFrame([{
        "Country": cc,
        "Company": nm,
        "Website": wb,
        "report": st.session_state['single_report'],
        "score": sc
    }])
    df_json_single = single_df.to_json(orient="split")
    xlsx_bytes_single = df_to_xlsx_bytes(df_json_single)
    st.download_button(
        label="📥 Excel indir (tek firma)",
        data=xlsx_bytes_single,
        file_name=f"{nm.replace(' ','_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="single_xlsx_dl",
    )

# --- Gerisi değişmedi ---

# --- Gerisi değişmedi ---
# ===================== UI =====================
st.set_page_config(page_title="B2B Research", initial_sidebar_state="collapsed")
st.title("📂 CSV Dosyası Yükleme")

uploaded_file = st.file_uploader("CSV dosyanızı yükleyin", type=["csv"])
if uploaded_file is None and AUTO_CSV.exists():
    uploaded_file = AUTO_CSV


if uploaded_file is not None:
    try:
        if isinstance(uploaded_file, Path):
            with open(uploaded_file, "rb") as f:
                content = f.read()
        else:
            content = uploaded_file.read()

        df = pd.read_csv(io.BytesIO(content))

        df = pd.read_csv(io.BytesIO(content))
        st.success(f"✅ Yüklenen dosya: {uploaded_file.name}")
        st.dataframe(df)
    except Exception as e:
        st.error(f"❌ CSV okunurken hata: {e}")
        st.stop()

# Eğer autosave varsa ve kullanıcı 'Devam Et' dedi ise
elif st.session_state.get("resume_now", False):
    df = st.session_state.get("cold_call", None)

# Hâlâ df yoksa
    if df is None:
        st.warning("Veri yüklenemedi. Lütfen CSV dosyası yükleyin veya autosave ile devam edin.")
        st.stop()
        st.success(f"✅ Yüklenen dosya: {uploaded_file.name}")
        st.dataframe(df)

    # Ülke/lokal seçimi (genel varsayılan)
  # Ülke/lokal ve sektör seçimi (genel varsayılan)
colA, colB = st.columns([1, 1])

with colA:
    country_box = st.selectbox("Ülke/Lokal (ara dili)", allowed, index=allowed.index(st.session_state['country_default']))

with colB:
    raw_country = st.text_input("Ülke kodu (opsiyonel, örn: FR/DE/UK/ES/IT/TR/EN)", value="")


default_sector = st.session_state.get("sector_default", "")
sector_input = st.text_input("Sektör (opsiyonel)", value=default_sector, placeholder="Gıda, Kozmetik, vb.")

# Ülke kodunu normalize et
country_code = normalize_country_code(raw_country) or country_box
if raw_country and not normalize_country_code(raw_country):
    st.warning(f"Geçersiz ülke kodu: {raw_country}. {country_box} kullanılacak.")

# Session state güncelle
st.session_state["country_default"] = country_code
st.session_state["sector_default"] = sector_input


    # === AUTOSAVE VARSA DEVAM ET / TEMİZLE ===
resume_now = False
if AUTO_CSV.exists():
        c1, c2 = st.columns(2)
        with c1:
                if st.button("▶ Devam Et (autosave)", key="resume_btn"):
                    try:
                        df_saved = pd.read_csv(AUTO_CSV)
                        df_main = st.session_state.get("cold_call")  # None olabilir

                        if df_main is None:
                            # 🔑 Ana df yoksa direkt autosave'den devam et
                            df_merged = df_saved.copy()
                            last_idx = int(
                                df_merged.get("report", pd.Series([""]*len(df_merged)))
                                .astype(str).str.strip().str.len().gt(0).sum()
                            )
                        else:
                            # Ana df varsa merge et
                            df_merged, last_idx = _merge_autosave_into_df(df_main, df_saved)

                        st.session_state['cold_call']       = df_merged
                        st.session_state['progress_i']      = last_idx   # 🔑 kaldığın yer
                        st.session_state['last_processed_index'] = last_idx
                        st.session_state['resume_now']      = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Autosave okunamadı: {e}")

            # --- İşlem başlatıcı (KOLON BLOĞU DIŞINDA!) ---
        run_now = st.session_state.get("resume_now", False)

        if run_now:
                st.session_state["resume_now"] = False  # bir kere çalışsın

                if "cold_call" not in st.session_state or st.session_state["cold_call"] is None:
                    st.warning("Çalıştırmak için veri seti (cold_call) yüklenmemiş.")
                else:
                    df = st.session_state["cold_call"]
                    # burada senin işleme döngün başlasın (start_i = st.session_state['progress_i'] ile)


        with c2:
            if st.button("🗑 Autosave temizle"):
                try:
                    AUTO_CSV.unlink(missing_ok=True)
                    AUTO_XLSX.unlink(missing_ok=True)
                    st.session_state['progress_i'] = 0
                    st.info("Autosave temizlendi.")
                except Exception as e:
                    st.warning(f"Autosave silinemedi: {e}")

    # ==== İşlem Başlat / Devam Et ====
run_now = st.button("Cold Call Dönüşümü") or st.session_state.get("resume_now", False)


if run_now:
  # ✅ Devam eden kodun düzgün girintide olması gerekiyor
        if "report" not in df.columns:
            df["report"] = ""
        if "score" not in df.columns:
            df["score"] = pd.NA
        companies = df["Company"].fillna("").astype(str)
        total = len(companies)

        # Kaldığın yer: autosave'den geldiyse state'te, yoksa mevcut rapor doluluğuna göre hesapla
        start_i = int(st.session_state.get("progress_i", 0))
        if start_i == 0:
            start_i = int(df["report"].astype(str).str.strip().str.len().gt(0).sum())
        st.session_state["progress_i"] = start_i

        base_cols = ["Country","Company","Website","Company Phone",
                     "First Name","Last Name","Title","Departments",
                     "Corporate Phone","Person Linkedin Url","Email"]

        header_ph = st.empty()
        row_msg_ph = st.empty()

        unprocessed = df["report"].astype(str).str.strip().eq("")



        AUTOSAVE_EVERY = 5

        # Hali hazırda işlenmiş satırları atla
        # İşlenmemiş satırları filtrele (raporu boş olanlar)
        unprocessed = df["report"].astype(str).str.strip().eq("")

        total = unprocessed.sum()  # toplam işlenecek satır sayısı
        done = 0  # kaç satır işlendi

                # Sadece işlenmemiş satırlarla döngüye gir
        row_msg_ph = st.empty()  # dışarıda tanımlı olsun

        for i, idx in enumerate(df[unprocessed].index, start=1):
            company_name = df.at[idx, "Company"]
            

            if not company_name.strip():
                df.at[idx, "report"] = "Şirket adı boş"
                df.at[idx, "score"] = None
            else:
                row_country = resolve_row_country(df, idx, st.session_state.get("country_default", "EN"))
                row_sector = st.session_state.get("sector_default", "")
                row_website = df.at[idx, "Website"] if "Website" in df.columns else None

                # 🔁 GÜNCELLENEN SATIR:
                row_msg_ph.write(f"🔎 {i}/{total} - {company_name} ({row_country}) işleniyor…")

                try:
                    report, score = call_with_cache(company_name, row_country, website=row_website, sector=row_sector)
                except Exception as e:
                    report, score = f"Hata: {e}", None

                df.at[idx, "report"] = report
                df.at[idx, "score"] = int(score) if score is not None else None
                st.session_state["progress_i"] += 1
                if st.session_state["progress_i"] % AUTOSAVE_EVERY == 0 or i == total:
                    try:
                        st.session_state["cold_call"] = safe_subset(df, base_cols + ["report", "score"])
                        st.session_state["cold_call"].to_csv(AUTO_CSV, index=False, encoding="utf-8")
                        with pd.ExcelWriter(AUTO_XLSX, engine="xlsxwriter") as w:
                            st.session_state["cold_call"].to_excel(w, index=False, sheet_name="Emails")
                        st.toast("💾 Autosave kaydedildi.")
                    except Exception as e:
                        st.warning(f"Autosave hatası: {e}")




        # İlerleme göstergesi
        done = df["report"].astype(str).str.strip().ne("").sum()
        prog = st.progress(0.0)
        prog.progress(done / len(df), text=f"{done}/{len(df)} tamamlandı")
        st.toast(f"{company_name} ✓")

        # Ara kayıt (autosave)
        st.session_state["cold_call"] = safe_subset(df, base_cols + ["report", "score"])
        if done % AUTOSAVE_EVERY == 0 or done == len(df):
            try:
                st.session_state["cold_call"].to_csv(AUTO_CSV, index=False, encoding="utf-8")
                with pd.ExcelWriter(AUTO_XLSX, engine="xlsxwriter") as w:
                    st.session_state["cold_call"].to_excel(w, index=False, sheet_name="Emails")
                st.toast("💾 Autosave")
            except Exception:
                pass

        st.success("✅ Tamamlandı.")

# ===================== Görüntüleme & İndirme (UPLOAD BLOĞU DIŞINDA) =====================
if st.session_state.get('cold_call') is not None:
    st.dataframe(st.session_state['cold_call'])

    # Excel indirme
    df_json = st.session_state['cold_call'].to_json(orient="split")
    xlsx_bytes = df_to_xlsx_bytes(df_json)
    st.download_button(
        label="📥 Excel olarak indir",
        data=xlsx_bytes,
        file_name=f"kontakt_listesi_{datetime.datetime.now():%Y%m%d_%H%M}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_xlsx",
    )
