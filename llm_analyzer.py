import os
from groq import Groq
from dotenv import load_dotenv

def get_llm_client():    
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables.")
    return Groq(api_key=api_key)

def analyze_clause(client, clause):
    prompt = (
        f"Analyze this contract clause to identify the most relevant legal regulation (e.g., GDPR, HIPAA, or None) and assess its compliance. "
        f"Return the result in this format ONLY:\n"
        f"Regulation: <GDPR/HIPAA/Other/None>\n"
        f"Summary: <your 1-2 sentence summary under 100 words>\n"
        f"Risk: <High/Medium/Low>\n"
        f"Risk Percentage: <A percentage value from 0-100>\n\n"
        f"Clause: {clause}"
    )
    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )
    result = chat.choices[0].message.content.strip()
    
    regulation = "N/A"
    summary = "N/A"
    risk_level = "Unknown"
    risk_percent = "N/A"
    for line in result.splitlines():
        if line.startswith("Regulation:"):
            regulation = line.replace("Regulation:", "").strip()
        elif line.startswith("Summary:"):
            summary = line.replace("Summary:", "").strip()
        elif line.startswith("Risk:"):
            risk_level = line.replace("Risk:", "").strip()
        elif line.startswith("Risk Percentage:"):
            risk_percent = line.replace("Risk Percentage:", "").strip()
            
    return regulation, summary, risk_level, risk_percent

def extract_key_clauses(client, clause):
    prompt = (
        f"Read the following contract clause. "
        f"Extract the most important phrases that summarize its core obligation or purpose. "
        f"Return only the phrases as a comma-separated list. "
        f"For example, from 'CONSULTANT agrees to exercise special skill...', return 'exercise special skill, manner reasonably satisfactory'. "
        f"Clause: {clause}"
    )
    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
    )
    result = chat.choices[0].message.content.strip()
    return result