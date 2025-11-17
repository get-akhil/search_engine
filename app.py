import subprocess
import json
import os
import re
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# --- Gemini API Configuration ---
# NOTE: The API key is left empty; the runtime environment will provide it.
GEMINI_API_KEY = "AIzaSyDMqxJoF_x-0wgUbFzLX4v3DyjflbRx3Ic" 
GEMINI_MODEL = "gemini-2.5-flash-preview-09-2025"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
# --------------------------------

app = Flask(__name__)
CORS(app)
PORT = 3000
C_EXECUTABLE_PATH = os.path.join(os.getcwd(), 'search_engine')
DOC_SETS_PATH = os.path.join(os.getcwd(), 'doc_sets')

# The categories list is maintained for clarity and the frontend dropdown
CATEGORIES_LIST = [
    "Animals", 
    "Art", 
    "Engineering", 
    "Food", 
    "Music", 
    "Famous_Landmarks"
]

def get_category_from_filename(filename):
    """
    Infers the category from the filename provided by the C engine.
    If format is 'Folder/file.txt', it returns 'Folder'.
    If format is 'file.txt' (old flat-structure engineering file), it returns 'Engineering'.
    """
    if '/' in filename:
        # For 'Animals/dog.txt', returns 'Animals'
        return filename.split('/')[0]
    
    # All old top-level documents are assumed to be "Engineering"
    if filename.endswith("_engg.txt") or filename in ["Text_Engg.txt", "iot_sub.txt", "ds_engg.txt", "ai.ml_engg.txt", "Petro_Engg.txt", "Mining_Engg.txt"]:
         return "Engineering"
         
    return "Unknown"


def _call_gemini_api(text_to_summarize):
    """Handles the POST request to the Gemini API for summarization."""
    system_prompt = "You are an expert technical document summarizer. Condense the following content into three concise, easy-to-read bullet points, focusing on the key topics and conclusions. Use an informative and professional tone."
    user_query = f"Summarize this document content: {text_to_summarize}"
    
    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
    }

    try:
        response = requests.post(
            GEMINI_API_URL,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload)
        )
        response.raise_for_status()
        
        result = response.json()
        
        generated_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'API failed to return text.')
        return generated_text

    except requests.exceptions.RequestException as e:
        print(f"Gemini API Request Failed: {e}")
        return f"Error: Failed to connect to summarization API. Details: {e}"
    except Exception as e:
        print(f"Gemini API Parsing Failed: {e}")
        return "Error: Could not parse API response."


# --- NEW FAST ROUTE: ONLY RETURNS RAW FILE CONTENT ---
@app.route('/api/document/content/<path:filename>', methods=['GET'])
def get_document_raw_content(filename):
    """Reads and returns only the raw content of a document instantly."""
    file_path = os.path.join(DOC_SETS_PATH, filename)
    
    if not os.path.exists(file_path):
        return jsonify({"error": f"Document file '{filename}' not found at path: {file_path}"}), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": f"Error reading document: {e}"}), 500

# --- NEW SLOW ROUTE: RETURNS ONLY LLM SUMMARY ---
@app.route('/api/document/summary/<path:filename>', methods=['GET'])
def get_document_summary(filename):
    """Reads content, calls the slow LLM API, and returns only the summary."""
    file_path = os.path.join(DOC_SETS_PATH, filename)
    
    if not os.path.exists(file_path):
        return jsonify({"error": f"Document file '{filename}' not found at path: {file_path}"}), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            summary = _call_gemini_api(content)
            return jsonify({"summary": summary})
    except Exception as e:
        return jsonify({"error": f"Error reading document for summary: {e}"}), 500


# --- Route 2: Base Route to Serve the Front End ---
@app.route('/')
def serve_frontend():
    """Serves the index.html file when the user accesses the base URL."""
    try:
        return send_file('index.html')
    except Exception as e:
        return jsonify({"error": f"Failed to serve index.html: {e}"}), 500


# --- Route 3: Search API Endpoint (Handles Browsing and Search Mode) ---
@app.route('/api/search', methods=['GET'])
def search_api():
    query = request.args.get('query', '').strip()
    category_filter = request.args.get('category', 'All') 
    
    # --- BROWSING MODE: If query is empty and a specific category is selected ---
    if not query and category_filter != 'All':
        filtered_files = []
        for entry in os.listdir(DOC_SETS_PATH):
            entry_path = os.path.join(DOC_SETS_PATH, entry)
            
            # Check for New Category Structure (Subdirectories)
            if os.path.isdir(entry_path) and entry == category_filter:
                for filename in os.listdir(entry_path):
                    if filename.endswith(".txt"):
                        full_filename = os.path.join(category_filter, filename)
                        # Score of 1 means it's just a file listing
                        filtered_files.append({"filename": full_filename, "score": 1}) 
                break

            # Check for Old Category Structure (Top-level Engineering files)
            elif os.path.isfile(entry_path) and entry.endswith(".txt"):
                doc_category = get_category_from_filename(entry)
                if doc_category == category_filter:
                    filtered_files.append({"filename": entry, "score": 1})
        
        return jsonify(filtered_files)

    if not query:
        return jsonify([]) # Query empty, Category 'All' -> return empty.


    # --- SEARCH MODE: Execute C engine ---

    safe_query = re.sub(r'[^a-zA-Z0-9\s]', '', query).strip()
    
    try:
        # 1. Call C executable to get raw search results
        result = subprocess.run(
            [C_EXECUTABLE_PATH, safe_query],
            capture_output=True,
            text=True,
            check=True
        )
        stdout = result.stdout
        
        json_output = json.loads(stdout.strip())
        
        if isinstance(json_output, list) and json_output and json_output[0].get('error'):
             return jsonify(json_output[0]), 500
        
        # 2. Filter the results based on the category (if a search is running)
        if category_filter != 'All':
            filtered_results = []
            
            for item in json_output:
                filename = item.get('filename')
                doc_category = get_category_from_filename(filename)
                
                if doc_category == category_filter:
                    filtered_results.append(item)
            
            return jsonify(filtered_results)

        return jsonify(json_output)

    except subprocess.CalledProcessError as e:
        print(f"C Program Execution Failed (Exit Code {e.returncode}): {e.stderr}")
        return jsonify({"error": f"C search engine failed to execute. Details: {e.stderr.strip()}"}), 500
    except FileNotFoundError:
        return jsonify({"error": f"C executable not found at {C_EXECUTABLE_PATH}. Did you compile it?"}), 500
    except json.JSONDecodeError:
        print("Failed to parse C output as JSON:", stdout)
        return jsonify({"error": "C program output was invalid. Ensure it returns a single JSON array.", "rawOutput": stdout.strip()}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)