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


import re
from typing import List, Optional, Dict
from openai import OpenAI

client = OpenAI()

# --- Skor yakalama ---
SCORE_RE = re.compile(r"Kısa cevap:\s*([0-9]+(?:[.,][0-9]+)?)\s*/\s*10\b", re.I)
def _extract_score(text: str) -> Optional[float]:
    m = SCORE_RE.search(text or "")
    if not m: return None
    s = m.group(1).replace(",", ".")
    try:
        x = float(s)
        return max(0.0, min(10.0, x))
    except Exception:
        return None

# --- Ülke/dil kısayolları (kısa & net anahtarlar) ---
REGION_CFG: Dict[str, Dict[str, List[str]]] = {
    "FR":{"lang":"FR","kw":["emballage plastique","sachet","doypack","film plastique","lidding","mono-PE","mono-PP","recyclable","EVOH","AlOx","SiOx","barrière"]},
    "DE":{"lang":"DE","kw":["Kunststoffverpackung","Beutel","Doypack","Sachet","Lidding","Mono-PE","Mono-PP","recycelbar","EVOH","AlOx","SiOx","Barriere"]},
    "UK":{"lang":"EN","kw":["plastic packaging","pouch","doypack","sachet","lidding film","mono-PE","mono-PP","recyclable","EVOH","AlOx","SiOx","barrier"]},
    "ES":{"lang":"ES","kw":["envase plástico","bolsa","doypack","sachet","film tapa","mono-PE","mono-PP","reciclable","EVOH","AlOx","SiOx","barrera"]},
    "IT":{"lang":"IT","kw":["imballaggio plastico","busta","doypack","sacchetto","lidding","mono-PE","mono-PP","riciclabile","EVOH","AlOx","SiOx","barriera"]},
    "TR":{"lang":"TR","kw":["plastik ambalaj","poşet","doypack","sachet","lidding film","mono PE","mono PP","geri dönüştürülebilir","EVOH","AlOx","SiOx","bariyer"]},
    "EN":{"lang":"EN","kw":["plastic packaging","pouch","doypack","sachet","lidding film","mono-PE","mono-PP","recyclable","EVOH","AlOx","SiOx","barrier"]},
}

# --- Kısa & net Prompt (tek görev, 7 blok çıktı, kaynak zorunlu) ---
BASE_PROMPT = """ROLE: Flexible packaging için kanıta-dayalı B2B araştırmacısın.

TASK: "{COMPANY}" hakkında yalnız web kanıtına dayanarak cevap ver.
LANG/COUNTRY: {LANG}
FOCUS: format (pouch/doypack, lidding film, sachet), malzeme (mono-PE/PP, recyclable, foil/EVOH/AlOx/SiOx), baskı (digital/gravure), sürdürülebilirlik.

RULES (kısa):
- Önce resmî siteyi bul (ülkeye uygun TLD varsa onu tercih et), sonra 2–4 bağımsız kaynak (NGO/haber/veritabanı).
- {KW_HINT}
- Kanıt yoksa “Bilinmiyor” de; uydurma yapma.
- Her iddiayı kısa alıntı (“…”) ve yıl/yüzde ile destekle.
- Yalnız 7 blok yaz; placeholder ([URL]) kullanma; gerçek URL ver.

OUTPUT (tam bu yapı):
1) Kısa cevap:
- Evet./Hayır./Bilinmiyor. {COMPANY} … (YYYY, “kısa alıntı”). …

2) Kaynak etiketleri:
- Resmi site
- (ör. Label PME+, Foodwatch, Reporterre / Packaging News / Open Food Facts …)

3) Tek cümle öneri:
- “İstersen, hangi formatları (doypack/pouch, lidding film, sachet) kullandıklarına dair kanıt arayıp hızlı bir özet de çıkarabilirim.”

4) Skor:
- Kısa cevap: X/10 (iyi/eşleşme/orta/zayıf)

5) Neden?
- Kategori uyumu: … [etiket]
- Plastik kanıtı: … [etiket]
- Sürdürülebilirlik/fırsat: … [etiket]

6) Risk/Notlar:
- … [etiket]

7) Kaynaklar:
- Etiket — URL
- Etiket — URL
- Etiket — URL
"""

def _prompt_for(company: str, country: str) -> str:
    cfg = REGION_CFG.get(country.upper(), REGION_CFG["EN"])
    kw = cfg["kw"]
    kw_hint = f"Ara: {company} + ({', '.join(kw[:6])}); resmi sitede 'sustainability/packaging/product' sayfaları; bağımsız kaynakta marka adıyla eşleşme."
    return (BASE_PROMPT
            .replace("{COMPANY}", company)
            .replace("{LANG}", cfg["lang"])
            .replace("{KW_HINT}", kw_hint))

def _call_once(prompt: str, effort: str = "high", seed: int = 7):
    params = {
        "model": "gpt-4o",                      # dil+web için iyi genel model
        "temperature": 0.2,
        "max_output_tokens": 1400,              # uzun 7 blok için alan
        "seed": seed,
        "tools": [{"type": "web_search"}],      # OpenAI web araması
        "tool_choice": "auto",
        "input": [{"role":"user","content":[{"type":"input_text","text": prompt}]}]
    }
    # reasoning destekli modellerde (örn. o3/o4) şu alan da işe yarar; desteklemiyorsa yoksayılır:
    params["reasoning"] = {"effort": effort}
    resp = client.responses.create(**params)
    return resp.output_text

def cold_call_cevir(company_name: str, country: str = "EN"):
    """
    Yüksek düşünme + 2 geçişli web araması; (text, score) döndürür.
    """
    prompt = _prompt_for(company_name, country)

    # Geçiş 1: yüksek reasoning
    text = _call_once(prompt, effort="high", seed=11)
    score = _extract_score(text)

    # Zayıfsa/“Bilinmiyor” ise Geçiş 2: agresif tekrar (PDF/marka/yerel dil vurgusu)
    if (score is None) or (score <= 2.0) or ("Bilinmiyor" in (text or "")) or ("[URL]" in (text or "")):
        fix = (
            "\n\n2nd PASS (daha derin):\n"
            "- PDF sonuçlarını özellikle tara; yıl ve yüzdeyi alıntıla.\n"
            "- Marka/ürün sayfalarını ve Open Food Facts/NGO kayıtlarını ekle.\n"
            "- En az 3 kaynak (1 resmi site), gerçek URL ver; placeholder kullanma.\n"
            "- Kanıt yetersizse yine 'Bilinmiyor' de."
        )
        text = _call_once(prompt + fix, effort="high", seed=29)
        score = _extract_score(text)

    return text, score
