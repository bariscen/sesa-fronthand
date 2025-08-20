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
from typing import Optional, Dict, List
from openai import OpenAI

import re, json
from typing import Optional, Dict, List, Any
from openai import OpenAI

client = OpenAI()

# --- Skor yakalama ---
SCORE_RE = re.compile(r"Kısa cevap:\s*([0-9]+(?:[.,][0-9]+)?)\s*/\s*10\b", re.I)
def _extract_score(text: str) -> Optional[float]:
    m = SCORE_RE.search(text or "")
    if not m:
        return None
    s = m.group(1).replace(",", ".")
    try:
        x = float(s)
        return max(0.0, min(10.0, x))
    except Exception:
        return None

# --- Bölgesel kısayollar ---
REGION_CFG: Dict[str, Dict[str, List[str]]] = {
    "FR":{"lang":"FR","kw":["emballage plastique","sachet","doypack","film plastique","lidding","mono-PE","mono-PP","recyclable","EVOH","AlOx","SiOx","barrière"],
          "indep":["label-pmeplus.fr","foodwatch.org","reporterre.net","openfoodfacts.org","packagingeurope.com"]},
    "DE":{"lang":"DE","kw":["Kunststoffverpackung","Beutel","Doypack","Sachet","Lidding","Mono-PE","Mono-PP","recycelbar","EVOH","AlOx","SiOx","Barriere"],
          "indep":["verpackung.org","lebensmittelzeitung.net","bvse.de","openfoodfacts.org","packagingeurope.com"]},
    "UK":{"lang":"EN","kw":["plastic packaging","pouch","doypack","sachet","lidding film","mono-PE","mono-PP","recyclable","EVOH","AlOx","SiOx","barrier"],
          "indep":["wrap.org.uk","thegrocer.co.uk","packagingnews.co.uk","openfoodfacts.org","packagingeurope.com"]},
    "ES":{"lang":"ES","kw":["envase plástico","bolsa","doypack","sachet","film tapa","mono-PE","mono-PP","reciclable","EVOH","AlOx","SiOx","barrera"],
          "indep":["packnet.es","envaspres.com","openfoodfacts.org","packagingeurope.com"]},
    "IT":{"lang":"IT","kw":["imballaggio plastico","busta","doypack","sacchetto","lidding","mono-PE","mono-PP","riciclabile","EVOH","AlOx","SiOx","barriera"],
          "indep":["packmedia.net","conai.org","openfoodfacts.org","packagingeurope.com"]},
    "TR":{"lang":"TR","kw":["plastik ambalaj","poşet","doypack","sachet","lidding film","mono PE","mono PP","geri dönüştürülebilir","EVOH","AlOx","SiOx","bariyer"],
          "indep":["ambalaj.org.tr","packagingturkey.com","openfoodfacts.org","packagingeurope.com"]},
    "EN":{"lang":"EN","kw":["plastic packaging","pouch","doypack","sachet","lidding film","mono-PE","mono-PP","recyclable","EVOH","AlOx","SiOx","barrier"],
          "indep":["openfoodfacts.org","packagingeurope.com","packaginginsights.com"]},
}

# --- Aşama 1: Kaynak topla (JSON) ---
SOURCES_SCHEMA = {
  "name":"PkgSources",
  "schema": {
    "type":"object",
    "properties":{
      "official":{"type":"string", "description":"Şirketin resmî web sitesi alan adı (ör. example.com)"},
      "items":{
        "type":"array",
        "items":{
          "type":"object",
          "properties":{
            "url":{"type":"string"},
            "title":{"type":"string"},
            "site_type":{"type":"string","enum":["official","independent"]},
            "date":{"type":"string","description":"YYYY veya YYYY-MM-DD gibi"},
            "quote":{"type":"string","description":"<=20 kelimelik kısa alıntı"}
          },
          "required":["url","site_type"]
        }
      }
    },
    "required":["items"]
  },
  "strict": True
}

def _source_harvest_prompt(company: str, country: str) -> str:
    cfg = REGION_CFG.get(country.upper(), REGION_CFG["EN"])
    kw = ", ".join(cfg["kw"][:6])
    indep = ", ".join(cfg["indep"][:4])
    main_token = company.split()[0]

    return f"""
ROLE: Web araştırmacısı.
GOAL: Aşağıdaki sorgularla kaynak topla ve JSON döndür (şema verildi). Gerçek URL ver; placeholder kullanma.

COMPANY: {company}
LANG/COUNTRY: {cfg['lang']}
SEARCH QUERIES (çalıştır):
1) "{company}" site:*.com OR site:*.{country.lower()}  ("about" OR "notre" OR "qui sommes" OR "über")  -> OFFICIAL
2) "{company}" packaging OR "emballage" OR "sustainability" OR "environment"
3) "{main_token}" brand OR "marque" OR "marke"  packaging OR "emballage"
4) "{company}" doypack OR pouch OR "sachet" OR "lidding" OR "film plastique"
5) "{company}" site:openfoodfacts.org
6) ("{company}" OR "{main_token}") site:{indep.replace(',', ' OR site:')}

RESULT RULES:
- En az 1 "official" ve en az 2 "independent" kayıt ver.
- PDF varsa aç ve <=20 kelime kısa alıntı çek ("…").
- "quote" alanında tarih/yüzde gibi en kuvvetli kanıtı ver.
- Dönüş sadece JSON olsun (şema: PkgSources).
"""

def _harvest_sources(company: str, country: str) -> Dict[str, Any]:
    prompt = _source_harvest_prompt(company, country)
    resp = client.responses.create(
        model="gpt-4o",
        tools=[{"type":"web_search"}],
        tool_choice="auto",
        temperature=0.1,
        max_output_tokens=1200,
        response_format={"type":"json_schema","json_schema":SOURCES_SCHEMA},
        input=[{"role":"user","content":[{"type":"input_text","text":prompt}]}]
    )
    try:
        data = json.loads(resp.output[0].content[0].text)
    except Exception:
        data = {"items":[]}

    # Yetersizse daha agresif ikinci tarama
    need_retry = True
    if data.get("items"):
        types = [it.get("site_type") for it in data["items"] if isinstance(it, dict)]
        if "official" in types and types.count("independent") >= 2:
            need_retry = False

    if need_retry:
        fix = "\n\n2nd PASS: PDF öncelikli tara; marka/alias olasılıklarını dene (örn. tüketici markası), FR/DE/ES/IT/TR lokal kelimelerle yeniden ara. En az 1 official + 2 independent şart."
        resp2 = client.responses.create(
            model="gpt-4o",
            tools=[{"type":"web_search"}],
            tool_choice="auto",
            temperature=0.1,
            max_output_tokens=1400,
            response_format={"type":"json_schema","json_schema":SOURCES_SCHEMA},
            input=[{"role":"user","content":[{"type":"input_text","text":prompt + fix}]}]
        )
        try:
            data2 = json.loads(resp2.output[0].content[0].text)
            # basit birleştirme
            if data.get("items") and data2.get("items"):
                merged = {it["url"]:it for it in data.get("items",[])+data2.get("items",[])}
                data = {"official": data.get("official") or data2.get("official"), "items": list(merged.values())}
            elif data2.get("items"):
                data = data2
        except Exception:
            pass

    return data

# --- Aşama 2: Sentez (7 blok) ---
def _synthesize_prompt(company: str, country: str, sources: Dict[str, Any]) -> str:
    cfg = REGION_CFG.get(country.upper(), REGION_CFG["EN"])
    # Kaynak paketini düz metin olarak enjekte et
    lines = []
    official = sources.get("official") or ""
    for it in sources.get("items", [])[:10]:
        url = it.get("url","")
        title = it.get("title","")
        site_type = it.get("site_type","")
        date = it.get("date","")
        quote = it.get("quote","")
        lines.append(f"- [{site_type}] {title} — {url} — {date} — “{quote}”")
    pack = "\n".join(lines) if lines else "NONE"

    return f"""
ROLE: Esnek ambalaj B2B analisti.
COUNTRY/LANG: {cfg['lang']}
COMPANY: {company}
OFFICIAL_HINT: {official or 'unknown'}

USE ONLY THESE SOURCES (below) for evidence. Do NOT invent:
{pack}

Write the answer in **Turkish** with exactly these 7 blocks and nothing else:

1) Kısa cevap (tek paragraf):
- "Evet./Hayır./Bilinmiyor." + Şirket adı + en güçlü 1–2 kanıt + yıl/yüzde (varsa).

2) Kaynak etiketleri:
- Örn: "Resmi site", "Label PME+", "Foodwatch", "Reporterre", "Open Food Facts", "Packaging Europe"

3) Tek cümle öneri:
- “İstersen, hangi formatları (doypack/pouch, lidding film, sachet) kullandıklarına dair kanıt arayıp hızlı bir özet de çıkarabilirim.”

4) Skor:
- "Kısa cevap: X/10 (iyi/eşleşme/orta/zayıf)"

5) Neden? (madde madde, her madde sonunda [etiket])
- Kategori uyumu: … [etiket]
- Plastik kanıtı: … [etiket]
- Sürdürülebilirlik/fırsat: … [etiket]

6) Risk/Notlar (madde madde) [etiket]

7) Kaynaklar (madde madde, "Etiket — URL"):
- Etiket — URL

KURALLAR:
- Her iddiayı YUKARIDAKİ kaynaklardan birine dayandır ve etiketle.
- Alıntıları "…" içinde kısa ver; URL’leri sadece 7. blokta yaz.
- Kanıt yetersizse “Bilinmiyor” de (uydurma yapma).
"""

def cold_call_cevir(company_name: str, country: str = "EN"):
    """
    İki aşamalı (ARA→SENTEZ) güvenilir akış.
    Dönüş: (text, score)
    """
    # 1) Kaynak topla
    src = _harvest_sources(company_name, country)

    # 2) Kaynaklarla 7 blok sentez
    syn_prompt = _synthesize_prompt(company_name, country, src)
    resp = client.responses.create(
        model="gpt-4o",
        temperature=0.1,
        max_output_tokens=1400,
        input=[{"role":"user","content":[{"type":"input_text","text": syn_prompt}]}]
    )
    text = resp.output_text
    score = _extract_score(text)

    # 3) Çok zayıfsa bir kez daha (ek ipucu: PDF/yerel dil/marka)
    if (score is None) or (score <= 2.0) or ("Bilinmiyor" in (text or "")):
        nudge = syn_prompt + "\n\nEK NOT: PDF ve yerel dil sayfalarına odaklan; tüketici markası/alias ihtimalini tekrar tara; en az 3 kaynak göster."
        resp2 = client.responses.create(
            model="gpt-4o",
            temperature=0.1,
            max_output_tokens=1500,
            input=[{"role":"user","content":[{"type":"input_text","text": nudge}]}]
        )
        text = resp2.output_text
        score = _extract_score(text)

    return text, score
