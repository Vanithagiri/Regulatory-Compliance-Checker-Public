from data_handler import (
    connect_sheet,
    extract_text_from_file,
    semantic_chunking,
    get_next_id,
    update_sheet_with_data
)
from llm_analyzer import get_llm_client, analyze_clause, extract_key_clauses

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

        llm_client = get_llm_client()
        rows_to_append = []
        starting_id = get_next_id(wks)
        
        for i, clause in enumerate(clauses):
            regulation, summary, risk_level, risk_percent = analyze_clause(llm_client, clause)
            key_clauses = extract_key_clauses(llm_client, clause)
            
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