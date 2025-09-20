import os
import requests
from groq import Groq
from groq.types.chat.chat_completion import ChatCompletion
from config import MODEL_CONFIG, MODEL_PREFERENCE_ORDER
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_preferred_model_and_config():
    for model_name in MODEL_PREFERENCE_ORDER:
        config = MODEL_CONFIG.get(model_name)
        if config:
            try:
                # Check for required API keys/tokens
                if config["provider"] == "groq":
                    api_key = os.getenv("GROQ_API_KEY")
                    if not api_key:
                        print(f"❌ GROQ_API_KEY not found. Skipping {model_name}.")
                        continue
                    test_client = Groq(api_key=api_key)
                    test_client.models.list()
                    config["client"] = test_client

                elif config["provider"] == "github":
                    pat = os.getenv("GITHUB_PAT")
                    if not pat:
                        print(f"❌ GITHUB_PAT not found. Skipping {model_name}.")
                        continue

                print(f"✅ Using model: {config['model_id']} from {config['provider']}")
                return config
            except Exception as e:
                print(f"❌ Model {config['model_id']} from {config['provider']} failed. Trying next model... Error: {e}")
                continue
    raise Exception("All configured models failed to connect.")

def _call_github_models_api(config, prompt, max_tokens):
    pat = os.getenv("GITHUB_PAT")
    headers = {
        "Authorization": f"Bearer {pat}",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    data = {
        "model": config["model_id"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens
    }

    response = requests.post(config["api_url"], headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"].strip()

# --- Parallelized Clause Analysis ---
def analyze_clause(config, clause):
    prompt = (
        f"Analyze this contract clause to identify the most relevant legal regulation (e'g., GDPR, HIPAA, or None) and assess its compliance. "
        f"Return the result in this format ONLY:\n"
        f"Regulation: <GDPR/HIPAA/Other/None>\n"
        f"Summary: <your 1-2 sentence summary under 100 words>\n"
        f"Risk: <High/Medium/Low>\n"
        f"Risk Percentage: <A percentage value from 0-100>\n\n"
        f"Clause: {clause}"
    )

    if config["provider"] == "groq":
        chat: ChatCompletion = config["client"].chat.completions.create(
            model=config["model_id"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        result = chat.choices[0].message.content.strip()
    elif config["provider"] == "github":
        result = _call_github_models_api(config, prompt, max_tokens=200)
    else:
        raise ValueError(f"Unknown provider: {config['provider']}")

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

def extract_key_clauses(config, clause): 
    prompt = (
        f"Read the following contract clause. "
        f"Extract the most important phrases that summarize its core obligation or purpose. "
        f"Return only the phrases as a comma-separated list. "
        f"For example, from 'CONSULTANT agrees to exercise special skill...', return 'exercise special skill, manner reasonably satisfactory'. "
        f"Clause: {clause}"
    )

    if config["provider"] == "groq":
        chat: ChatCompletion = config["client"].chat.completions.create(
            model=config["model_id"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )
        result = chat.choices[0].message.content.strip()
    elif config["provider"] == "github":
        result = _call_github_models_api(config, prompt, max_tokens=100)
    else:
        raise ValueError(f"Unknown provider: {config['provider']}")

    return result

# --- Parallel Processing Wrappers ---
def analyze_clauses_parallel(config, clauses, max_workers=5):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(analyze_clause, config, c): c for c in clauses}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                print(f"Error analyzing clause: {e}")
    return results

def extract_clauses_parallel(config, clauses, max_workers=5):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(extract_key_clauses, config, c): c for c in clauses}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                print(f"Error extracting key clause: {e}")
    return results
def modify_clause(config, clause, risk_level):
    if risk_level.lower() == "low":
        return clause  # no modification needed

    prompt = (
        f"The following contract clause has been assessed as {risk_level} risk. "
        f"Rewrite this clause to make it compliant with relevant regulations (e.g., GDPR, HIPAA), "
        f"while keeping the legal meaning intact. Return only the rewritten clause text.\n\n"
        f"Original Clause:\n{clause}"
    )

    if config["provider"] == "groq":
        chat = config["client"].chat.completions.create(
            model=config["model_id"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        return chat.choices[0].message.content.strip()
    elif config["provider"] == "github":
        return _call_github_models_api(config, prompt, max_tokens=300)
    else:
        raise ValueError(f"Unknown provider: {config['provider']}")
