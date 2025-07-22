from google.cloud import storage
import pickle # .pkl dosyalarını okumak için gerekli
import os
import streamlit as st
import json



def get_gcs_client(): # Yardımcı fonksiyon olduğu için başına '_' ekledik
    """Google Cloud Storage istemcisini başlatır."""
    try:
        # Streamlit Cloud'da 'gcp_service_account' sırrı varsa onu kullan
        # Yerel çalışırken bu Key Error verir ve 'else' bloğuna düşer.
        gcs_credentials = st.secrets["gcp_service_account"]
        credentials_info = json.loads(gcs_credentials)
        client = storage.Client.from_service_account_info(credentials_info)
    except KeyError:
        # Sır bulunamazsa (yerel testte olduğu gibi), ADC'yi kullan
        client = storage.Client()
    except Exception as e:
        st.error(f"GCS istemcisi oluşturulurken bir hata oluştu: {e}")
        st.info("Lütfen Streamlit sırlarınızın doğru ayarlandığından emin olun.")
        client = None # Hata durumunda istemciyi None yap
    return client


# --- GCS'ten Dosya Okuyan Ana Fonksiyon ---
def read_gcs_blob_content(blob_key: str):

    # secrets.toml'dan kova adını ve blob adını çek
    try:
        bucket_name = st.secrets.GCS_BUCKET_NAME
        blob_name = st.secrets[blob_key]
    except KeyError as e:
        st.error(f"secrets.toml dosyasında '{e}' anahtarı bulunamadı. Lütfen kontrol edin.")
        return None

    client = get_gcs_client()
    if client is None: # İstemci oluşmazsa devam etme
        return None

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    try:
        # Dosyayı ikili (byte) olarak indir
        content_bytes = blob.download_as_bytes()
        loaded_data = pickle.loads(content_bytes)

        st.success(f"✅ Dosya çekildi.")
        return loaded_data

    except Exception as e:
        st.error(f"❌ GCS'den '{blob_name}' dosyasını okurken hata oluştu: {e}")
        st.info("Lütfen şunları kontrol edin:")
        st.info(f"1. **'{bucket_name}'** kova adının ve **'{blob_name}'** dosya yolunun doğru olduğundan ve dosyanın GCS'te mevcut olduğundan.")
        st.info("2. Kimlik bilgilerinizin (hizmet hesabı veya kişisel hesabınızın) bu kovaya **'Depolama Nesnesi Görüntüleyici'** iznine sahip olduğundan.")
        st.info("3. İnternet bağlantınızın aktif olduğundan.")
        return None
