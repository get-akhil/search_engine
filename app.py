import subprocess
import json
import os
<<<<<<< HEAD
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
=======
import re # Import the standard regex module
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for all origins, allowing the front end on a different port (like 3360) to connect.
CORS(app)

PORT = 3000

# IMPORTANT: Set the path to your compiled C executable
# Assuming 'search_engine' is in the root directory where you run this server.
C_EXECUTABLE_PATH = os.path.join(os.getcwd(), 'search_engine')


# --- Root Route to Serve the Front End ---
>>>>>>> c3d1db25eea4b537c3d358c8557bc4632df15395
@app.route('/')
def serve_frontend():
    """Serves the index.html file when the user accesses the base URL."""
    try:
<<<<<<< HEAD
=======
        # We use send_file to return the index.html file directly.
        # This resolves the 'Not Found' error when accessing the base Codespaces URL.
>>>>>>> c3d1db25eea4b537c3d358c8557bc4632df15395
        return send_file('index.html')
    except Exception as e:
        return jsonify({"error": f"Failed to serve index.html: {e}"}), 500


<<<<<<< HEAD
# --- Route 3: Search API Endpoint (Modified) ---
=======
# --- Search API Endpoint ---
>>>>>>> c3d1db25eea4b537c3d358c8557bc4632df15395
@app.route('/api/search', methods=['GET'])
def search_api():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Missing search query parameter."}), 400

<<<<<<< HEAD
    safe_query = re.sub(r'[^a-zA-Z0-9\s]', '', query).strip()
    
    try:
=======
    # 1. Sanitize the query to prevent command injection
    # Use Python's 're' module for sanitization (Fixes previous SyntaxError)
    safe_query = re.sub(r'[^a-zA-Z0-9\s]', '', query).strip()

    # 2. Execute the C program
    # The command executes the C engine and passes the cleaned query as an argument.
    try:
        # We wrap the query in quotes so that the C program receives the full string 
        # as a single argument, which matches the expected usage (argv[1]).
>>>>>>> c3d1db25eea4b537c3d358c8557bc4632df15395
        result = subprocess.run(
            [C_EXECUTABLE_PATH, safe_query],
            capture_output=True,
            text=True,
<<<<<<< HEAD
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
=======
            check=True # Raise an exception for non-zero exit codes
        )
        stdout = result.stdout
        stderr = result.stderr

    except subprocess.CalledProcessError as e:
        # This catches errors where the C program crashed or exited with an error code
        print(f"C Program Execution Failed (Exit Code {e.returncode}): {e.stderr}")
        return jsonify({
            "error": "C search engine failed to execute.",
            "details": e.stderr.strip()
        }), 500
    except FileNotFoundError:
        return jsonify({"error": f"C executable not found at {C_EXECUTABLE_PATH}. Did you compile it?"}), 500


    if stderr:
        print(f"C Program STDERR (Warnings/Debug): {stderr.strip()}")
        # Often stderr contains non-fatal warnings; we proceed to parse stdout.

    try:
        # 3. Capture and parse the JSON output from the C program
        json_output = json.loads(stdout.strip())
        
        # Check if the C program returned an error message in JSON format (e.g., failed to open doc_sets)
        if isinstance(json_output, list) and json_output and json_output[0].get('error'):
             return jsonify(json_output[0]), 500

        # 4. Send the results back to the front end
        return jsonify(json_output)

    except json.JSONDecodeError:
        print("Failed to parse C output as JSON:", stdout)
        return jsonify({ 
            "error": "C program output was invalid. Ensure it returns a single JSON array.",
            "rawOutput": stdout.strip()
        }), 500


if __name__ == '__main__':
    # When running in Codespaces, the host '0.0.0.0' is required to listen on all interfaces.
>>>>>>> c3d1db25eea4b537c3d358c8557bc4632df15395
    app.run(host='0.0.0.0', port=PORT, debug=True)