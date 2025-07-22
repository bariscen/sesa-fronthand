from google.cloud import storage
import pickle # .pkl dosyalarını okumak için gerekli
import os
import streamlit as st
import json



def get_gcs_client():
    """Google Cloud Storage istemcisini başlatır."""
    try:
        # Streamlit Cloud'da 'gcp_service_account' sırrı varsa onu al
        gcp_service_account_info = st.secrets['gcp_service_account']
        st.write(gcp_service_account_info)
        # Artık json.loads() kullanmaya gerek yok, çünkü st.secrets doğrudan bir AttrDict (sözlük benzeri) döndürüyor.
        # storage.Client.from_service_account_info() doğrudan bu sözlüğü kabul eder.
        client = storage.Client.from_service_account_info(gcp_service_account_info)

        st.success("GCS istemcisi hizmet hesabı ile başarıyla oluşturuldu.")

    except KeyError:
        # 'gcp_service_account' sırrı bulunamazsa buraya düşeriz (yerel testte veya sır eksikse)
        st.warning("GCP Service Account sırrı (gcp_service_account) Streamlit.secrets'ta bulunamadı. Yerel geliştirme için Application Default Credentials (ADC) kullanılacak.")
        client = storage.Client() # Yerelde ADC'yi kullanır, Cloud'da hata verir (çünkü sır yok)

    except Exception as e: # Catch all other potential errors during client creation
        st.error(f"GCS istemcisi oluşturulurken beklenmeyen bir hata oluştu: {e}")
        st.info("Lütfen Streamlit sırlarınızın doğru ayarlandığından ve hizmet hesabınızın geçerli olduğundan emin olun.")
        client = None

    return client


# --- GCS'ten Dosya Okuyan Ana Fonksiyon ---
def read_gcs_blob_content(blob_key: str):
    """
    secrets.toml'da tanımlı bir blob anahtarını kullanarak GCS'ten dosyayı okur.

    Args:
        blob_key (str): secrets.toml dosyasında tanımlı olan blob'un anahtarı (örn: "dikkat", "gelecek").

    Returns:
        Any or None: Okunan dosyanın içeriği (pickle ile yüklenmiş Python nesnesi)
                     veya bir hata oluşursa None.
    """
    # secrets.toml'dan kova adını ve blob adını çek
    try:
        bucket_name = st.secrets.GCS_BUCKET_NAME
        blob_name = st.secrets[blob_key]
        st.info(f"Kova adı: {bucket_name}, Blob adı: {blob_name}")
    except KeyError as e:
        st.error(f"secrets.toml dosyasında '{e}' anahtarı bulunamadı. Lütfen kontrol edin.")
        return None

    client = get_gcs_client()
    if client is None: # İstemci oluşmazsa devam etme
        st.error("GCS istemcisi oluşturulamadı, veri çekilemiyor.")
        return None

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    try:
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
