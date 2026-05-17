from flask import Flask, jsonify, request, session
from flask_cors import CORS
from prometheus_client import Counter, generate_latest
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

import hvac
import json
import os
import time
from datetime import datetime, timezone

from search_engine import LegalSearchEngine


load_dotenv()

VAULT_SECRET_KEYS = ("SECRET_KEY", "JWT_SECRET", "FLASK_ENV", "DEBUG")
VAULT_SECRET_PATH = "legalbridge/config"
VAULT_MOUNT_POINT = "secret"


def str_to_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def load_vault_secrets():
    vault_addr = os.getenv("VAULT_ADDR")
    vault_token = os.getenv("VAULT_TOKEN")

    if not vault_addr or not vault_token:
        print("Vault unavailable, using environment fallback")
        return {}

    for attempt in range(1, 6):
        try:
            client = hvac.Client(url=vault_addr, token=vault_token, timeout=3)

            if not client.is_authenticated():
                print("Vault unavailable, using environment fallback")
                return {}

            response = client.secrets.kv.v2.read_secret_version(
                mount_point=VAULT_MOUNT_POINT,
                path=VAULT_SECRET_PATH,
            )
            vault_data = response.get("data", {}).get("data", {})
            loaded_secrets = {
                key: str(vault_data[key])
                for key in VAULT_SECRET_KEYS
                if vault_data.get(key) is not None
            }

            if loaded_secrets:
                for key, value in loaded_secrets.items():
                    os.environ[key] = value
                print("Vault secrets loaded successfully")
                return loaded_secrets

            print("Vault unavailable, using environment fallback")
            return {}

        except Exception:
            if attempt == 5:
                print("Vault unavailable, using environment fallback")
                return {}
            time.sleep(2)

    print("Vault unavailable, using environment fallback")
    return {}


def get_secret(name, legacy_name=None, default=None):
    return os.getenv(name) or (os.getenv(legacy_name) if legacy_name else None) or default


def create_app():
    load_vault_secrets()

    app = Flask(__name__)

    flask_env = os.getenv("FLASK_ENV", "development").strip().lower()
    debug_enabled = str_to_bool(os.getenv("DEBUG"), default=flask_env == "development")
    secret_key = get_secret("SECRET_KEY", legacy_name="LEGALBRIDGE_SECRET_KEY")
    jwt_secret = get_secret("JWT_SECRET")

    if flask_env == "production":
        missing = [
            name
            for name, value in {
                "SECRET_KEY": secret_key,
                "JWT_SECRET": jwt_secret,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Missing required production secret(s): "
                + ", ".join(missing)
                + ". Set them in .env, Docker, or GitHub Secrets."
            )

    app.config.update(
        SECRET_KEY=secret_key or "dev-only-change-this-secret-key",
        JWT_SECRET=jwt_secret or "dev-only-change-this-jwt-secret",
        FLASK_ENV=flask_env,
        DEBUG=debug_enabled,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=flask_env == "production",
    )

    register_extensions(app)
    register_routes(app)
    return app


def register_extensions(app):
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


REQUEST_COUNT = Counter(
    "app_requests_total",
    "Total LegalBridge HTTP request count",
)

BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "../data/sections.json")
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "legalbridge")
MONGODB_USERS_COLLECTION = os.getenv("MONGODB_USERS_COLLECTION", "users")


if not MONGODB_URI:
    raise RuntimeError(
        "Missing MONGODB_URI. Set your MongoDB Atlas connection string in .env, "
        "Docker, or your deployment environment."
    )


mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
mongo_db = mongo_client[MONGODB_DB_NAME]
users_collection = mongo_db[MONGODB_USERS_COLLECTION]


def init_user_store():
    users_collection.create_index("email", unique=True)


def load_legal_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


init_user_store()
legal_data = load_legal_data()
ipc_sections = legal_data["ipc_sections"]
bns_sections = legal_data["bns_sections"]
ipc_to_bns = legal_data["ipc_to_bns"]
bns_to_ipc = legal_data["bns_to_ipc"]
legal_search_engine = LegalSearchEngine(ipc_sections, bns_sections)


def build_section_payload(law, section_number, section_data):
    return {
        "law": law,
        "section": section_number,
        "title": section_data.get("title", f"Section {section_number}"),
        "description": section_data.get("description", ""),
    }


def predict_section(text):
    text = (text or "").lower()

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


def register_routes(app):
    @app.route("/")
    def home():
        REQUEST_COUNT.inc()
        return "LegalBridge Backend Running"

    @app.route("/metrics")
    def metrics():
        REQUEST_COUNT.inc()
        return generate_latest(), 200, {"Content-Type": "text/plain"}

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
                "message": "Full name, email, and password are required.",
            }), 400

        password_hash = generate_password_hash(password)

        try:
            users_collection.insert_one({
                "fullname": fullname,
                "email": email,
                "password": password_hash,
                "created_at": datetime.now(timezone.utc),
            })
        except DuplicateKeyError:
            return jsonify({
                "success": False,
                "message": "A user with this email already exists.",
            }), 409

        return jsonify({
            "success": True,
            "message": "Account created successfully.",
        }), 201

    @app.route("/api/login", methods=["POST"])
    def login():
        REQUEST_COUNT.inc()
        body = request.get_json(silent=True) or {}

        email = (body.get("email") or "").strip().lower()
        password = body.get("password") or ""

        if not email or not password:
            return jsonify({
                "success": False,
                "message": "Email and password are required.",
            }), 400

        user = users_collection.find_one({"email": email})

        if not user or not check_password_hash(user["password"], password):
            return jsonify({
                "success": False,
                "message": "Invalid email or password.",
            }), 401

        session["logged_in"] = True
        session["user_id"] = str(user["_id"])
        session["fullname"] = user["fullname"]
        session["email"] = user["email"]

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "user": {
                "id": str(user["_id"]),
                "fullName": user["fullname"],
                "email": user["email"],
            },
        })

    @app.route("/api/check-session", methods=["GET"])
    def check_session():
        REQUEST_COUNT.inc()

        if not session.get("logged_in"):
            return jsonify({
                "authenticated": False,
                "success": False,
            }), 401

        return jsonify({
            "authenticated": True,
            "success": True,
            "user": {
                "id": session.get("user_id"),
                "fullName": session.get("fullname"),
                "email": session.get("email"),
            },
        })

    @app.route("/api/logout", methods=["POST"])
    def logout():
        REQUEST_COUNT.inc()
        session.clear()
        return jsonify({
            "success": True,
            "message": "Logged out successfully.",
        })

    @app.route("/api/mapping/ipc-to-bns", methods=["POST"])
    def map_ipc_to_bns():
        REQUEST_COUNT.inc()
        body = request.get_json(silent=True) or {}
        ipc_num = str(
            body.get("ipc_section")
            or body.get("section")
            or ""
        ).strip().upper()

        if not ipc_num:
            return jsonify({
                "success": False,
                "message": "IPC section is required.",
            }), 400

        ipc_info = ipc_sections.get(ipc_num) or ipc_sections.get(ipc_num.lower())
        if not ipc_info:
            return jsonify({
                "success": False,
                "message": f"IPC section {ipc_num} not found.",
            }), 404

        mapped_numbers = (
            ipc_to_bns.get(ipc_num)
            or ipc_to_bns.get(ipc_num.lower())
            or []
        )
        bns_equivalents = [
            build_section_payload("BNS", bns_num, bns_sections[bns_num])
            for bns_num in mapped_numbers
            if bns_num in bns_sections
        ]

        return jsonify({
            "success": True,
            "status": "success",
            "mapping_type": "ipc_to_bns",
            "ipc_section": build_section_payload("IPC", ipc_num, ipc_info),
            "bns_equivalents": bns_equivalents,
        })

    @app.route("/api/mapping/bns-to-ipc", methods=["POST"])
    def map_bns_to_ipc():
        REQUEST_COUNT.inc()
        body = request.get_json(silent=True) or {}
        bns_num = str(
            body.get("bns_section")
            or body.get("section")
            or ""
        ).strip()

        if not bns_num:
            return jsonify({
                "success": False,
                "message": "BNS section is required.",
            }), 400

        bns_info = bns_sections.get(bns_num)
        if not bns_info:
            return jsonify({
                "success": False,
                "message": f"BNS section {bns_num} not found.",
            }), 404

        mapped_numbers = bns_to_ipc.get(bns_num) or []
        ipc_equivalents = [
            build_section_payload("IPC", ipc_num, ipc_sections[ipc_num])
            for ipc_num in mapped_numbers
            if ipc_num in ipc_sections
        ]

        return jsonify({
            "success": True,
            "status": "success",
            "mapping_type": "bns_to_ipc",
            "bns_section": build_section_payload("BNS", bns_num, bns_info),
            "ipc_equivalents": ipc_equivalents,
        })

    @app.route("/api/sections/search", methods=["GET"])
    def search_sections():
        REQUEST_COUNT.inc()
        query = (request.args.get("q") or "").strip()
        law_filter = (request.args.get("law") or "all").strip().lower()

        try:
            limit = min(max(int(request.args.get("limit", 20)), 1), 100)
        except ValueError:
            limit = 20

        if law_filter not in ("all", "ipc", "bns"):
            return jsonify({
                "success": False,
                "message": "law must be one of all, ipc, or bns.",
            }), 400

        results = legal_search_engine.search(
            query=query,
            law=law_filter,
            limit=limit,
        )

        return jsonify({
            "success": True,
            "status": "success",
            "query": query,
            "law": law_filter,
            "count": len(results),
            "results": results,
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
                "success": False,
                "error": "No matching section found for the given complaint.",
            }), 404

        ipc_info = ipc_sections[ipc_num]
        bns_equivalents = ipc_to_bns.get(ipc_num, [])
        bns_details = []

        for bns_num in bns_equivalents:
            if bns_num in bns_sections:
                bns_details.append({
                    "section": bns_num,
                    "title": bns_sections[bns_num]["title"],
                })

        law = "IPC" if date < "2024-07-01" else "BNS"

        return jsonify({
            "success": True,
            "complaint": text,
            "ipc_section": ipc_num,
            "ipc_title": ipc_info["title"],
            "bns_equivalents": bns_details,
            "applicable_law": law,
            "note": (
                "Incident before July 1, 2024 charged under IPC."
                if law == "IPC"
                else "Incident on/after July 1, 2024 charged under BNS."
            ),
        })


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=app.config["DEBUG"],
    )
