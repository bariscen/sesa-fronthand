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

def call_with_cache(name: str, country: str):
    key = (name.strip().lower(), country)
    if key in st.session_state['cc_cache']:
        return st.session_state['cc_cache'][key]
    out = cold_call_cevir(name, country=country)
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


# ==== TEK FİRMA HIZLI TEST (token dostu) ====
st.subheader("🔍 Tek Firma Hızlı Test")
with st.form("single_company_test"):
    c1, c2 = st.columns([2,1])
    with c1:
        single_name = st.text_input("Firma adı", placeholder="Örn: Daco France")
    with c2:
        # allowed ve country_default yukarıda tanımlı (kodu zaten içeriyor)
        single_country = st.selectbox(
            "Ülke/Lokal (ara dili)",
            allowed,
            index=allowed.index(st.session_state.get('country_default', 'EN'))
        )
    run_single = st.form_submit_button("Çalıştır (tek firma)")

if run_single:
    if not single_name.strip():
        st.warning("Firma adını gir.")
    else:
        with st.spinner("Araştırılıyor…"):
            try:
                # mevcut cache'li çağrıyı kullanalım → aynı firma tekrarında token yemez
                report, score = call_with_cache(single_name, single_country)
                st.session_state['single_report'] = report
                st.session_state['single_score'] = score
                st.session_state['single_name'] = single_name
                st.session_state['single_country'] = single_country
            except Exception as e:
                st.session_state['single_report'] = f"Hata: {e}"
                st.session_state['single_score'] = None
                st.session_state['single_name'] = single_name
                st.session_state['single_country'] = single_country

# Sonucu göster + indirme seçenekleri
if st.session_state.get('single_report'):
    nm = st.session_state.get('single_name', 'Firma')
    cc = st.session_state.get('single_country', 'EN')
    sc = st.session_state.get('single_score', None)

    st.markdown("**Skor:**")
    st.metric(label=f"{nm} · {cc}", value=f"{sc if sc is not None else '—'}/10")

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

# ==== (ALTTAKİ CSV BÖLÜMÜNÜZ AYNEN DEVAM EDER) ====


# ===================== UI =====================
st.set_page_config(page_title="B2B Research", initial_sidebar_state="collapsed")
st.title("📂 CSV Dosyası Yükleme")

uploaded_file = st.file_uploader("CSV dosyanızı yükleyin", type=["csv"])

if uploaded_file is not None:
    # CSV oku + önizleme
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"❌ CSV okunurken hata: {e}")
        st.stop()

    st.success(f"✅ Yüklenen dosya: {uploaded_file.name}")
    st.dataframe(df)

    # Ülke/lokal seçimi (genel varsayılan)
    colA, colB = st.columns([1,1])
    with colA:
        country_box = st.selectbox("Ülke/Lokal (ara dili)", allowed, index=allowed.index(st.session_state['country_default']))
    with colB:
        raw_country = st.text_input("Ülke kodu (opsiyonel, örn: FR/DE/UK/ES/IT/TR/EN)", value="")
    country_code = normalize_country_code(raw_country) or country_box
    if raw_country and not normalize_country_code(raw_country):
        st.warning(f"Geçersiz ülke kodu: {raw_country}. {country_box} kullanılacak.")
    st.session_state["country_default"] = country_code

    # === AUTOSAVE VARSA DEVAM ET / TEMİZLE ===
    resume_now = False
    if AUTO_CSV.exists():
        c1, c2 = st.columns(2)
        with c1:
            if st.button("▶ Devam Et (autosave)"):
                try:
                    df_saved = pd.read_csv(AUTO_CSV)
                    df, start_i = _merge_autosave_into_df(df, df_saved)
                    st.session_state['cold_call'] = df
                    st.session_state['progress_i'] = start_i
                    st.success(f"Autosave yüklendi. Başlangıç: {start_i}.")
                    resume_now = True
                except Exception as e:
                    st.error(f"Autosave okunamadı: {e}")
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
    run_now = st.button("Mail Dönüşümü Başlat") or resume_now

    if run_now:
        if "Company" not in df.columns:
            st.error("CSV'de 'Company' kolonu yok.")
            st.stop()

        # Çıktı kolonları
        if "report" not in df.columns: df["report"] = ""
        if "score"  not in df.columns: df["score"]  = pd.NA

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
        prog = st.progress(0.0, text=f"{start_i}/{total} başlıyor…")
        header_ph.info(f"Toplam {total} şirket işlenecek. Başlangıç: {start_i}")

        AUTOSAVE_EVERY = 5

        # Hali hazırda işlenmiş satırları atla
        already = df["report"].astype(str).str.strip().str.len().gt(0)

        try:
            for i, (idx, company_name) in enumerate(companies.items(), start=1):
                if already.loc[idx]:
                    if i % 50 == 0:
                        prog.progress(i/total, text=f"{i}/{total} (işlenmişleri atlıyorum)")
                    continue

                if not company_name.strip():
                    df.at[idx, "report"] = "Şirket adı boş"
                    df.at[idx, "score"]  = None
                else:
                    # satıra özel ülke kodu
                    row_country = resolve_row_country(df, idx, st.session_state.get("country_default","EN"))
                    row_msg_ph.write(f"🔎 {i}/{total} — **{company_name}** ({row_country}) işleniyor…")
                    try:
                        report, score = call_with_cache(company_name, row_country)
                    except Exception as e:
                        report, score = f"Hata: {e}", None

                    df.at[idx, "report"] = report
                    df.at[idx, "score"]  = score

                # ilerleme
                st.session_state["progress_i"] += 1
                prog.progress(st.session_state["progress_i"]/total,
                              text=f"{st.session_state['progress_i']}/{total} tamamlandı")
                st.toast(f"{company_name} ✓")

                # ara-kayıt: session + disk
                st.session_state["cold_call"] = safe_subset(df, base_cols + ["report","score"])
                if (st.session_state["progress_i"] % AUTOSAVE_EVERY == 0) or (st.session_state["progress_i"] == total):
                    try:
                        st.session_state["cold_call"].to_csv(AUTO_CSV, index=False, encoding="utf-8")
                        with pd.ExcelWriter(AUTO_XLSX, engine="xlsxwriter") as w:
                            st.session_state["cold_call"].to_excel(w, index=False, sheet_name="Emails")
                        st.toast("💾 Autosave")
                    except Exception:
                        pass

            st.success("✅ Tamamlandı.")
        finally:
            pass

# ===================== Görüntüleme & İndirme (UPLOAD BLOĞU DIŞINDA) =====================
if st.session_state.get('cold_call') is not None:
    st.dataframe(st.session_state['cold_call'])

if st.session_state.get('cold_call') is not None:
    df_json = st.session_state['cold_call'].to_json(orient="split")
    xlsx_bytes = df_to_xlsx_bytes(df_json)
    st.download_button(
        label="📥 Excel olarak indir",
        data=xlsx_bytes,
        file_name=f"kontakt_listesi_{datetime.datetime.now():%Y%m%d_%H%M}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_xlsx",
    )
