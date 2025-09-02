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
import google.generativeai as genai



os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

gemini_key = st.secrets["GEMINI_API_KEY"]
model_gemini = genai.GenerativeModel('gemini-1.5-pro-latest')





llm = ChatOpenAI(model="gpt-4o", temperature=0.7)


def get_observation(company_info: str, state: str, website: str, target_sector: str) -> str:
    messages = [
        SystemMessage(content="""
You are a research-oriented business analyst and B2B cold email strategist. Your role is to extract the most insightful, strategic observation from real company data.
"""),
        HumanMessage(content=f"""
Please conduct research on {company_info} based in {state} to understand its core business, market position, and strategy. You may use local-language sources for your research to gain the deepest insights.

Based on your findings, generate a single, concise English paragraph (2-3 sentences) that provides a strategic observation about the company.

Your observation must:
- Demonstrate a deep understanding of the company's **position**, **strategy**, **market**, or **operations**.
- Be strictly grounded in the data you find—do not make assumptions or guesses.
- Not mention any specific dates.
- Be analytical and professional, like a business analyst would write.
- **Do NOT** write an email.

Company Information:
- Company Name: {company_info}
- State: {state}
- Target Sector: {target_sector}
- Website: {website}
""")
    ]
    try:
        response = model_gemini.generate_content(messages)
        return response.text.strip()
    except Exception as e:
        return f"Hata(get_observation): {e}"


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
import re

client = OpenAI()

import re
from openai import OpenAI

client = OpenAI()

def cold_call_cevir(company_name: str, country: str = "EN", website: str = None, sector: str = None):
    """
    Esnek ambalaj firması için verilen şirketin potansiyel müşteri olup olmadığını analiz eder.
    Sadece OpenAI kullanır. Geriye analiz metni ve 10 üzerinden puan döner.
    """

    site_info = f'The official website of the company is: {website}' if website else 'There is no official website provided.'

    prompt = f"""
You are a senior B2B market analyst working for a flexible packaging manufacturer in Europe. Your task is to assess whether the company "{company_name}" located in "{country}" in {sector} sector could be a good potential customer for flexible packaging products (e.g., doypacks, lidding films, pouches).

{site_info}

Flexible packaging is typically used in food, cosmetics, pet food, homecare, personal care, detergents, supplements, and healthcare.

All research, analysis, and output MUST be done in the native language of {country}. This includes visiting the company's {website}, reading their product and about-us pages, and analyzing packaging clues.

If the website is not available or inaccessible, clearly state that and rely only on known industry signals.

Answer in the following format:

1) Short answer (1 paragraph):
- Visit their website and describe what the company does.
- Check their product pages to see if flexible packaging is visible or likely.
- Check the about-us or corporate section to see if they own brands or are resellers.

2) Score (on a 10-point scale):
- Format: "Score: X/10 (excellent/good/moderate/weak)"
- Important: Output the score exactly in this format.

3) Why? (bullet points)
- Sector alignment
- Packaging indicators
- Sustainability or sourcing opportunity
- Strategic clues (growth, innovation, product line, etc.)
- **Production/Filling Activities:** Does the company manufacture or fill its own products? This indicates a direct need for packaging.
- **Import/Export Activities:** Does the company engage in international trade? This can signal a need for high-quality, durable packaging suitable for transport.

4) Risks / unknowns (bullet points)
- Packaging needs unclear?
- Outsourced production?
- Lack of market signals?

5) Final recommendation (1 sentence)

Rules:
- Do NOT make up information. If info is unclear, say so.
- Use industry knowledge.
- Do not use placeholder URLs or fake evidence.
- Stay concise and structured.


6) Yazdığın cevabın hepsini Türkçeye çevir ve öyle ver, yazının orjinalini verme.
"""

    # Gemini API çağrısı
    response = model_gemini.generate_content(prompt)
    text = response.text

    # Extract score
    score = None
    match = re.search(r"(Score|Puan)[:：]?\s*([0-9]+(?:[.,][0-9]+)?)\s*/\s*10", text, re.IGNORECASE)
    if match:
        try:
            score = float(match.group(2).replace(",", "."))
        except ValueError:
            pass

    return text, score
