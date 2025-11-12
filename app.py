import os
import json
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS # Used to allow web page (index.html) to communicate with the server

app = Flask(__name__)
# Enable CORS for all routes, allowing your local index.html or GitHub Pages
# to fetch data from this local server.
CORS(app) 

# IMPORTANT: Set the path to your compiled C executable
# Assuming 'search_engine' is in the root directory where you run this server.
C_EXECUTABLE_PATH = os.path.join(os.path.dirname(__file__), 'search_engine')

@app.route('/api/search', methods=['GET'])
def search_endpoint():
    """
    Handles search requests from the front-end, executes the C search engine,
    and returns the JSON results.
    """
    query = request.args.get('query')
    
    if not query:
        return jsonify({"error": "Missing search query parameter."}), 400

    # 1. Sanitize the query
    # Simple sanitization to strip non-alphanumeric/non-space characters
    safe_query = ''.join(filter(lambda x: x.isalnum() or x.isspace(), query)).strip()

    if not safe_query:
         return jsonify({"error": "Query contains only invalid characters or stop words."}), 400

    # 2. Execute the C program
    # The command executes the C engine and passes the cleaned query as an argument.
    # We use shlex.quote to handle spaces in the query safely.
    command = [C_EXECUTABLE_PATH, safe_query]

    try:
        # Use subprocess.run to execute the C program and capture its output
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True, # Raise an error if the C program returns a non-zero exit code
            encoding='utf-8'
        )
        
        stdout_output = result.stdout.strip()

        # 3. Capture and parse the JSON output from the C program
        if not stdout_output:
            # If the C program returned nothing (e.g., no results found)
            return jsonify([])

        json_output = json.loads(stdout_output)

        # 4. Check if the C program returned an error message in JSON format
        if isinstance(json_output, list) and len(json_output) > 0 and 'error' in json_output[0]:
             # Return C-side error (e.g., failed to open doc_sets folder)
             return jsonify(json_output[0]), 500

        # 5. Send the results back to the front end
        return jsonify(json_output)

    except subprocess.CalledProcessError as e:
        # This catches errors if the C program execution fails (non-zero exit code)
        print(f"C Program Execution Failed. STDERR: {e.stderr}")
        return jsonify({"error": "Failed to execute C search engine program.", "details": e.stderr}), 500
    
    except json.JSONDecodeError:
        # This catches errors if the C program output is not valid JSON
        print(f"Failed to parse C output as JSON: {stdout_output}")
        return jsonify({ 
            "error": "C program output was invalid. Ensure it returns a single JSON array.",
            "rawOutput": stdout_output
        }), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "Internal server error."}), 500

if __name__ == '__main__':
    # Flask runs on port 3000, matching the front-end configuration
    # Binding to 0.0.0.0 ensures it listens on all interfaces, often resolving local connectivity issues.
    app.run(debug=True, host='0.0.0.0', port=3000)