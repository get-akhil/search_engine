import subprocess
import json
import os
import re
import requests # Needed for external API calls
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# --- Gemini API Configuration ---
# NOTE: The API key is left empty; the runtime environment will provide it.
GEMINI_API_KEY = "" 
GEMINI_MODEL = "gemini-2.5-flash-preview-09-2025"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
# --------------------------------

app = Flask(__name__)
CORS(app)
PORT = 3000
C_EXECUTABLE_PATH = os.path.join(os.getcwd(), 'search_engine')
DOC_SETS_PATH = os.path.join(os.getcwd(), 'doc_sets')


def _call_gemini_api(text_to_summarize):
    """Handles the POST request to the Gemini API for summarization."""
    # System instruction guiding the model to act as a summarizer
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
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        result = response.json()
        
        # Extract the generated text
        generated_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'API failed to return text.')
        return generated_text

    except requests.exceptions.RequestException as e:
        print(f"Gemini API Request Failed: {e}")
        return f"Error: Failed to connect to summarization API. Details: {e}"
    except Exception as e:
        print(f"Gemini API Parsing Failed: {e}")
        return "Error: Could not parse API response."


# --- Route 1: Serve Document Content (New) ---
@app.route('/api/document/<filename>', methods=['GET'])
def get_document_content(filename):
    """Reads and returns the content of a document from doc_sets."""
    file_path = os.path.join(DOC_SETS_PATH, filename)
    
    if not os.path.exists(file_path):
        return jsonify({"error": f"Document file '{filename}' not found."}), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Summarize the document content using the Gemini API
            summary = _call_gemini_api(content)

            return jsonify({
                "filename": filename,
                "content": content,
                "summary": summary
            })
    except Exception as e:
        return jsonify({"error": f"Error reading document: {e}"}), 500


# --- Route 2: Base Route to Serve the Front End ---
@app.route('/')
def serve_frontend():
    """Serves the index.html file when the user accesses the base URL."""
    try:
        return send_file('index.html')
    except Exception as e:
        return jsonify({"error": f"Failed to serve index.html: {e}"}), 500


# --- Route 3: Search API Endpoint (Modified) ---
@app.route('/api/search', methods=['GET'])
def search_api():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Missing search query parameter."}), 400

    safe_query = re.sub(r'[^a-zA-Z0-9\s]', '', query).strip()
    
    try:
        result = subprocess.run(
            [C_EXECUTABLE_PATH, safe_query],
            capture_output=True,
            text=True,
            check=True
        )
        stdout = result.stdout
        # ... (rest of the error handling and JSON parsing remains the same) ...
        
        json_output = json.loads(stdout.strip())
        
        if isinstance(json_output, list) and json_output and json_output[0].get('error'):
             return jsonify(json_output[0]), 500

        return jsonify(json_output)

    except subprocess.CalledProcessError as e:
        print(f"C Program Execution Failed (Exit Code {e.returncode}): {e.stderr}")
        return jsonify({"error": "C search engine failed to execute.", "details": e.stderr.strip()}), 500
    except FileNotFoundError:
        return jsonify({"error": f"C executable not found at {C_EXECUTABLE_PATH}. Did you compile it?"}), 500
    except json.JSONDecodeError:
        print("Failed to parse C output as JSON:", stdout)
        return jsonify({"error": "C program output was invalid. Ensure it returns a single JSON array.", "rawOutput": stdout.strip()}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)