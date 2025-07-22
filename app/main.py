import streamlit as st
import numpy as np
import pandas as pd
import os
from pathlib import Path


# Bu dosyanın bulunduğu dizin
current_dir = Path(__file__).parent

# row-data yolunu oluştur
image_path = current_dir.parent / "row-data" / "sesa-logo-80-new.png"

st.image(str(image_path), width=300)

st.markdown("""
    <style>
    .stApp {
        background-color: #d3d3d3; /* 1 ton açık gri */
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown(
    """
    <h2 style="color: #FFBF00;">
        <span style="background-color:#666666; padding: 5px 10px; border-radius: 5px;">
            SESA Ambalaj Yapay Zekaya Hoşgeldin
        </span>
    </h2>
    """,
    unsafe_allow_html=True
)

st.markdown("<div style='margin-bottom: 50px;'></div>", unsafe_allow_html=True) # Adds a 30px vertical space

# --- Özel Buton Stilleri ---
st.markdown("""
<style>
div.stButton > button:first-child {
    background-color:#FFBF00; /* Butonun arka plan rengi (Koyu Gri) */
    color: #555555;             /* Butonun yazı rengi */
    border-radius: 8px;       /* Köşeleri yuvarla */
    border: 1px solid #555555;/* Kenarlık ekle */
    padding: 10px 20px;       /* İç boşluk */
    font-size: 16px;          /* Yazı boyutu */
    transition: background-color 0.3s, color 0.3s; /* Geçiş efekti */
}

div.stButton > button:first-child:hover {
    background-color: #777777; /* Fare üzerine gelince rengi */
    color: white;
    border-color: #AAAAAA;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Style for the custom info box */
.custom-info-box {
    background-color: #444444; /* Darker grey background */
    color: #FFBF00;            /* Gold text color */
    border-left: 5px solid #FFBF00; /* Gold left border */
    padding: 10px 15px;
    border-radius: 5px;
    margin-bottom: 20px; /* Add some space below it */
}
</style>
""", unsafe_allow_html=True)

# SİSTEM ÇALIŞIYORDU 4 TUŞLU 2 TUŞ OLUNCA TUŞLARI BUYUTMEK İCİN
st.markdown("""
<style>
div.stButton > button {
    font-size: 24px !important;       /* Yazı boyutu */
    padding: 20px 40px !important;    /* Buton iç boşluğu */
    height: auto !important;          /* Yüksekliği büyüt */
    width: 100% !important;           /* Kolon genişliği kadar büyüt */
}
</style>
""", unsafe_allow_html=True)
# -------------------------------------


# PAGE_PASSWORDS sözlüğünü tam yol isimleriyle güncelle
PAGE_PASSWORDS = {
    "pages/page1.py": st.secrets.page1,
    "pages/page2.py": st.secrets.page2,
    "pages/page3.py": st.secrets.page3,
    "pages/page4.py": st.secrets.page4
}

# Secrets.toml dosyanızın içeriğinin bu şekilde olduğundan emin olun:
# .streamlit/secrets.toml
# [passwords]
# page1 = "gerçek_sifre_page1"
# page2 = "gerçek_sifre_page2"
# page3 = "gerçek_sifre_page3"
# page4 = "gerçek_sifre_page4"




# --- Şifre yönetimi için session state'leri başlat ---
if 'show_password_input' not in st.session_state:
    st.session_state.show_password_input = False
if 'target_page' not in st.session_state:
    st.session_state.target_page = None
if 'password_error' not in st.session_state:
    st.session_state.password_error = False


def check_password_and_navigate():
    entered_password = st.session_state.password_input
    target_page = st.session_state.target_page

    expected_password = PAGE_PASSWORDS.get(target_page) # Artık doğru şifreyi alacak!



    if target_page and entered_password == expected_password: # expected_password artık None olmayacak
        st.session_state.show_password_input = False
        st.session_state.password_error = False
        st.session_state.target_page = None
        st.switch_page(target_page) # Örneğin: "pages/page1.py"
    else:
        st.session_state.password_error = True


# --- Navigasyon Butonları ---
col1, col2 = st.columns(2)
with col1:
    if st.button('SATIŞ'):
        st.session_state.show_password_input = True
        st.session_state.target_page = "pages/page1.py" # Tam yolu kullan
        st.session_state.password_error = False
        # st.rerun() # Buradan kaldırıldı

with col2:
    if st.button('PAZARLAMA'):
        st.session_state.show_password_input = True
        st.session_state.target_page = "pages/page2.py" # Tam yolu kullan
        st.session_state.password_error = False
        # st.rerun() # Buradan kaldırıldı

#col3, col4 = st.columns(2)
#with col3:
    #if st.button('Veri Analizi'):
        #st.session_state.show_password_input = True
        #st.session_state.target_page = "pages/page3.py" # Tam yolu kullan
        #st.session_state.password_error = False
        # st.rerun() # Buradan kaldırıldı

#with col4:
    #if st.button('Raporlar'):
        #st.session_state.show_password_input = True
        #st.session_state.target_page = "pages/page4.py" # Tam yolu kullan
        #st.session_state.password_error = False
        # st.rerun() # Buradan kaldırıldı

st.markdown("<div style='margin-bottom: 70px;'></div>", unsafe_allow_html=True) # Adds a 30px vertical space


# --- Şifre Giriş Formu (Şartlı olarak görüntülenir) ---
if st.session_state.show_password_input:
    DISPLAY_NAMES = {
        "pages/page1.py": "SATIŞ",
        "pages/page2.py": "PAZARLAMA",
        "pages/page3.py": "VERİ ANALİZİ",
        "pages/page4.py": "RAPORLAR"
    }

    page_display_name = DISPLAY_NAMES.get(st.session_state.target_page, "BİLİNMEYEN SAYFA")

    st.markdown(f"""

    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="custom-info-box">
        <b>'{page_display_name}'</b> sayfasına erişmek için şifrenizi girin.
    </div>
    """, unsafe_allow_html=True)



    with st.form(key="password_form"):
        password_input = st.text_input("Şifre", type="password", key="password_input")
        col_buttons_1, col_buttons_2 = st.columns(2)

        with col_buttons_1:
            submit_button = st.form_submit_button("Onayla")

        with col_buttons_2:
            cancel_button = st.form_submit_button("İptal")

        if submit_button:
            check_password_and_navigate() # Bu çağrı zaten bir rerun tetikler
            # st.rerun() # Buradan kaldırıldı, gereksiz ve debug çıktısını siliyor olabilir
        elif cancel_button:
            st.session_state.show_password_input = False
            st.session_state.password_error = False
            st.session_state.target_page = None
            # st.rerun() # Buradan kaldırıldı

    if st.session_state.password_error:
        st.error("Yanlış şifre! Lütfen tekrar deneyin.")
