from data_handler import (
    connect_sheet,
    extract_text_from_file,
    semantic_chunking,
    get_next_id,
    update_sheet_with_data
)
from llm_analyze_switch import get_preferred_model_and_config, analyze_clause, extract_key_clauses
import time

def main():
    contract_file_path = input("Enter path to contract file (.pdf or .docx): ")

    try:
        wks = connect_sheet()
        if not wks:
            return

        expected_header = ["Clause ID", "Contract Clause", "Regulation", "Key Clauses (AI)", "Risk Level (AI)", "Risk % (AI)", "AI Summary"]
        current_header = wks.get_row(1, include_tailing_empty=False)
        if current_header != expected_header:
            wks.update_row(1, expected_header)
            print("Header updated to match required columns.")

        print("Reading contract...")
        contract_text = extract_text_from_file(contract_file_path)
        clauses = semantic_chunking(contract_text)
        print(f"Extracted {len(clauses)} clauses from the document.")

        rows_to_append = []
        starting_id = get_next_id(wks)
        
        # Get the initial model configuration before the loop starts
        current_config = get_preferred_model_and_config()

        for i, clause in enumerate(clauses):
            try:
                # The functions now take the full config dictionary
                regulation, summary, risk_level, risk_percent = analyze_clause(current_config, clause)
                key_clauses = extract_key_clauses(current_config, clause)
                time.sleep(1) # Add a small delay to respect API rate limits
            except Exception as e:
                print(f"⚠️ Error analyzing clause with current model. Attempting to switch to next available model.")
                print(f"Error: {e}")
                
                # If an error occurs, get the next model configuration
                current_config = get_preferred_model_and_config()
                
                # Retry the failed clause with the new model
                regulation, summary, risk_level, risk_percent = analyze_clause(current_config, clause)
                key_clauses = extract_key_clauses(current_config, clause)

            clause_id = starting_id + i
            
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
        print("Workflow completed.")

    except FileNotFoundError as e:
        print(f"Error: {e}. Please check the file path.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
