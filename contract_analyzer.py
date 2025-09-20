from data_handler import (
    connect_sheet,
    extract_text_from_file,
    semantic_chunking,
    get_next_id,
    update_sheet_with_data
)
from llm_analyzer import get_preferred_model_and_config, analyze_clause, extract_key_clauses
from concurrent.futures import ThreadPoolExecutor, as_completed



def analyze_single_clause(clause, clause_id, config):
    """
    Helper to analyze a single clause in parallel.
    Returns the result dict and row for Google Sheets.
    """
    try:
        regulation, summary, risk_level, risk_percent = analyze_clause(config, clause)
        key_clauses = extract_key_clauses(config, clause)
    except Exception as e:
        print(f"⚠️ Error analyzing clause {clause_id}: {e}")
        # Retry with next model
        config = get_preferred_model_and_config()
        regulation, summary, risk_level, risk_percent = analyze_clause(config, clause)
        key_clauses = extract_key_clauses(config, clause)

    result = {
        'clause_id': clause_id,
        'clause': clause,
        'regulation': regulation,
        'key_clauses': key_clauses,
        'risk_level': risk_level,
        'risk_percent': risk_percent,
        'summary': summary
    }

    row = [
        clause_id,
        regulation,
        key_clauses,
        risk_level,
        risk_percent,
        summary
    ]

    return result, row


def analyze_contract_file(file_path):
    """
    Analyze a contract file and return the analysis results.
    Parallelized across clauses.
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
        current_config = get_preferred_model_and_config()

        analysis_results = []
        rows_to_append = []

        # Parallel execution
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(analyze_single_clause, clause, starting_id + i, current_config): (i, clause)
                for i, clause in enumerate(clauses)
            }

            for future in as_completed(futures):
                try:
                    result, row = future.result()
                    analysis_results.append(result)
                    rows_to_append.append(row)
                except Exception as e:
                    print(f"Error in future: {e}")

        # Sort by clause_id so rows remain in order
        analysis_results.sort(key=lambda x: x['clause_id'])
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
    """
    Analyze multiple contract files in batch.
    """
    results = {}
    for file_path in file_paths:
        results[file_path] = analyze_contract_file(file_path)
    return results
