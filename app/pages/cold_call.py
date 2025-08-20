# streamlit_app.py  (veya sayfanızın .py dosyası)

import os, io, datetime, tempfile
from pathlib import Path
from typing import List
import pandas as pd
import streamlit as st

# --- OpenAI tarafını kullanan kendi fonksiyonun ---
# (Aynen senin yazdığın/eklediğin modul)
from app.gpt import cold_call_cevir

# ===================== Session State INIT =====================
if 'cold_call' not in st.session_state:
    st.session_state['cold_call'] = None
if 'running' not in st.session_state:
    st.session_state['running'] = False
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

    # Autosave var mı? Devam / Temizle
    if AUTO_CSV.exists():
        c1, c2 = st.columns(2)
        with c1:
            if st.button("▶ Devam et (autosave)"):
                try:
                    df_saved = pd.read_csv(AUTO_CSV)
                    st.session_state['cold_call'] = df_saved
                    st.session_state['progress_i'] = len(df_saved)
                    st.success("Autosave yüklendi. Aşağıda görüntüleme/indirme aktif.")
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

    # Çalıştırma butonu
    if st.button("Mail Dönüşümü Başlat"):
        if "Company" not in df.columns:
            st.error("CSV'de 'Company' kolonu yok.")
            st.stop()

        # Çıktı kolonları
        if 'report' not in df.columns: df['report'] = ""
        if 'score'  not in df.columns: df['score']  = pd.NA

        companies = df["Company"].fillna("").astype(str)
        total = len(companies)

        st.session_state['running'] = True
        start_i = st.session_state.get('progress_i', 0)  # kaldığın yerden
        base_cols = ["Country","Company","Website","Company Phone",
                     "First Name","Last Name","Title","Departments",
                     "Corporate Phone","Person Linkedin Url","Email"]

        header_ph = st.empty()
        row_msg_ph = st.empty()
        prog = st.progress(0.0, text=f"{start_i}/{total} başlıyor…")
        header_ph.info(f"Toplam {total} şirket işlenecek. Başlangıç: {start_i}")

        AUTOSAVE_EVERY = 5  # her 5 satırda ara-kayıt

        try:
            for i, (idx, company_name) in enumerate(companies.items(), start=1):
                if i <= start_i:
                    continue  # daha önce işlenenleri atla

                if not company_name.strip():
                    df.at[idx, 'report'] = "Şirket adı boş"
                    df.at[idx, 'score'] = None
                else:
                    # Satıra özel ülke kodu
                    row_country = resolve_row_country(df, idx, st.session_state.get("country_default","EN"))
                    row_msg_ph.write(f"🔎 {i}/{total} — **{company_name}** ({row_country}) işleniyor…")
                    try:
                        # Cache'li çağrı (aynı firma+ülke tekrarlanırsa)
                        report, score = call_with_cache(company_name, row_country)
                    except Exception as e:
                        report, score = f"Hata: {e}", None

                    df.at[idx, 'report'] = report
                    df.at[idx, 'score']  = score

                # İlerleme & durum
                st.session_state['progress_i'] = i
                prog.progress(i/total, text=f"{i}/{total} tamamlandı")
                st.toast(f"{company_name} ✓")

                # Ara-kayıt (session + disk)
                st.session_state['cold_call'] = safe_subset(df, base_cols + ["report","score"])
                if i % AUTOSAVE_EVERY == 0 or i == total:
                    try:
                        st.session_state['cold_call'].to_csv(AUTO_CSV, index=False, encoding="utf-8")
                        with pd.ExcelWriter(AUTO_XLSX, engine="xlsxwriter") as w:
                            st.session_state['cold_call'].to_excel(w, index=False, sheet_name="Emails")
                        st.toast("💾 Autosave")
                    except Exception:
                        pass

            st.success("✅ Tamamlandı.")
        finally:
            st.session_state['running'] = False

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
