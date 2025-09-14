from data_handler import (
    connect_sheet,
    extract_text_from_file,
    semantic_chunking,
    get_next_id,
    update_sheet_with_data
)
from llm_analyzer import get_preferred_model_and_config, analyze_clause, extract_key_clauses
import time

def analyze_contract_file(file_path):
    """
    Analyze a contract file and return the analysis results.
    This function can be imported and used by other modules.
    
    Args:
        file_path (str): Path to the contract file (.pdf or .docx)
    
    Returns:
        list: List of analysis results for each clause
        None: If analysis fails
    """
    try:
        wks = connect_sheet()
        if not wks:
            print("Failed to connect to Google Sheets")
            return None

        expected_header = ["Clause ID", "Contract Clause", "Regulation", "Key Clauses (AI)", "Risk Level (AI)", "Risk % (AI)", "AI Summary"]
        current_header = wks.get_row(1, include_tailing_empty=False)
        if current_header != expected_header:
            wks.update_row(1, expected_header)
            print("Header updated to match required columns.")

        print("Reading contract...")
        contract_text = extract_text_from_file(file_path)
        clauses = semantic_chunking(contract_text)
        print(f"Extracted {len(clauses)} clauses from the document.")

        analysis_results = []
        rows_to_append = []
        starting_id = get_next_id(wks)
        
        current_config = get_preferred_model_and_config()

        for i, clause in enumerate(clauses):
            try:
                regulation, summary, risk_level, risk_percent = analyze_clause(current_config, clause)
                key_clauses = extract_key_clauses(current_config, clause)
                time.sleep(1)  # Add a small delay to respect API rate limits
            except Exception as e:
                print(f"⚠️ Error analyzing clause with current model. Attempting to switch to next available model.")
                print(f"Error: {e}")
                
                # If an error occurs, get the next model configuration
                current_config = get_preferred_model_and_config()
                
                regulation, summary, risk_level, risk_percent = analyze_clause(current_config, clause)
                key_clauses = extract_key_clauses(current_config, clause)

            clause_id = starting_id + i
            
            result = {
                'clause_id': clause_id,
                'clause': clause,
                'regulation': regulation,
                'key_clauses': key_clauses,
                'risk_level': risk_level,
                'risk_percent': risk_percent,
                'summary': summary
            }
            analysis_results.append(result)
            
            rows_to_append.append([
                clause_id,
                clause,
                regulation,
                key_clauses,
                risk_level,
                risk_percent,
                summary
            ])

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
    
    Args:
        file_paths (list): List of file paths to analyze
    
    Returns:
        dict: Dictionary with file paths as keys and analysis results as values
    """
    results = {}
    
    for file_path in file_paths:
        analysis_result = analyze_contract_file(file_path)
        results[file_path] = analysis_result
    
    return results