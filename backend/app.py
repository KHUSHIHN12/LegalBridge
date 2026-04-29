#test change 
from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os

app = Flask(__name__)
CORS(app)

base_dir = os.path.dirname(__file__)
with open(os.path.join(base_dir, "../data/sections.json")) as f:
    data = json.load(f)

ipc_sections = data["ipc_sections"]
bns_sections = data["bns_sections"]
ipc_to_bns = data["ipc_to_bns"]
bns_to_ipc = data["bns_to_ipc"]

def predict_section(text):
    text = text.lower()
    if "murder" in text or "kill" in text:
        return "302"
    if "theft" in text or "steal" in text or "snatch" in text:
        return "379"
    if "cheat" in text or "fraud" in text:
        return "420"
    if "threat" in text or "blackmail" in text or "intimidat" in text:
        return "506"
    if "rape" in text or "sexual assault" in text:
        return "376"
    if "dowry" in text:
        return "304B"
    if "kidnap" in text or "abduct" in text:
        return "364"
    if "hurt" in text or "assault" in text or "attack" in text:
        return "323"
    return None
    
@app.route("/")
def home():
    return "LegalBridge Backend Running ✅"

@app.route("/analyze", methods=["POST"])
def analyze():
    body = request.json
    text = body.get("text", "")
    date = body.get("date", "")

    ipc_num = predict_section(text)

    if not ipc_num or ipc_num not in ipc_sections:
        return jsonify({"error": "No matching section found for the given complaint."})

    ipc_info = ipc_sections[ipc_num]
    bns_equivalents = ipc_to_bns.get(ipc_num, [])

    bns_details = []
    for b in bns_equivalents:
        if b in bns_sections:
            bns_details.append({
                "section": b,
                "title": bns_sections[b]["title"]
            })

    law = "IPC" if date < "2024-07-01" else "BNS"

    return jsonify({
        "complaint": text,
        "ipc_section": ipc_num,
        "ipc_title": ipc_info["title"],
        "bns_equivalents": bns_details,
        "applicable_law": law,
        "note": f"Incident before July 1, 2024 → charged under IPC. After → charged under BNS." if law == "IPC" else f"Incident on/after July 1, 2024 → charged under BNS."
    })

if __name__ == "__main__":
    app.run(debug=True)