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


# app/gpt.py
# -*- coding: utf-8 -*-
"""
Cold-call research helper for flexible packaging.
Two-stage pipeline:
  1) HARVEST: collect web sources as JSON
  2) SYNTH: synthesize the 7-block Turkish report from those sources

Designed for OpenAI Python SDK >= 1.0; uses Responses API.
No 'response_format', no 'seed'. Optional web_search tool is toggleable.
"""

from __future__ import annotations
import re, json
from typing import Optional, Dict, List, Any, Tuple
from openai import OpenAI

# ---------- Client ----------
client = OpenAI()

# Toggle this if your account does/doesn't have the 'web_search' tool:
USE_WEB_SEARCH_TOOL_DEFAULT = True  # set False if your org lacks the tool

# ---------- Score parser ----------
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

# ---------- Region/Lang config ----------
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

# ---------- System/Human templates (concise, “think more” via planning cue) ----------

HARVEST_SYS = (
    "You are a senior web researcher. If a search tool is available, use it actively.\n"
    "Goal: collect EVIDENCE for {COMPANY} on flexible plastic packaging.\n"
    "Rules:\n"
    "- First, find the official site; then 2–4 independent sources.\n"
    "- Discover brand/alias pages (about/qui sommes nous/über uns/brands).\n"
    "- Prefer PDFs; extract a ≤20-word short quote including YEAR/PERCENT when present.\n"
    "- Only count as evidence what is explicitly written on the page.\n"
    "- OUTPUT: return **one single-line valid JSON** only; no fences, no extra text.\n"
    '- JSON schema: {"official":"<domain or empty>","items":[{"url":"...","site_type":"official|independent","date":"YYYY or empty","quote":"<=20 words"}]}\n'
    "- No placeholder URLs. No fabrication.\n"
    "Plan silently: (1) find official domain (2) collect 3–6 strongest sources (3) pull quote+year (4) output JSON."
)

HARVEST_USER = (
    "COMPANY: {COMPANY}\n"
    "LANG/COUNTRY: {LANG}\n\n"
    "Search hints:\n"
    '1) "{COMPANY}" site:*.com OR site:*.{TLD} ("about" OR "qui sommes" OR "über" OR "brands") → official\n'
    '2) "{COMPANY}" (packaging OR emballage OR sustainability OR environment)\n'
    '3) "{COMPANY}" (doypack OR pouch OR sachet OR "lidding film" OR "film plastique")\n'
    '4) "{MAIN_TOKEN}" (brand OR marque OR marke) (packaging OR emballage)\n'
    '5) "{COMPANY}" site:openfoodfacts.org\n'
    '6) ("{COMPANY}" OR "{MAIN_TOKEN}") site:{INDEP}\n\n'
    "Local keywords: {KW_HINT}\n\n"
    'Return **one single-line JSON** only, e.g. {"official":"example.com","items":[{"url":"https://example.com/...","site_type":"official","date":"2023","quote":"…"}]}'
)

SYNTH_SYS = (
    "You are a senior B2B analyst for flexible packaging. USE ONLY the provided sources. "
    "Do not show your chain of thought; only the final 7 blocks.\n"
    "Rules:\n"
    "- Base every claim on the given sources (official + independent).\n"
    '- Support claims with short quotes (“…”) and year/percent; put URLs ONLY in block 7.\n'
    "- Focus signals: formats (pouch/doypack, lidding, sachet), materials (mono-PE/PP, recyclable, EVOH/AlOx/SiOx), printing (digital/gravure), sustainability.\n"
    '- If evidence is weak, say “Bilinmiyor”; never invent.\n'
    "- Exactly 7 blocks; Turkish output.\n"
    "Plan silently: (1) split official/independent (2) pick 1–2 strongest proofs (3) extract YEAR/QUOTE (4) compute 0–10 score "
    "(category fit, evidence strength, material/barrier signal, sustainability) (5) write the 7 blocks.\n"
)

SYNTH_USER = (
    "ŞİRKET: {COMPANY}\n"
    "DİL/ÜLKE: {LANG}\n\n"
    "KAYNAK LİSTESİ (yalnız bunları kullan):\n"
    "{SOURCES_PACK}\n\n"
    "ÇIKTIYI Türkçe ve tam şu blok yapısında üret:\n\n"
    "1) Kısa cevap (tek paragraf):\n"
    '- "Evet./Hayır./Bilinmiyor." + Şirket adı + en güçlü 1–2 kanıt + yıl/yüzde.\n\n'
    "2) Kaynak etiketleri:\n"
    '- Örn: "Resmi site", "Label PME+", "Foodwatch", "Reporterre", "Open Food Facts", "Packaging Europe"\n\n'
    "3) Tek cümle öneri:\n"
    ' - “İstersen, hangi formatları (doypack/pouch, lidding film, sachet) kullandıklarına dair kanıt arayıp hızlı bir özet de çıkarabilirim.”\n\n'
    "4) Skor:\n"
    '- "Kısa cevap: X/10 (iyi/eşleşme/orta/zayıf)"\n\n'
    "5) Neden? (madde madde, her madde sonunda [etiket])\n"
    "- Kategori uyumu: … [etiket]\n"
    "- Plastik kanıtı: … [etiket]\n"
    "- Sürdürülebilirlik/fırsat: … [etiket]\n\n"
    "6) Risk/Notlar (madde madde) [etiket]\n\n"
    '7) Kaynaklar (madde madde, "Etiket — URL"):\n'
    "- Etiket — URL\n"
    "- Etiket — URL\n"
    "- Etiket — URL\n"
)

# ---------- Low-level helpers ----------

def _first_json_obj(text: str) -> Optional[dict]:
    """Extract the first {...} JSON object from plain text."""
    if not text:
        return None
    s = text.find("{")
    e = text.rfind("}")
    if s == -1 or e == -1 or e <= s:
        return None
    try:
        return json.loads(text[s:e+1])
    except Exception:
        return None

def _dedupe_items(items: List[dict]) -> List[dict]:
    seen, out = set(), []
    for it in items or []:
        url = (it or {}).get("url","").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(it)
    return out

def _build_sources_pack(items: List[dict], limit: int = 10) -> str:
    lines: List[str] = []
    for it in (items or [])[:limit]:
        url = (it.get("url","") or "").strip()
        title = (it.get("title","") or "").strip()
        site_type = (it.get("site_type","") or "").strip()
        date = (it.get("date","") or "").strip()
        quote = (it.get("quote","") or "").strip()
        lines.append(f"- [{site_type}] {title} — {url} — {date} — “{quote}”")
    return "\n".join(lines) if lines else "NONE"

def _responses_call(messages: List[dict], *, temperature=0.2, max_output_tokens=1400, use_web=True) -> str:
    """Thin wrapper around client.responses.create. Safe defaults; optional web_search tool."""
    params: Dict[str, Any] = {
        "model": "gpt-4o",
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
        "input": messages,
    }
    if use_web and USE_WEB_SEARCH_TOOL_DEFAULT:
        params["tools"] = [{"type": "web_search"}]
        params["tool_choice"] = "auto"
    resp = client.responses.create(**params)
    return getattr(resp, "output_text", None) or ""

# ---------- Stage 1: HARVEST ----------

def _harvest_sources(company: str, country: str, use_web: bool = True) -> Dict[str, Any]:
    cfg = REGION_CFG.get(country.upper(), REGION_CFG["EN"])
    lang = cfg["lang"]
    kw_hint = ", ".join(cfg["kw"][:6])
    indep_domains = " OR site:".join(cfg["indep"])
    tld = country.lower()

    sys_msg = HARVEST_SYS.format(COMPANY=company)
    usr_msg = HARVEST_USER.format(
        COMPANY=company,
        LANG=lang,
        TLD=tld,
        MAIN_TOKEN=company.split()[0],
        INDEP=indep_domains,
        KW_HINT=kw_hint,
    )

    messages = [
        {"role": "system", "content": [{"type": "input_text", "text": sys_msg}]},
        {"role": "user",   "content": [{"type": "input_text", "text": usr_msg}]},
    ]
    text = _responses_call(messages, temperature=0.15, max_output_tokens=1200, use_web=use_web)
    data = _first_json_obj(text) or {"items":[]}

    # Minimal adequacy check
    items = _dedupe_items(data.get("items") or [])
    has_official = any((it.get("site_type") == "official") for it in items)
    indep_count = sum(1 for it in items if it.get("site_type") == "independent")

    if not has_official or indep_count < 2:
        # Second pass: more aggressive nudge (PDF, alias, local terms)
        extra_user = (
            usr_msg +
            "\n\nSECOND PASS:\n- Prioritize PDFs; re-check brand/alias pages; prefer local-language queries (FR/DE/ES/IT/TR as relevant). "
            "Return one JSON line. At least 1 official + 2 independent."
        )
        messages2 = [
            {"role": "system", "content": [{"type": "input_text", "text": sys_msg}]},
            {"role": "user",   "content": [{"type": "input_text", "text": extra_user}]},
        ]
        text2 = _responses_call(messages2, temperature=0.1, max_output_tokens=1400, use_web=use_web)
        data2 = _first_json_obj(text2) or {"items":[]}
        # Merge
        merged = {}
        for it in (items + (data2.get("items") or [])):
            url = (it or {}).get("url","").strip()
            if url and url not in merged:
                merged[url] = it
        official = data.get("official") or data2.get("official") or ""
        data = {"official": official, "items": list(merged.values())}

    data["items"] = _dedupe_items(data.get("items") or [])
    return data

# ---------- Stage 2: SYNTHESIZE ----------

def _synthesize_report(company: str, country: str, sources: Dict[str, Any], use_web: bool = False) -> Tuple[str, Optional[float]]:
    cfg = REGION_CFG.get(country.upper(), REGION_CFG["EN"])
    lang = cfg["lang"]

    pack = _build_sources_pack(sources.get("items", []), limit=10)
    sys_msg = SYNTH_SYS
    usr_msg = SYNTH_USER.format(COMPANY=company, LANG=lang, SOURCES_PACK=pack)

    messages = [
        {"role": "system", "content": [{"type": "input_text", "text": sys_msg}]},
        {"role": "user",   "content": [{"type": "input_text", "text": usr_msg}]},
    ]
    text = _responses_call(messages, temperature=0.15, max_output_tokens=1500, use_web=use_web)
    score = _extract_score(text)
    return text, score

# ---------- Public entrypoint ----------

def cold_call_cevir(company_name: str, country: str = "EN", use_web: bool = True) -> Tuple[str, Optional[float]]:
    """
    Main entry. Returns (report_text, score_float|None).
    - company_name: e.g., "Daco France"
    - country: one of FR/DE/UK/ES/IT/TR/EN (EN is default)
    - use_web: True to enable web_search tool if your org has it
    """
    # Stage 1: harvest sources
    src = _harvest_sources(company_name, country, use_web=use_web)

    # Stage 2: synthesize report
    text, score = _synthesize_report(company_name, country, src, use_web=False)

    # Safety second pass if too weak
    if (score is None) or (score <= 2.0) or ("Bilinmiyor" in (text or "")):
        # Push the model to lean into PDFs/locals/alias again, but without changing API params
        nudged_pack = ( _build_sources_pack(src.get("items", []), limit=14) or "NONE" ) + \
                      "\n- [note] Re-check PDF/brand pages; prefer local-language quotes where available."
        usr_msg = SYNTH_USER.format(COMPANY=company_name, LANG=REGION_CFG.get(country.upper(), REGION_CFG["EN"])["lang"], SOURCES_PACK=nudged_pack)
        messages = [
            {"role": "system", "content": [{"type": "input_text", "text": SYNTH_SYS}]},
            {"role": "user",   "content": [{"type": "input_text", "text": usr_msg}]},
        ]
        text = _responses_call(messages, temperature=0.1, max_output_tokens=1600, use_web=False)
        score = _extract_score(text)

    return text, score


# ---------- Optional: quick manual test ----------
if __name__ == "__main__":
    name = "Daco France"
    out, sc = cold_call_cevir(name, country="FR", use_web=USE_WEB_SEARCH_TOOL_DEFAULT)
    print("\n=== REPORT ===\n")
    print(out)
    print("\n=== SCORE ===\n", sc)
