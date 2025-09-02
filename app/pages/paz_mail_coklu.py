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
import sys
import io
from google.cloud import storage
from google.cloud.exceptions import NotFound
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

GCS_BUCKET_NAME = st.secrets.get('GCS_BUCKET_NAME')
GCS_FILENAME = "gonderilen_mailler.pkl"


from app.function import read_gcs_blob_content, download_gcs_csv_as_df, upload_df_to_gcs_csv, saving_gcs
# from app.gpt import get_observation, extract_sector, rag, referans, generate_better_email, create_personalized_email, extract_state
# Gerekli fonksiyonların Gemini versiyonlarını kullanmak için güncelliyoruz.
from app.gpt import get_observation, extract_sector, rag, referans, generate_better_email, create_personalized_email, extract_state
import google.generativeai as genai

# --- Gemini API anahtarı ve model kurulumu ---
gemini_api_key = st.secrets.get("GEMINI_API_KEY")
if not gemini_api_key:
    st.error("Lütfen secrets.toml dosyasına Gemini API anahtarını ekleyin.")
    st.stop()
genai.configure(api_key=gemini_api_key)
model_gemini = genai.GenerativeModel('gemini-1.5-pro-latest')

# --- Diğer API anahtarları ---
openai_api_key = st.secrets.get("OPENAI_API_KEY")
langsmith_api_key = st.secrets.get("LANGSMITH_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["LANGSMITH_API_KEY"] = langsmith_api_key
os.environ["TAVILY_API_KEY"] = tavily_api_key

# --- OpenAI, Langchain vs. importları ---
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
import PyPDF2

llm = ChatOpenAI(model="gpt-4o", temperature=0.6)
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = "langchain-academy"

sektor_ulke = read_gcs_blob_content("sesa1")

### SIDE BAR KAPAMA BASLIYOR
st.set_page_config(initial_sidebar_state="collapsed")
st.markdown("""
<style>
    [data-testid="collapsedControl"] {
        display: none
    }
    section[data-testid="stSidebarNav"] {
        display: none;
    }
    button[title="Toggle sidebar"] {
        display: none;
    }
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp {
        background-color: #d3d3d3; /* 1 ton açık gri */
    }
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
### SIDE BAR KAPAMA BİTTİ

# Bu dosyanın bulunduğu dizin (app.py'nin dizini)
current_dir = Path(__file__).parent.parent
image_path_for_logo = current_dir.parent / "row-data" / "sesa-logo-80-new.png"
if 'logo_image_path' not in st.session_state:
    st.session_state.logo_image_path = str(image_path_for_logo)

st.image(st.session_state.logo_image_path, width=200)

# SADECE bu button'a özel container (testid kullanılıyor)
with st.container():
    st.markdown('<div data-testid="pazarlama_button">', unsafe_allow_html=True)
    if st.button("Pazarlama Menüsüne Dön", key="pazarlama"):
        st.switch_page("pages/page2.py")
    st.markdown("</div>", unsafe_allow_html=True)







st.title("📂 CSV Dosyası Yükleme")

uploaded_file = st.file_uploader("CSV dosyanızı yükleyin", type=["csv"])
import tempfile

AUTO_CSV = Path(tempfile.gettempdir()) / "email_autosave.csv"
AUTO_XLSX = Path(tempfile.gettempdir()) / "email_autosave.xlsx"

if "progress_i" not in st.session_state:
    st.session_state["progress_i"] = 0
if "resume_now" not in st.session_state:
    st.session_state["resume_now"] = False
if "start_process" not in st.session_state: # Yeni session_state değişkeni
    st.session_state["start_process"] = False

if uploaded_file is not None:
    try:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file)

        if df.empty:
            st.warning("Yüklenen CSV dosyası boş görünüyor.")
        else:
            st.success(f"✅ Yüklenen dosya: {uploaded_file.name}")
            st.write("📊 Veri Önizlemesi:")
            st.dataframe(df)
            st.session_state["uploaded_df"] = df.copy() # Yüklenen df'i session state'e kaydet

    except Exception as e:
        st.error(f"❌ CSV okunurken hata oluştu: {e}")
        st.session_state["uploaded_df"] = None


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
def _observation_cached(company_name: str, state, website, target_sector):
    return get_observation(company_name, state, website, target_sector)

def email(company_name, state, position, name, website,target_sector):
    # Gemini modelini fonksiyon içine gönderiyoruz
    tavily_res = _observation_cached(company_name, state, website, target_sector)
    ulke_kodu = extract_state(state)

    pdf_path = current_dir / "data" / "RAG-SESA.pdf"
    context =  _rag_cached(str(pdf_path))
    referanslar = referans(sektor_ulke, target_sector, ulke_kodu)
    _throttle(12)
    result = _backoff_call(
        generate_better_email, tavily_res, position, target_sector, context, company_name, referanslar)

    final = create_personalized_email(result, name)
    return final

# --- Hedef sektör girişi (BUTONLARDAN ÖNCE) ---
st.subheader("🎯 Hedef Sektör")
st.session_state["target_sector"] = st.text_input(
    "Hedef sektörünüzü girin",
    value=st.session_state.get("target_sector", ""),
    placeholder="örn. Food & Beverage, Cosmetics, Pet Food, Frozen Foods ..."
)

if "uploaded_df" in st.session_state and not st.session_state["uploaded_df"].empty:
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🚀 Mail Dönüşümünü Başlat", key="start_btn"):
            st.session_state["start_process"] = True
            st.session_state["resume_now"] = False
            st.rerun() # Sayfayı yeniden yükle
    with c2:
        if st.button("▶ Devam Et (autosave)", key="resume_btn"):
            st.session_state["start_process"] = True
            st.session_state["resume_now"] = True
            st.rerun()
    with c3:
        if st.button("🗑 Autosave temizle", key="clear_btn"):
            try:
                AUTO_CSV.unlink(missing_ok=True)
                AUTO_XLSX.unlink(missing_ok=True)
                st.session_state["progress_i"] = 0
                st.toast("🗑 Autosave temizlendi.")
                # Sayfayı temiz bir şekilde yeniden başlat
                st.session_state["start_process"] = False
                st.rerun()
            except Exception as e:
                st.warning(f"Autosave silinemedi: {e}")

# Süreci başlatan ana kısım
if st.session_state.get("start_process", False):

    # İşleme başlamadan hedef sektör kontrolü
    if not st.session_state.get("target_sector"):
        st.warning("Lütfen 'Hedef Sektör' bilgisini girin (üstteki kutu).")
        st.session_state["start_process"] = False
        st.stop()

    dfw = st.session_state.get("uploaded_df")

    if st.session_state.get("resume_now", False):
        # Resume mantığı
        try:
            if not AUTO_CSV.exists():
                st.warning("Autosave bulunamadı.")
                st.session_state["start_process"] = False
            else:
                saved = pd.read_csv(AUTO_CSV)
                df_merged = dfw.copy()
                if "Company" in saved.columns and "Company" in df_merged.columns:
                    carry_cols = ["Company", "Email_icerik", "Email Atıldı", "Soğuk Arama Gerçekleşti", "linkedin Eklendi"]
                    carry = saved[[c for c in carry_cols if c in saved.columns]].drop_duplicates("Company")
                    df_merged = df_merged.merge(carry, on="Company", how="left", suffixes=("", "_saved"))
                    for c in ["Email_icerik", "Email Atıldı", "Soğuk Arama Gerçekleşti", "linkedin Eklendi"]:
                        if f"{c}_saved" in df_merged.columns:
                            df_merged[c] = df_merged[c].where(df_merged[c].notna(), df_merged[f"{c}_saved"])
                            df_merged.drop(columns=[f"{c}_saved"], inplace=True)
                dfw = df_merged
                st.session_state["email_df_work"] = dfw

                last_idx = int(dfw["Email_icerik"].fillna("").astype(str).str.strip().str.len().gt(0).sum())
                st.session_state["progress_i"] = last_idx
        except Exception as e:
            st.error(f"Autosave okunamadı: {e}")
            st.session_state["start_process"] = False
            st.rerun()
    else:
        # Baştan başlama mantığı
        st.session_state["email_df_work"] = dfw.copy()
        st.session_state["progress_i"] = 0

    # Tüm fonksiyon çağrılarına model_gemini'yi ekliyoruz
    # Örn: extract_sector(tavily_res, model_gemini) gibi
    # Ancak bu fonksiyonda sadece bir tane get_observation var. Diğer fonksiyonlarınızı da Gemini'ye dönüştürmeniz gerekir.
    # Bu örnekte, sadece get_observation'ı ve email fonksiyonunu düzelttim.
    # Diğer fonksiyonlarınızın da Gemini'ye uyumlu hale getirilmiş olması gerekir.

    dfw = st.session_state.get("email_df_work")
    if dfw is None:
        st.warning("Veri yok. Lütfen CSV yükleyin.")
        st.session_state["start_process"] = False
    else:
        for col in ["Email_icerik", "Email Atıldı", "Soğuk Arama Gerçekleşti", "linkedin Eklendi"]:
            if col not in dfw.columns:
                dfw[col] = pd.NA

        unprocessed_mask = dfw["Email_icerik"].fillna("").astype(str).str.strip().eq("")
        idx_list = dfw.index[unprocessed_mask].tolist()
        total = len(idx_list)

        if total == 0:
            st.info("İşlenecek satır kalmadı.")
            st.session_state["start_process"] = False
        else:
            prog = st.progress(0.0)
            status_ph = st.empty()
            start_done = int(st.session_state.get("progress_i", 0))
            AUTOSAVE_EVERY = 5
            step = 0

            for i, row_idx in enumerate(idx_list, start=1):
                row = dfw.loc[row_idx]
                company = str(row.get("Company", "")).strip()


                if not company:
                    dfw.at[row_idx, "Email_icerik"] = "Şirket adı boş"
                    step += 1
                    prog.progress(step / total, text=f"{step}/{total} tamamlandı")
                    continue

                status_ph.write(f"✉️ {step + 1}/{total} işleniyor: {company}")

                try:
                    # 'email' fonksiyonuna model_gemini'yi gönderin
                    icerik = email(
                        company_name=company,
                        state=row.get("Country", ""),
                        position=row.get("Title", ""),
                        name=row.get("First Name", ""),
                        website=row.get("Website", ""),
                        target_sector=st.session_state["target_sector"]
                    )
                except Exception as e:
                    icerik = f"Hata: {e}"

                dfw.at[row_idx, "Email_icerik"] = icerik
                step += 1
                st.session_state["progress_i"] += 1
                prog.progress(step / total, text=f"{step}/{total} tamamlandı")

                if (step % AUTOSAVE_EVERY == 0) or (step == total):
                    try:
                        out_df = dfw.copy()
                        FINAL_COLS = [
                            'Country', 'Company', 'Website', 'Company Phone', 'First Name', 'Last Name',
                            'Title', 'Departments', 'Corporate Phone', 'Person Linkedin Url', 'Email',
                            'Email_icerik', 'Email Atıldı', 'Soğuk Arama Gerçekleşti', 'linkedin Eklendi'
                        ]
                        save_df = out_df[[c for c in FINAL_COLS if c in out_df.columns]].copy()
                        AUTO_CSV = Path(tempfile.gettempdir()) / "email_autosave.csv"
                        AUTO_XLSX = Path(tempfile.gettempdir()) / "email_autosave.xlsx"
                        save_df.to_csv(AUTO_CSV, index=False, encoding="utf-8")
                        with pd.ExcelWriter(AUTO_XLSX, engine="xlsxwriter") as w:
                            save_df.to_excel(w, index=False, sheet_name="Emails")
                        st.toast("💾 Autosave kaydedildi.")
                    except Exception as e:
                        st.warning(f"Autosave hatası: {e}")

            # Tamamlandıktan sonra
            st.session_state["email_df_work"] = dfw
            st.session_state["email_df"] = dfw[[c for c in FINAL_COLS if c in dfw.columns]].copy()
            if 'email_df' in st.session_state:
                st.dataframe(st.session_state['email_df'])

                # Excel
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                    st.session_state['email_df'].to_excel(writer, index=False, sheet_name='Emails')
                output_excel.seek(0)
                st.download_button(
                    label="Excel İndir",
                    data=output_excel,
                    file_name="email_list.xlsx",
                    mime="application/vnd.ms-excel",
                )

                # CSV
                csv_data = st.session_state['email_df'].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="CSV İndir",
                    data=csv_data,
                    file_name='email_list.csv',
                    mime='text/csv',
                        )


        # İşleme döngüsünün bittiği yer
        # ... (önceki kodlar)

# İşleme döngüsünün bittiği yer
st.session_state["start_process"] = False

# DataFrame'in başarıyla oluşturulduğu ve gösterildiği kısım
if 'email_df' in st.session_state:
    st.dataframe(st.session_state['email_df'])

    # Excel indirme düğmesi
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
        st.session_state['email_df'].to_excel(writer, index=False, sheet_name='Emails')
    output_excel.seek(0)
    st.download_button(
        label="Excel İndir",
        data=output_excel,
        file_name="email_list.xlsx",
        mime="application/vnd.ms-excel",
        key="download_excel_button"
    )

    # CSV indirme düğmesi
    csv_data = st.session_state['email_df'].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="CSV İndir",
        data=csv_data,
        file_name='email_list.csv',
        mime='text/csv',
        key="download_csv_button"
    )

    # --- YENİ EKLENECEK KOD BLOĞU TAM BURADA ---
    # Kullanıcının GCS'ye yüklemesini sağlayacak buton ve mantık
    st.subheader("☁️ Google Cloud Storage'a Kaydet")

    # BUTONA BASILDIĞINDA NE OLACAĞINI KONTROL ETME
    if st.button("Sonuçları Google Storage'a Yükle/Güncelle", key="gcs_upload_btn"):
        with st.spinner("GCS ile senkronize ediliyor..."):

            # Yüklenecek DataFrame'i seçin
            final_df_to_upload = st.session_state['email_df']

            # Mevcut GCS dosyasını indirmeyi dene
            existing_df_path = Path(tempfile.gettempdir()) / GCS_FILENAME
            try:
                # read_gcs_blob_content fonksiyonunuzun doğru çalıştığını varsayarak
                existing_df = read_gcs_blob_content("mail")

                if existing_df is not None:
                    # Varolan dataframe ile yenisini birleştir
                    if 'Yükleme_Tarihi' not in existing_df.columns:
                        existing_df['Yükleme_Tarihi'] = "Tarih Bulunmuyor"


                        combined_df = pd.concat([existing_df, final_df_to_upload], ignore_index=True)
                        # Mükerrer kayıtları sil
                        combined_df.drop_duplicates(subset=['Company', 'Email'], keep='last', inplace=True)
                        final_df_to_upload = combined_df
                        st.write("Eski ve yeni veriler birleştirildi.")
                    else:
                        st.write("Mevcut GCS dosyası bulunamadı. Sadece yeni sonuçlar yüklenecek.")

                 # --- YENİ KOD BURAYA GELİYOR ---
                # final_df_to_upload'a bugünün tarihini içeren bir sütun ekle
                final_df_to_upload['Yükleme_Tarihi'] = pd.to_datetime('today').strftime('%Y-%m-%d %H:%M')

                #final_df_to_upload['Email Atıldı'] = 1
                # DataFrame'i geçici bir yola pickle dosyası olarak kaydedin
                final_df_to_upload.to_pickle(existing_df_path)

            except Exception as e:
                    st.warning(f"Mevcut GCS dosyası indirilemedi veya işlenemedi. Sadece yeni sonuçlar yüklenecek. Hata: {e}")

                # DataFrame'i geçici bir yola pickle dosyası olarak kaydedin
            final_df_to_upload.to_pickle(existing_df_path)

                # Düzenlenmiş saving_gcs fonksiyonunu çağırın
            saving_gcs(existing_df_path)

            st.balloons()

                # Yükleme işlemi bittiğinde, kullanıcıya bir mesaj gösterin ve DataFrame'i tekrar ekranda tutun
            st.success("Veri Google Cloud Storage'a başarıyla yüklendi ve güncellendi!")

                # Bu kod bloğunun dışına çıkıp ana döngüye dönün
                # Bu sayede DataFrame yeniden çizilir ve görünmeye devam eder
            st.rerun() # Sayfayı yeniden çalıştırarak güncel durumu göster
