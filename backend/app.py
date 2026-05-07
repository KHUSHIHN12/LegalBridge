from flask import Flask, request, jsonify, session
from prometheus_client import Counter, generate_latest
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
import json
import os
import sqlite3


app = Flask(__name__)

REQUEST_COUNT = Counter(
    "app_requests_total",
    "Total App HTTP Request Count"
)

# -----------------------------
# Flask Configuration
# -----------------------------
app.secret_key = os.environ.get(
    "LEGALBRIDGE_SECRET_KEY",
    "legalbridge-dev-secret-key"
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
)

# -----------------------------
# CORS Configuration
# -----------------------------
CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "null",
    ],
)

# -----------------------------
# Database Setup
# -----------------------------
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

# -----------------------------
# Load Legal Data
# -----------------------------
with open(os.path.join(base_dir, "../data/sections.json"), encoding="utf-8") as f:
    data = json.load(f)

ipc_sections = data["ipc_sections"]
bns_sections = data["bns_sections"]
ipc_to_bns = data["ipc_to_bns"]
bns_to_ipc = data["bns_to_ipc"]


# -----------------------------
# Helper Functions
# -----------------------------
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


# -----------------------------
# Home Route
# -----------------------------
@app.route("/")
def home():
    REQUEST_COUNT.inc()
    return "LegalBridge Backend Running ✅"


# -----------------------------
# Prometheus Metrics Endpoint
# -----------------------------
@app.route("/metrics")
def metrics():
    REQUEST_COUNT.inc()
    return generate_latest(), 200, {
        "Content-Type": "text/plain"
    }


# -----------------------------
# Signup API
# -----------------------------
@app.route("/api/signup", methods=["POST"])
def signup():
    REQUEST_COUNT.inc()

    body = request.get_json(silent=True) or {}

    fullname = (body.get("fullname") or "").strip()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not fullname or not email or not password:
        return jsonify({
            "success": False,
            "message": "Full name, email, and password are required."
        }), 400

    password_hash = generate_password_hash(password)

    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO users (fullname, email, password) VALUES (?, ?, ?)",
                (fullname, email, password_hash),
            )
            conn.commit()

    except sqlite3.IntegrityError:
        return jsonify({
            "success": False,
            "message": "A user with this email already exists."
        }), 409

    return jsonify({
        "success": True,
        "message": "Account created successfully."
    }), 201


# -----------------------------
# Login API
# -----------------------------
@app.route("/api/login", methods=["POST"])
def login():
    REQUEST_COUNT.inc()

    body = request.get_json(silent=True) or {}

    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400

    with get_db_connection() as conn:
        user = conn.execute(
            "SELECT id, fullname, email, password FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if not user or not check_password_hash(user["password"], password):
        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    session["logged_in"] = True
    session["user_id"] = user["id"]
    session["fullname"] = user["fullname"]
    session["email"] = user["email"]

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "user": {
            "id": user["id"],
            "fullname": user["fullname"],
            "email": user["email"],
        },
    })


# -----------------------------
# Session Check API
# -----------------------------
@app.route("/api/check-session", methods=["GET"])
def check_session():
    REQUEST_COUNT.inc()

    if session.get("logged_in"):
        return jsonify({
            "logged_in": True,
            "user": {
                "id": session.get("user_id"),
                "fullname": session.get("fullname"),
                "email": session.get("email"),
            }
        })

    return jsonify({
        "logged_in": False
    }), 401


# -----------------------------
# Logout API
# -----------------------------
@app.route("/api/logout", methods=["POST"])
def logout():
    REQUEST_COUNT.inc()

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    })


# -----------------------------
# IPC -> BNS Mapping API
# -----------------------------
@app.route("/api/mapping/ipc-to-bns", methods=["POST"])
def ipc_to_bns_mapping():
    REQUEST_COUNT.inc()

    body = request.get_json(silent=True) or {}

    ipc_section = body.get("ipc_section")

    mappings = ipc_to_bns.get(ipc_section, [])

    return jsonify({
        "ipc_section": ipc_section,
        "bns_mappings": mappings
    })


# -----------------------------
# BNS -> IPC Mapping API
# -----------------------------
@app.route("/api/mapping/bns-to-ipc", methods=["POST"])
def bns_to_ipc_mapping():
    REQUEST_COUNT.inc()

    body = request.get_json(silent=True) or {}

    bns_section = body.get("bns_section")

    mappings = bns_to_ipc.get(bns_section, [])

    return jsonify({
        "bns_section": bns_section,
        "ipc_mappings": mappings
    })


# -----------------------------
# Search Sections API
# -----------------------------
@app.route("/api/sections/search", methods=["GET"])
def search_sections():
    REQUEST_COUNT.inc()

    query = request.args.get("q", "").lower()

    results = []

    for section, details in ipc_sections.items():
        if query in details.get("title", "").lower():
            results.append({
                "law": "IPC",
                "section": section,
                "title": details.get("title")
            })

    for section, details in bns_sections.items():
        if query in details.get("title", "").lower():
            results.append({
                "law": "BNS",
                "section": section,
                "title": details.get("title")
            })

    return jsonify({
        "results": results
    })



@app.route("/analyze", methods=["POST"])
def analyze():
    REQUEST_COUNT.inc()

    body = request.get_json(silent=True) or {}

    text = body.get("text", "")
    date = body.get("date", "")

    ipc_num = predict_section(text)

    if not ipc_num or ipc_num not in ipc_sections:
        return jsonify({
            "error": "No matching section found for the given complaint."
        }), 404

    ipc_info = ipc_sections[ipc_num]
    bns_equivalents = ipc_to_bns.get(ipc_num, [])

    bns_details = []

    for bns in bns_equivalents:
        if bns in bns_sections:
            bns_details.append({
                "section": bns,
                "title": bns_sections[bns]["title"]
            })

    law = "IPC" if date < "2024-07-01" else "BNS"

    return jsonify({
        "complaint": text,
        "ipc_section": ipc_num,
        "ipc_title": ipc_info["title"],
        "bns_equivalents": bns_details,
        "applicable_law": law,
        "note": (
            "Incident before July 1, 2024 → charged under IPC."
            if law == "IPC"
            else "Incident on/after July 1, 2024 → charged under BNS."
        )
    })


# -----------------------------
# Run Flask App
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)