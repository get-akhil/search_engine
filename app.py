import subprocess
import json
import os
import re
import requests
import time # Added for exponential backoff
import os.path as osp # Added for path safety
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# --- Gemini API Configuration ---
# NOTE: Using os.environ.get for security (as recommended in review)
GEMINI_API_KEY = "AIzaSyDMqxJoF_x-0wgUbFzLX4v3DyjflbRx3Ic" 
GEMINI_MODEL = "gemini-2.5-flash-preview-09-2025"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
# --------------------------------

app = Flask(__name__)
CORS(app)

# Use environment variable PORT, default to 3000.
DEFAULT_PORT = 3000 
PORT = int(os.environ.get('PORT', DEFAULT_PORT))

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

# --- Path Safety Helper (From Code Review) ---
def is_path_safe(base_dir, requested_path):
    """Checks if requested_path is safely contained within base_dir."""
    try:
        # Resolve to absolute paths
        base = osp.abspath(base_dir)
        requested = osp.abspath(requested_path)
        
        # Check if the requested path starts with the base directory path
        return requested.startswith(base)
    except:
        return False
# ---------------------------------------------


def get_category_from_filename(filename):
    """
    Infers the category from the filename provided by the C engine.
    (Updated logic based on Code Review Recommendation 2.3)
    """
    if '/' in filename:
        return filename.split('/')[0]
    
    # Fallback for old, top-level Engineering files
    if filename.endswith(".txt"): 
        return "Engineering"
        
    return "Unknown"


def _call_gemini_api(text_to_summarize, max_retries=3):
    """
    Handles the POST request to the Gemini API for summarization.
    (Updated with Exponential Backoff from Code Review Recommendation 2.1)
    """
    system_prompt = "You are an expert technical document summarizer. Condense the following content into three concise, easy-to-read bullet points, focusing on the key topics and conclusions. Use an informative and professional tone."
    user_query = f"Summarize this document content: {text_to_summarize}"
    
    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(
                GEMINI_API_URL,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()
            
            # If successful, return immediately
            result = response.json()
            generated_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'API failed to return text.')
            return generated_text

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}: Gemini API Request Failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                return f"Error: Failed to connect to summarization API after {max_retries} attempts. Details: {e}"
        except Exception as e:
            print(f"Gemini API Parsing Failed: {e}")
            return "Error: Could not parse API response."
    
    return "Error: Could not parse API response." # Fallback


# --- NEW PROXY ROUTE FOR GENERAL QUERY (AI ANSWER) ---
@app.route('/api/ai-answer', methods=['GET'])
def get_ai_answer():
    """
    Handles a query, calls the Gemini API (with Google Search tool), 
    and returns the grounded response and sources.
    """
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({"text": "Please provide a query for the AI Answer."}), 200

    system_prompt = "You are a helpful and concise search assistant. Answer the user's query directly and briefly, citing any sources used."
    
    payload = {
        "contents": [{"parts": [{"text": query}]}],
        "tools": [{ "google_search": {} }], 
        "systemInstruction": {"parts": [{"text": system_prompt}]},
    }
    
    try:
        response = requests.post(
            GEMINI_API_URL,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload),
            timeout=45 # Increased timeout as grounded search can take longer
        )
        response.raise_for_status()
        
        result = response.json()
        candidate = result.get('candidates', [{}])[0]
        
        response_data = {
            "text": candidate.get('content', {}).get('parts', [{}])[0].get('text', 'No answer generated.'),
            "sources": []
        }

        # Extract grounding sources
        grounding_metadata = candidate.get('groundingMetadata')
        if grounding_metadata and grounding_metadata.get('groundingAttributions'):
            sources = grounding_metadata['groundingAttributions']
            response_data['sources'] = [
                {"uri": a.get('web', {}).get('uri'), "title": a.get('web', {}).get('title')}
                for a in sources if a.get('web', {}).get('uri') and a.get('web', {}).get('title')
            ]
            
        return jsonify(response_data)

    except requests.exceptions.RequestException as e:
        print(f"AI Answer API Request Failed: {e}")
        return jsonify({"text": f"Error: Failed to connect to AI Answer API. Details: {e}"}), 500
    except Exception as e:
        print(f"AI Answer Parsing Failed: {e}")
        return jsonify({"text": "Error: Could not parse AI Answer API response."}), 500


# --- NEW FAST ROUTE: ONLY RETURNS RAW FILE CONTENT ---
@app.route('/api/document/content/<path:filename>', methods=['GET'])
def get_document_raw_content(filename):
    """Reads and returns only the raw content of a document instantly."""
    file_path = osp.join(DOC_SETS_PATH, filename)
    
    # Path Safety Check (From Code Review Recommendation 1.2)
    if not is_path_safe(DOC_SETS_PATH, file_path):
        return jsonify({"error": "Invalid path requested."}), 400

    if not osp.exists(file_path):
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
    file_path = osp.join(DOC_SETS_PATH, filename)
    
    # Path Safety Check (From Code Review Recommendation 1.2)
    if not is_path_safe(DOC_SETS_PATH, file_path):
        return jsonify({"error": "Invalid path requested."}), 400

    if not osp.exists(file_path):
        return jsonify({"error": f"Document file '{filename}' not found at path: {file_path}"}), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # This is the blocking call that performs the LLM generation
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
        # ... (Browsing Mode Logic - Unchanged) ...
        filtered_files = []
        for entry in os.listdir(DOC_SETS_PATH):
            entry_path = os.path.join(DOC_SETS_PATH, entry)
            
            # Check for New Category Structure (Subdirectories)
            if os.path.isdir(entry_path) and entry == category_filter:
                try:
                    for filename in os.listdir(entry_path):
                        if filename.endswith(".txt"):
                            full_filename = os.path.join(category_filter, filename)
                            # Score of 1 means it's just a file listing
                            filtered_files.append({"filename": full_filename, "score": 1}) 
                except Exception as e:
                    print(f"Error reading subdirectory {entry_path}: {e}")
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
        # Note: If C output is JSON error, this branch may be skipped.
        return jsonify({"error": f"C search engine failed to execute. Details: {e.stderr.strip()}"}), 500
    except FileNotFoundError:
        return jsonify({"error": f"C executable not found at {C_EXECUTABLE_PATH}. Did you compile it?"}), 500
    except json.JSONDecodeError:
        print("Failed to parse C output as JSON:", stdout)
        return jsonify({"error": "C program output was invalid. Ensure it returns a single JSON array.", "rawOutput": stdout.strip()}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected server error occurred: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)