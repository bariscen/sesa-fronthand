import streamlit as st

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Bu sayfaya erişmek için giriş yapmalısınız.")
    st.stop()
