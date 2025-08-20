import os
import pandas as pd
import streamlit as st
import numpy as np
from pathlib import Path
import requests
import time
import sys
import PyPDF2
from langchain.schema import HumanMessage, SystemMessage


os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["LANGSMITH_API_KEY"] = st.secrets["LANGSMITH_API_KEY"]
os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)


def get_observation(company_info: str) -> str:
    messages = [
        SystemMessage(content="""
You are a research-oriented business analyst and B2B cold email strategist. Your role is to extract the most insightful, strategic observation from real company data.
"""),
        HumanMessage(content=f"""
Using the company data below, generate a short and insightful paragraph (2–3 sentences) that:

- Demonstrates a deep understanding of the company's **position**, **strategy**, or **market**

- Don't mention any dates.
- Is grounded strictly in the data — no guesses or assumptions

Do NOT write an email. Just return the observation paragraph, like a strategist or business analyst would.

Company Information:
{company_info}
""")
    ]

   # - Can reference packaging, innovation, growth, hiring, product focus, operations, or industry dynamics

    response = llm(messages)
    return response.content.strip()

def extract_state(State):
    prompt = f"""
    Based on the following information, identify the country code.

    info:
    {State}

    Choose **only one** from this list:
    ['TR', 'NL', 'QA', 'SE', 'PL', 'CY', 'GB', 'TN', 'GR', 'FR', 'IL',
       'US', 'RO', 'BG', 'MA', 'DE', 'IT']

    Return only the selected country code, e.g., 'TR', 'DE', 'FR'.
    """

    try:
        ulke = llm.predict(prompt).strip().upper()
        return ulke if ulke in ['TR', 'NL', 'QA', 'SE', 'PL', 'CY', 'GB', 'TN', 'GR', 'FR', 'IL',
                                'US', 'RO', 'BG', 'MA', 'DE', 'IT'] else None
    except Exception as e:
        print(f"Error processing row: {e}")
        return None



def extract_sector(tavily_response):
    prompt = f"""
    You are an expert in classifying companies by industry sector.

    Based on the following company information, identify the **main** industry sector from the predefined list.

    Company info:
    {tavily_response}

    Choose **only one** from this list:
    ['snacking', 'protein', 'pet', 'bakery', 'seafood', 'meat products', 'fertilizer/pesticide',
     'powdered food', 'personal care', 'ready meal', 'frozen fruit and vegetable',
     'agricultural products', 'legumes/grains', 'dairy products', 'powdered beverage',
     'wet wipes', 'nuts', 'dried fruit', 'pet food', 'seasoning', 'coffee',
     'lamination film', 'fresh vegetable', 'retort pet food', 'shopping bag',
     'retort canned food']

    Return only the selected category word, e.g., 'protein', 'meat products', etc.
    """
    sector = llm.predict(prompt).strip().lower()
    return sector


def rag(file_path):
    with open(file_path, "rb") as f:
        pdf_reader = PyPDF2.PdfReader(f)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def referans(df, target_sector, ulke):
    en_cok_benzeyen = df[(df['COUNTRY'] == ulke) & (df['Sektor'] == target_sector)]['Musteri'].to_dict()
    ayni_ulke = df[(df['COUNTRY'] == ulke)]['Musteri'].head().to_dict()
    ayni_sektor = df[(df['Sektor'] == target_sector)]['Musteri'].head().to_dict()
    referanslar = {}
    referanslar['Same country and same sector'] = en_cok_benzeyen
    referanslar['same country'] = ayni_ulke
    referanslar['same sector'] = ayni_sektor
    return referanslar

def generate_better_email(tavily_info, position, target_sector, context, company_info, referanslar):
    prompt = f"""
You are writing a cold email on behalf of a flexible packaging company based in Turkey. Keep it under 120 words.

Here is some background info:

- The recipient works in the position of: {position}
- Target sector: {target_sector}
- Our strengths: {context}
- Our competitive andvantages: Shorter delivery time, competitive prices and all production is in one place
- Products for sustainability: recyclable and compostable packaging
- Social proof: {referanslar}
- Observations: {tavily_info}
- Targetted company: {company_info}


Instructions:
- Write a **short, warm and human-like cold email**.
- Start with a personalized, observational intro (2 sentences).
- Then 2–3 sentences explaining why we’re reaching out and how we can help.
- Mention competitive andvantages
- Mention products for sustainability if relevant.
- Mention 3 reference clients or projects if relevant.
- End with a soft close: say we’re happy to answer questions, and mention our packaging trends newsletter.

Guidelines:
- Use simple English.
- Avoid sounding too “salesy” or robotic.
- Avoid "I" — write as a team.
- If halal or kosher needs are relevant, you can mention we support both.

Output: Write the full email as plain text.
"""
    return llm.predict(prompt).strip()



def create_personalized_email(message, recipient_name, target_language=None):
    """
    message: plain message text (str)
    recipient_name: target kişinin tam adı (str)
    target_language: eğer belirtilirse, mesajı bu dile çevir (str), örn. 'Turkish', 'Spanish', vs.

    Fonksiyon, verilen mesajı alır, kişiselleştirir, mail formatına çevirir ve istenirse çeviri yapar.
    """

    prompt = f"""
You are a professional email assistant.

1) Take the following plain message and write a polite, clear cold email body by:
- Starting with "Dear {recipient_name},"
- Then inserting the message text naturally, breaking it into paragraphs if needed
- Ending with a polite sign-off like:
  "Best regards,
   [Your Name]
   [Your Position]
   SESA Packaging Solutions"

2) If a target language is specified (other than English), translate the entire email to that language, keeping formatting and politeness.

Here is the plain message to use:

\"\"\"{message}\"\"\"

Target language: {target_language if target_language else 'English'}
Write like a avarage {target_language} human.
Write the full email text only.

"""
    email_text = llm.predict(prompt).strip()
    return email_text


def translator(text, target_lang="English"):
    system_prompt = "You are a professional translator."
    user_prompt = f"Translate the following text to {target_lang}:\n\n{text}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    response = llm.invoke(messages)
    return response.content.strip()


from openai import OpenAI
client = OpenAI()


import re


client = OpenAI()

SCORE_RE = re.compile(r"Kısa cevap:\s*([0-9]+(?:[.,][0-9]+)?)\s*/\s*10\b", re.IGNORECASE)

def _extract_score(text: str):
    """
    Metindeki 'Kısa cevap: X/10' deseninden skoru (float) çeker.
    Bulamazsa None döner.
    """
    m = SCORE_RE.search(text or "")
    if not m:
        return None
    s = m.group(1).replace(",", ".")
    try:
        val = float(s)
    except ValueError:
        return None
    # 0-10 aralığına kırp
    return max(0.0, min(10.0, val))

def cold_call_cevir(COMPANY_NAME: str):
    PROMPT = """ROLE: Esnek ambalaj (flexible packaging) alanında kanıta-dayalı B2B araştırmacısın.

GÖREV: "{COMPANY_NAME}" için webde (önce resmî site/marka sayfaları) kanıt topla ve aşağıdaki çıktıyı üret.
- Web araması yap, 3–6 güvenilir kaynaktan veri çek. En az 1 kaynak resmî site olmalı.
- Yalnızca sitede AÇIKÇA yazan şeyleri “kanıt” say. Sezgi/yorumları “Risk/Notlar”a yaz.
- Tarihleri belirt (örn. "2020", "2023-05"). Yüzdeleri ve iddiaları kısa alıntıyla (≤20 kelime) destekle.
- Plastik ambalaj kullanımı için paket formatları (pouch/doypack, lidding/top web, sachet), malzemeler (mono-PE/PP, recyclable, foil/EVOH/AlOx/SiOx), baskı (digital/gravure) ve sürdürülebilirlik ifadeleri aransın.
- Yeterli kanıt yoksa "Bilinmiyor" de; uydurma yapma.

ÇIKTI FORMATIN (Türkçe, aynen bu blok yapısı):
1) Kısa cevap (tek paragraf):
- "Evet./Hayır./Bilinmiyor." + Şirket adı + en güçlü 1–2 kanıt + (varsa) yıl/yüzde.
- Örnek format:
  Evet. {Şirket} ürünlerinde plastik ambalaj kullanıyor/kullandı. {YYYY}’de {kısa kanıt}. {YYYY}’de {kısa kanıt}.

2) Kaynak etiketleri (yalın satırlar, kurum/etiket + isteğe bağlı dil/ülke):
- Örnek: "Label PME+", "Foodwatch EN", "Reporterre", "Resmi site"

3) Tek cümle öneri:
- “İstersen, hangi formatları (doypack/pouch, lidding film, sachet) kullandıklarına dair kanıt arayıp hızlı bir özet de çıkarabilirim.”

4) Skor:
- "Kısa cevap: X/10 (iyi/eşleşme/orta/zayıf)"
- Değerlendirme ölçütü: kategori uyumu, plastik/format kanıtı, malzeme & bariyer sinyalleri, sürdürülebilirlik hedefleri.
  8–10: güçlü kanıt; 5–7: kısmi kanıt; 3–4: zayıf; 0–2: yok/çelişkili.

5) Neden? (madde madde, her madde sonunda kısa kaynak etiketi)
- Kategori uyumu: … [etiket]
- Plastik kanıtı: … [etiket]
- Sürdürülebilirlik/fırsat: … [etiket]

6) Risk/Notlar (madde madde, varsa alternatif materyal/kağıt eğilimleri, belirsizlikler) [etiket]

7) Kaynaklar (madde madde, "Etiket — URL" şeklinde):
- Label PME+ — <url>
- Foodwatch EN — <url>
- Reporterre — <url>
- Resmi site — <url>

KURALLAR:
- Tüm iddiaları kaynakla bağla; her maddeye en az bir etiket ekle.
- Alıntıları "…" içinde ver ve kısa tut.
- URL’leri “Kaynaklar” bölümünde ver; gövdede yalnız etiket kullan.
- Kanıt tarihi eskiyse belirt; çelişki varsa uyar.
- Çıktıda sadece belirtilen 7 blok olsun, fazladan açıklama yazma.
"""
    prompt = PROMPT.replace("{COMPANY_NAME}", COMPANY_NAME)

    resp = client.responses.create(
        model="gpt-4o",
        tools=[{"type": "web_search"}],  # hesabında açıksa web araması yapar
        input=[{
            "role": "user",
            "content": [{"type": "input_text", "text": prompt}]
        }]
    )

    text = resp.output_text
    score = _extract_score(text)  # float veya None
    return text, score
