from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '..', 'data', 'sections.json')
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend')

def load_sections():
    with open(DATA_PATH, 'r') as f:
        return json.load(f)

def find_matching_sections(complaint_text):
    sections = load_sections()
    complaint_lower = complaint_text.lower()
    matches = []
    for section in sections:
        for keyword in section['keywords']:
            if keyword.lower() in complaint_lower:
                if section not in matches:
                    matches.append(section)
                break
    return matches

# ── Serve Frontend ──
@app.route('/')
def serve_frontend():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)

# ── API Routes ──
@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json()
    if not data or 'complaint' not in data:
        return jsonify({"error": "Please provide a complaint text."}), 400

    complaint = data['complaint'].strip()
    if len(complaint) < 5:
        return jsonify({"error": "Complaint is too short. Please describe your situation."}), 400

    matches = find_matching_sections(complaint)

    if not matches:
        return jsonify({
            "complaint": complaint,
            "matches": [],
            "message": "No matching IPC/BNS sections found. Please consult a legal expert."
        })

    return jsonify({
        "complaint": complaint,
        "matches": [
            {
                "ipc": m["ipc"],
                "bns": m["bns"],
                "title": m["title"],
                "description": m["description"]
            }
            for m in matches
        ],
        "message": f"Found {len(matches)} matching legal section(s)."
    })

@app.route('/api/sections', methods=['GET'])
def get_all_sections():
    sections = load_sections()
    return jsonify({"sections": sections, "total": len(sections)})

if __name__ == '__main__':
    print("Starting LegalBridge Backend...")
    print("✅ Open your browser and go to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
