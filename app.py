import subprocess
import json
import os
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
@app.route('/')
def serve_frontend():
    """Serves the index.html file when the user accesses the base URL."""
    try:
        # We use send_file to return the index.html file directly.
        # This resolves the 'Not Found' error when accessing the base Codespaces URL.
        return send_file('index.html')
    except Exception as e:
        return jsonify({"error": f"Failed to serve index.html: {e}"}), 500


# --- Search API Endpoint ---
@app.route('/api/search', methods=['GET'])
def search_api():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Missing search query parameter."}), 400

    # 1. Sanitize the query to prevent command injection
    # Use Python's 're' module for sanitization (Fixes previous SyntaxError)
    safe_query = re.sub(r'[^a-zA-Z0-9\s]', '', query).strip()

    # 2. Execute the C program
    # The command executes the C engine and passes the cleaned query as an argument.
    try:
        # We wrap the query in quotes so that the C program receives the full string 
        # as a single argument, which matches the expected usage (argv[1]).
        result = subprocess.run(
            [C_EXECUTABLE_PATH, safe_query],
            capture_output=True,
            text=True,
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
    app.run(host='0.0.0.0', port=PORT, debug=True)