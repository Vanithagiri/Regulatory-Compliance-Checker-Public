import os
import pygsheets
import docx
from pypdf import PdfReader
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_experimental.text_splitter import SemanticChunker

def connect_sheet():
    load_dotenv()
    creds_path = os.getenv("GOOGLE_SHEET_API_CRED")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    
    if not creds_path or not os.path.exists(creds_path):
        raise FileNotFoundError(f"Service account JSON not found at {creds_path}")
    try:
        gc = pygsheets.authorize(service_file=creds_path)
        sh = gc.open_by_key(sheet_id)
        return sh.sheet1
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def extract_text_from_file(file_path):
    if file_path.endswith('.pdf'):
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    elif file_path.endswith('.docx'):
        doc = docx.Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    else:
        raise ValueError("Unsupported file format. Please use a .pdf or .docx file.")

def semantic_chunking(text):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    text_splitter = SemanticChunker(embeddings)
    clauses = text_splitter.create_documents([text])
    return [doc.page_content for doc in clauses]

def get_next_id(wks):
    """Gets the next available Clause ID from the sheet."""
    all_values = wks.get_all_values(include_tailing_empty=False)
    return len(all_values)

def update_sheet_with_data(wks, data):
    """Appends a list of rows to the sheet."""
    if data:
        wks.append_table(data)
        print(f"Successfully added {len(data)} new rows to the Google Sheet.")
