from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
import json
import os
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get("LEGALBRIDGE_SECRET_KEY", "legalbridge-dev-secret-key")
CORS(app, supports_credentials=True)

base_dir = os.path.dirname(__file__)
db_path = os.path.join(base_dir, "users.db")


def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_user_db():
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fullname TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


init_user_db()

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

@app.route("/api/signup", methods=["POST"])
def signup():
    body = request.get_json(silent=True) or {}
    fullname = (body.get("fullname") or "").strip()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not fullname or not email or not password:
        return jsonify({"success": False, "message": "Full name, email, and password are required."}), 400

    password_hash = generate_password_hash(password)

    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO users (fullname, email, password) VALUES (?, ?, ?)",
                (fullname, email, password_hash),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "A user with this email already exists."}), 409

    return jsonify({"success": True, "message": "Account created successfully."}), 201


@app.route("/api/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    with get_db_connection() as conn:
        user = conn.execute(
            "SELECT id, fullname, email, password FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if not user or not check_password_hash(user["password"], password):
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    session["logged_in"] = True
    session["user_id"] = user["id"]
    session["fullname"] = user["fullname"]
    session["email"] = user["email"]

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "user": {
            "id": user["id"],
            "fullName": user["fullname"],
            "email": user["email"],
        },
    })


@app.route("/api/check-session", methods=["GET"])
def check_session():
    if not session.get("logged_in"):
        return jsonify({"authenticated": False}), 401

    return jsonify({
        "authenticated": True,
        "user": {
            "id": session.get("user_id"),
            "fullName": session.get("fullname"),
            "email": session.get("email"),
        },
    })


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully."})


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
