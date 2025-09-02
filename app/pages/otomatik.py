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
from app.function import read_gcs_blob_content, saving_gcs
from app.gpt import get_observation, extract_sector, rag, referans, generate_better_email, create_personalized_email
import tempfile
import smtplib
from email.mime.text import MIMEText
import streamlit as st
from datetime import datetime, timedelta


def send_email_function(to_email, subject, content):
    """
    Belirtilen e-posta adresine mail gönderir.

    Args:
        to_email (str): Alıcının e-posta adresi.
        subject (str): E-postanın konusu.
        content (str): E-postanın içeriği (HTML formatında).

    Returns:
        bool: E-posta başarıyla gönderildiyse True, aksi halde False.
    """
    # secrets.toml dosyasından e-posta bilgilerinizi alın
    try:
        from_email = st.secrets["EMAIL_USER"]
        from_password = st.secrets["EMAIL_PASSWORD"]
    except KeyError as e:
        st.error(f"secrets.toml dosyasında {e} anahtarı bulunamadı. Lütfen kontrol edin.")
        return False

    msg = MIMEText(content, "html") # HTML içeriği kullan
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(from_email, from_password)
            smtp.send_message(msg)
        st.success(f"✅ Mail başarıyla {to_email} adresine gönderildi.")
        return True
    except Exception as e:
        st.error(f"❌ {to_email} adresine mail gönderilirken hata oluştu: {e}")
        return False



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



df = read_gcs_blob_content("mail")

# GCS'ten veriyi oku
st.subheader("✉️ Geri Dönüşleri İşaretle")

# 'read_gcs_blob_content' fonksiyonunuzu kullanarak DataFrame'i GCS'ten yükleyin
try:
    gcs_df = read_gcs_blob_content('mail')
    #gcs_df = gcs_df['Company', ]
    if gcs_df is None:
        st.warning("GCS'te 'gonderilen_mailler.pkl' dosyası bulunamadı.")
        gcs_df = pd.DataFrame() # Boş bir DataFrame oluştur
except Exception as e:
    st.error(f"GCS dosyası yüklenirken hata oluştu: {e}")
    gcs_df = pd.DataFrame()

# DataFrame'de 'Geri Dönüş' sütunu yoksa ekleyin
if 'Geri Dönüş' not in gcs_df.columns:
    gcs_df['Geri Dönüş'] = False
if 'Cevaplandı' not in gcs_df.columns:
    gcs_df['Cevaplandı'] = False # Alternatif bir sütun adı

# --- BURAYA YENİ KOD EKLENECEK ---
# Arama çubuğunu ve filtreleme mantığını burada uygulayın
st.write("Aşağıdaki tabloda geri dönüş yapan kişileri işaretleyebilirsiniz:")

# Arama çubuğu
search_query = st.text_input("Firma Adı veya E-posta adresine göre ara", "")

# Arama sorgusuna göre DataFrame'i filtrele
if search_query:
    filtered_df = gcs_df[
        gcs_df['Company'].str.contains(search_query, case=False, na=False) |
        gcs_df['Email'].str.contains(search_query, case=False, na=False)
    ]
else:
    filtered_df = gcs_df
# --- YENİ KOD BURADA SONA ERIYOR ---

# Filtrelenmiş DataFrame'i kullanıcıya göster
edited_df = st.data_editor(
    filtered_df,
    num_rows="dynamic",
    column_config={
        "Geri Dönüş": st.column_config.CheckboxColumn(
            "Geri Dönüş Yaptı",
            help="Bu kişiden geri dönüş alındıysa işaretleyin.",
            default=False,
        ),
        "Cevaplandı": st.column_config.CheckboxColumn(
            "Cevaplandı",
            help="Bu kişiden geri dönüş alındıysa işaretleyin.",
            default=False,
        )
    },
    hide_index=True,
    key="veri_editoru"
)


# DataFrame'i kullanıcı tarafından düzenlenebilir hale getirin
# st.write("Aşağıdaki tabloda geri dönüş yapan kişileri işaretleyebilirsiniz:")
# edited_df = st.data_editor(
#     gcs_df,
#     num_rows="dynamic",
#     column_config={
#         "Geri Dönüş": st.column_config.CheckboxColumn(
#             "Geri Dönüş Yaptı",
#             help="Bu kişiden geri dönüş alındıysa işaretleyin.",
#             default=False,
#         ),
#         "Cevaplandı": st.column_config.CheckboxColumn(
#             "Cevaplandı",
#             help="Bu kişiden geri dönüş alındıysa işaretleyin.",
#             default=False,
#         )
#     },
#     hide_index=True,
#     key="veri_editoru"

# )

# Değişiklikleri kaydetmek için buton
if st.button("Değişiklikleri Kaydet"):
    with st.spinner("Değişiklikler GCS'e kaydediliyor..."):

        # Sadece işaretlenen satırları seçmek için bir örnek
        isaretlenenler = edited_df[edited_df["Geri Dönüş"] == True]

        # Tüm DataFrame'i tekrar kaydetmek için
        # edited_df, tüm düzenlemeleri içerir.

        try:
            # Geçici bir pickle dosyası oluştur
            temp_pickle_path = Path(tempfile.gettempdir()) / st.secrets.get('mail')
            edited_df.to_pickle(temp_pickle_path)

            # Güncellenmiş DataFrame'i GCS'e yükle
            saving_gcs(temp_pickle_path)

            st.success("✅ Veri başarıyla güncellendi ve GCS'e kaydedildi!")
            st.rerun() # Sayfayı yenileyerek güncel veriyi göster

        except Exception as e:
            st.error(f"Veri GCS'e kaydedilirken hata oluştu: {e}")

# Not: Geri Dönüş yapanlara 2. mail atılmasını engellemek için,
# mail atma fonksiyonunuzda 'Geri Dönüş' sütunu False olanları filtreleyebilirsiniz.
# Örn: islenecek_df = gcs_df[gcs_df['Geri Dönüş'] == False]



st.title("✉️ Toplu Mail Gönderimi")
if st.button("Seçilenlere Mail Gönder"):
    with st.spinner("Mailler hazırlanıyor ve gönderiliyor..."):

         # Sadece 'Geri Dönüş' yapmamış VE 'Email Atıldı' sütunu False olanları seç

        uc_gun_once = datetime.now() - timedelta(days=3)

        geri_donus_yapmayanlar_df = edited_df[
            (edited_df['Geri Dönüş'] == False) & (edited_df['Email Atıldı'] != True) & (pd.to_datetime(edited_df['Yükleme Tarihi']) < uc_gun_once)
        ]

        if geri_donus_yapmayanlar_df.empty:
            st.info("Geri dönüş yapmayan kişi bulunamadı. İşlem durduruldu.")
        else:
            prog = st.progress(0.0)
            status_ph = st.empty()
            total_mails = len(geri_donus_yapmayanlar_df)

            # DataFrame'in bir kopyasını alarak üzerinde işlem yapalım
            updated_df = edited_df.copy()

            for i, (index, row) in enumerate(geri_donus_yapmayanlar_df.iterrows()):
                company = row.get("Company", "Bilinmiyor")
                email_address = row.get("Email", None)
                mail_icerik = f'Dear {row.get("First Name", "")}, <br><br>Did you able to reach my email? Looking forward to our collabration. Thanks for your time'

                status_ph.write(f"Mailler hazırlanıyor: {i+1}/{total_mails} - {company}")

                if email_address and mail_icerik:
                    # Mail gönderme fonksiyonunu çağır
                    mail_sent = send_email_function(
                        to_email=email_address,
                        subject=f"Flexible Packaging Offer for {company}",
                        content=mail_icerik
                    )

                    # Eğer mail başarıyla gönderildiyse DataFrame'i güncelle
                    if mail_sent:
                        updated_df.loc[index, "Email Atıldı"] = True

                else:
                    st.warning(f"'{company}' şirketi için e-posta adresi veya içerik bulunamadı.")

                prog.progress((i+1) / total_mails)

            # İşlem bittikten sonra güncellenmiş DataFrame'i GCS'e yükle
            st.write("Değişiklikler GCS'e kaydediliyor...")
            temp_pickle_path = Path(tempfile.gettempdir()) / "gonderilen_mailler.pkl"

            updated_df.to_pickle(temp_pickle_path)
            saving_gcs(temp_pickle_path)

            st.success("✅ Tüm işlemler tamamlandı ve veri güncellendi!")
            st.balloons()
