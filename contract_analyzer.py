# contract_analyzer.py (Updated with improved fallback logic)

from data_handler import (
    connect_sheet,
    extract_text_from_file,
    semantic_chunking,
    get_next_id,
    update_sheet_with_data
)
from llm_analyzer import get_preferred_model_and_config, analyze_clause, extract_key_clauses
from config import MODEL_PREFERENCE_ORDER, MODEL_CONFIG
from concurrent.futures import ThreadPoolExecutor, as_completed

def analyze_single_clause(clause, clause_id):
    """
    Helper to analyze a single clause in parallel with robust model fallback.
    It will try each model in MODEL_PREFERENCE_ORDER until one succeeds.
    """
    for model_name in MODEL_PREFERENCE_ORDER:
        try:
            print(f"Attempting to analyze Clause ID: {clause_id} with model: {model_name}")
            config = MODEL_CONFIG.get(model_name)
            if not config:
                print(f"⚠️ Config for model '{model_name}' not found. Skipping.")
                continue

            regulation, summary, risk_level, risk_percent, ai_modified_clause, ai_modified_risk_level = analyze_clause(config, clause)
            key_clauses = extract_key_clauses(config, clause)

            result = {
                'clause_id': clause_id,
                'clause': clause,
                'regulation': regulation,
                'key_clauses': key_clauses,
                'risk_level': risk_level,
                'risk_percent': risk_percent,
                'summary': summary,
                'AI-Modified Clause': ai_modified_clause,
                'AI-Modified Risk Level': ai_modified_risk_level
            }

            row = [
                clause_id,
                regulation,
                key_clauses,
                risk_level,
                risk_percent,
                summary
            ]
            
            print(f"✅ Successfully analyzed Clause ID: {clause_id} with model: {model_name}")
            return result, row

        except Exception as e:
            print(f"❌ FAILED to analyze Clause ID: {clause_id} with model: {model_name}. Error: {e}")
            continue # Try the next model in the preference order

    # This part is reached only if all models fail for a clause
    print(f"🚨 ALL MODELS FAILED for Clause ID: {clause_id}. Returning empty data.")
    return None, None


def analyze_contract_file(file_path):
    """
    Analyze a contract file and return the analysis results.
    """
    try:
        wks = connect_sheet()
        if not wks:
            print("Failed to connect to Google Sheets")
            return None

        expected_header = ["Clause ID", "Regulation", "Key Clauses (AI)", "Risk Level (AI)", "Risk % (AI)", "AI Summary"]

        current_header = wks.get_row(1, include_tailing_empty=False)
        if current_header != expected_header:
            wks.update_row(1, expected_header)
            print("Header updated to match required columns.")

        print("Reading contract...")
        contract_text = extract_text_from_file(file_path)
        clauses = semantic_chunking(contract_text)
        print(f"Extracted {len(clauses)} clauses from the document.")

        starting_id = get_next_id(wks)

        analysis_results = []
        rows_to_append = []

        # Parallel execution
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(analyze_single_clause, clause, starting_id + i): (i, clause)
                for i, clause in enumerate(clauses)
            }

            for future in as_completed(futures):
                try:
                    result, row = future.result()
                    if result and row: # Only append if the analysis was successful
                        analysis_results.append(result)
                        rows_to_append.append(row)
                except Exception as e:
                    print(f"Error processing future result: {e}")

        
        if analysis_results:
            analysis_results.sort(key=lambda x: x['clause_id'])
        if rows_to_append:
            rows_to_append.sort(key=lambda x: x[0])

        update_sheet_with_data(wks, rows_to_append)
        print("Analysis completed and data updated in Google Sheets.")

        return analysis_results

    except FileNotFoundError as e:
        print(f"Error: {e}. Please check the file path.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def batch_analyze_contracts(file_paths):
    results = {}
    for file_path in file_paths:
        results[file_path] = analyze_contract_file(file_path)
    return results