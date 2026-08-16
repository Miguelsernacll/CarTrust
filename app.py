import csv
import json
import os
import re
import secrets
import sqlite3
import time
import unicodedata
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from uuid import uuid4

import requests
from dotenv import load_dotenv
from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, send_file, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "instance" / "cartrust.sqlite3"))
if not DB_PATH.is_absolute():
    DB_PATH = BASE_DIR / DB_PATH
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
ALLOWED_IMAGES = {"jpg", "jpeg", "png", "webp", "gif"}
USER_ROLES = {"customer", "dealer", "insurer"}
ROLE_LABELS = {
    "customer": "Particular",
    "dealer": "Concesionario",
    "insurer": "Aseguradora",
}
PAYMENT_METHODS = [
    ("pse", "PSE desde cuenta bancaria colombiana"),
    ("card", "Tarjeta credito o debito tokenizada"),
    ("nequi", "Nequi"),
    ("daviplata", "DaviPlata"),
    ("bancolombia", "Boton Bancolombia"),
    ("bank_transfer", "Transferencia bancaria online"),
]
BUSINESS_ROLES = {"dealer", "insurer"}
VERIFICATION_LABELS = {
    "verified": "Verificado",
    "pending_review": "En revision legal",
    "rejected": "Requiere ajuste",
}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-cartrust-change-me")
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
if os.getenv("SESSION_COOKIE_SECURE", "").lower() in {"1", "true", "yes"}:
    app.config["SESSION_COOKIE_SECURE"] = True

_station_cache = {}


def compute_asset_version():
    if os.getenv("ASSET_VERSION"):
        return os.getenv("ASSET_VERSION")
    files = [
        BASE_DIR / "static" / "css" / "styles.css",
        BASE_DIR / "static" / "js" / "app.js",
    ]
    mtimes = [path.stat().st_mtime for path in files if path.exists()]
    return str(int(max(mtimes))) if mtimes else str(int(time.time()))


ASSET_VERSION = compute_asset_version()


def utc_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def money(value):
    return "Consultar" if value in (None, "") else "$" + f"{int(value):,}".replace(",", ".")


def number(value):
    return "-" if value in (None, "") else f"{int(value):,}".replace(",", ".")


def parse_int(value, default=None):
    if value in (None, ""):
        return default
    digits = re.sub(r"[^\d]", "", str(value))
    return int(digits) if digits else default


def clean_text(value):
    return (value or "").strip()


def clean_identifier(value):
    return re.sub(r"[^0-9A-Za-z-]", "", clean_text(value))


def normalize_key(value):
    plain = unicodedata.normalize("NFKD", clean_text(value))
    return plain.encode("ascii", "ignore").decode("ascii").lower()


app.jinja_env.filters["money"] = money
app.jinja_env.filters["number"] = number


def db():
    if "db" not in g:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    conn = g.pop("db", None)
    if conn:
        conn.close()


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


@app.before_request
def protect_form_posts():
    if request.method != "POST" or request.path.startswith("/api/"):
        return
    if request.form.get("_csrf_token") != session.get("_csrf_token"):
        abort(400)


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    else:
        response.headers.setdefault("Cache-Control", "no-cache")
    return response


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


@app.context_processor
def inject_globals():
    return {
        "current_user": current_user(),
        "role_labels": ROLE_LABELS,
        "verification_labels": VERIFICATION_LABELS,
        "payment_methods": PAYMENT_METHODS,
        "csrf_token": csrf_token,
        "asset_version": ASSET_VERSION,
    }


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Entra o crea una cuenta para continuar.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Entra o crea una cuenta para continuar.", "error")
                return redirect(url_for("login", next=request.path))
            if user["role"] not in roles:
                flash("Tu tipo de cuenta no tiene permiso para esta accion.", "error")
                return redirect(url_for("account"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def read_scope():
    fallback = {
        "brand": "CarTrust",
        "market_mode": "medellin",
        "allowed_dealer_cities": ["Medellin"],
        "future_national_enabled": False,
    }
    path = BASE_DIR / "config" / "market_scope.json"
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8") as file:
        return {**fallback, **json.load(file)}


SCOPE = read_scope()
ALLOWED_CITIES = {normalize_key(city) for city in SCOPE["allowed_dealer_cities"]}


CAPITALS = {
    "Arauca": (7.0847, -70.7591), "Armenia": (4.5339, -75.6811),
    "Barranquilla": (10.9685, -74.7813), "Bogota": (4.7110, -74.0721),
    "Bucaramanga": (7.1193, -73.1227), "Cali": (3.4516, -76.5320),
    "Cartagena": (10.3910, -75.4794), "Cucuta": (7.8891, -72.4967),
    "Florencia": (1.6144, -75.6062), "Ibague": (4.4389, -75.2322),
    "Inirida": (3.8653, -67.9239), "Leticia": (-4.2153, -69.9406),
    "Manizales": (5.0703, -75.5138), "Medellin": (6.2442, -75.5812),
    "Mitu": (1.2539, -70.2350), "Mocoa": (1.1478, -76.6473),
    "Monteria": (8.7500, -75.8814), "Neiva": (2.9273, -75.2819),
    "Pasto": (1.2136, -77.2811), "Pereira": (4.8087, -75.6906),
    "Popayan": (2.4448, -76.6147), "Puerto Carreno": (6.1890, -67.4859),
    "Quibdo": (5.6947, -76.6611), "Riohacha": (11.5444, -72.9072),
    "San Andres": (12.5847, -81.7006), "San Jose del Guaviare": (2.5729, -72.6459),
    "Santa Marta": (11.2408, -74.1990), "Sincelejo": (9.3047, -75.3978),
    "Tunja": (5.5353, -73.3678), "Valledupar": (10.4631, -73.2532),
    "Villavicencio": (4.1420, -73.6266), "Yopal": (5.3378, -72.3959),
}


SEED_LISTINGS = [
    ("Renault Kwid Zen 2023", "Renault", "Kwid Zen", 2023, 46500000, 18500, "Laureles", "Hatchback", "Gasolina", "Manual", 5, 0, 62, 91, 58, 45, 60, 48, "Compacto economico para ciudad y bajo mantenimiento.", "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=1200&q=80"),
    ("Toyota Corolla Cross Hybrid 2024", "Toyota", "Corolla Cross Hybrid", 2024, 142000000, 9200, "El Poblado", "SUV", "Hibrido", "Automatica", 5, 1, 88, 89, 86, 70, 84, 82, "SUV hibrida confiable, comoda y eficiente para familia.", "https://images.unsplash.com/photo-1606611013016-969c19ba27bb?auto=format&fit=crop&w=1200&q=80"),
    ("BYD Yuan Plus EV 2025", "BYD", "Yuan Plus", 2025, 169900000, 4100, "Envigado", "SUV", "Electrico", "Automatica", 5, 1, 90, 96, 88, 83, 88, 78, "Electrico familiar con autonomia estimada de 480 km y conector Tipo 2 / CCS.", "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?auto=format&fit=crop&w=1200&q=80"),
    ("Mazda CX-30 Touring 2022", "Mazda", "CX-30 Touring", 2022, 108000000, 32000, "Belen", "SUV", "Gasolina", "Automatica", 5, 1, 86, 72, 80, 82, 86, 74, "Camioneta compacta comoda, segura y con buen manejo.", "https://images.unsplash.com/photo-1580273916550-e323be2ae537?auto=format&fit=crop&w=1200&q=80"),
    ("Chevrolet Onix Turbo 2021", "Chevrolet", "Onix Turbo", 2021, 58900000, 45500, "Itagui", "Sedan", "Gasolina", "Automatica", 5, 0, 78, 86, 72, 72, 74, 67, "Sedan eficiente con turbo, conectividad y buen precio.", "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1200&q=80"),
    ("Ford Ranger XLT Diesel 2020", "Ford", "Ranger XLT", 2020, 128000000, 68200, "Sabaneta", "Pickup", "Diesel", "Automatica", 5, 1, 82, 70, 74, 86, 76, 94, "Pickup para trabajo, finca y carretera, con gran capacidad de carga.", "https://images.unsplash.com/photo-1551830820-330a71b99659?auto=format&fit=crop&w=1200&q=80"),
    ("Kia Carnival 2023", "Kia", "Carnival", 2023, 188000000, 21000, "Las Palmas", "Van", "Gasolina", "Automatica", 8, 1, 87, 58, 97, 76, 92, 91, "Van amplia para familia grande, viajes largos y mucho equipaje.", "https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&w=1200&q=80"),
    ("Porsche Cayenne 2023", "Porsche", "Cayenne", 2023, 680000000, 12500, "El Tesoro", "SUV", "Gasolina", "Automatica", 5, 1, 92, 50, 82, 96, 95, 84, "SUV premium para quien prioriza confort, desempeño y respaldo.", "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80"),
]


REFERENCE_ROWS = [
    ("Referencia propia", "Renault Kwid", "Renault", "Kwid", 2023, 42000000, 46500000, 52000000, 8),
    ("Referencia propia", "Toyota Corolla Cross", "Toyota", "Corolla Cross", 2024, 132000000, 148000000, 168000000, 7),
    ("Referencia propia", "BYD Yuan Plus", "BYD", "Yuan Plus", 2025, 155000000, 172000000, 190000000, 5),
    ("Referencia propia", "Ford Ranger", "Ford", "Ranger", 2020, 112000000, 132000000, 168000000, 8),
    ("Referencia propia", "Porsche Cayenne", "Porsche", "Cayenne", 2023, 520000000, 680000000, 920000000, 3),
    ("Referencia propia", "Toyota Land Cruiser 300", "Toyota", "Land Cruiser 300", 2024, 620000000, 790000000, 980000000, 3),
]


def ensure_columns(conn, table, columns):
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    for name, definition in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def init_db():
    conn = db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, make TEXT, model TEXT, year INTEGER,
            price INTEGER NOT NULL, mileage INTEGER DEFAULT 0,
            city TEXT DEFAULT 'Medellin', neighborhood TEXT,
            dealer_name TEXT NOT NULL, dealer_phone TEXT, dealer_nit TEXT,
            body_type TEXT, fuel_type TEXT, transmission TEXT, seats INTEGER,
            verified INTEGER DEFAULT 0, status TEXT DEFAULT 'active',
            safety_score INTEGER DEFAULT 70, economy_score INTEGER DEFAULT 70,
            family_score INTEGER DEFAULT 70, performance_score INTEGER DEFAULT 70,
            comfort_score INTEGER DEFAULT 70, cargo_score INTEGER DEFAULT 70,
            description TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS listing_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL, url TEXT NOT NULL, is_primary INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL, name TEXT NOT NULL, phone TEXT NOT NULL,
            message TEXT, privacy_acceptance INTEGER DEFAULT 1, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS vehicle_reference (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL, title TEXT NOT NULL, make TEXT, model TEXT, year INTEGER,
            min_price INTEGER, avg_price INTEGER, max_price INTEGER, sample_size INTEGER DEFAULT 0,
            source_url TEXT, license_note TEXT, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('customer', 'dealer', 'insurer')),
            name TEXT NOT NULL,
            business_name TEXT,
            nit TEXT,
            document_type TEXT,
            document_number TEXT,
            address TEXT,
            business_kind TEXT,
            commercial_registry TEXT,
            chamber_of_commerce TEXT,
            rut_confirmed INTEGER DEFAULT 0,
            legal_representative TEXT,
            representative_document TEXT,
            sfc_code TEXT,
            sfc_entity_type TEXT,
            verification_status TEXT DEFAULT 'pending_review',
            privacy_acceptance INTEGER DEFAULT 0,
            terms_acceptance INTEGER DEFAULT 0,
            compliance_acceptance INTEGER DEFAULT 0,
            city TEXT DEFAULT 'Medellin',
            phone TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS insurer_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insurer_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            monthly_price INTEGER NOT NULL,
            coverage_summary TEXT NOT NULL,
            city TEXT DEFAULT 'Medellin',
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            concept TEXT NOT NULL,
            amount INTEGER NOT NULL,
            method TEXT NOT NULL,
            status TEXT NOT NULL,
            reference TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_listings_price ON listings(price);
        CREATE INDEX IF NOT EXISTS idx_listings_fuel ON listings(fuel_type);
        CREATE INDEX IF NOT EXISTS idx_listings_body ON listings(body_type);
        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
        CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id);
        CREATE INDEX IF NOT EXISTS idx_insurer_products_owner ON insurer_products(insurer_id);
        """
    )
    ensure_columns(conn, "users", {
        "document_type": "TEXT",
        "document_number": "TEXT",
        "address": "TEXT",
        "business_kind": "TEXT",
        "commercial_registry": "TEXT",
        "chamber_of_commerce": "TEXT",
        "rut_confirmed": "INTEGER DEFAULT 0",
        "legal_representative": "TEXT",
        "representative_document": "TEXT",
        "sfc_code": "TEXT",
        "sfc_entity_type": "TEXT",
        "verification_status": "TEXT DEFAULT 'pending_review'",
        "privacy_acceptance": "INTEGER DEFAULT 0",
        "terms_acceptance": "INTEGER DEFAULT 0",
        "compliance_acceptance": "INTEGER DEFAULT 0",
    })
    if conn.execute("SELECT COUNT(*) total FROM listings").fetchone()["total"] == 0:
        now = utc_iso()
        for item in SEED_LISTINGS:
            cur = conn.execute(
                """
                INSERT INTO listings
                (title, make, model, year, price, mileage, neighborhood, body_type, fuel_type,
                 transmission, seats, verified, safety_score, economy_score, family_score,
                 performance_score, comfort_score, cargo_score, description, dealer_name,
                 dealer_phone, dealer_nit, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (*item[:-1], "Concesionario verificado Medellin", "+57 300 000 0000", "900000000-0", now),
            )
            conn.execute(
                "INSERT INTO listing_images (listing_id, url, is_primary) VALUES (?, ?, 1)",
                (cur.lastrowid, item[-1]),
            )
    if conn.execute("SELECT COUNT(*) total FROM vehicle_reference").fetchone()["total"] == 0:
        now = utc_iso()
        for row in REFERENCE_ROWS:
            conn.execute(
                """
                INSERT INTO vehicle_reference
                (source, title, make, model, year, min_price, avg_price, max_price, sample_size, source_url, license_note, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '', 'Referencia propia o autorizada; no scraping de inventarios de terceros.', ?)
                """,
                (*row, now),
            )
    conn.commit()


def listing_image(listing_id):
    row = db().execute(
        "SELECT url FROM listing_images WHERE listing_id = ? ORDER BY is_primary DESC, id ASC LIMIT 1",
        (listing_id,),
    ).fetchone()
    return row["url"] if row else "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=1200&q=80"


def serialize(row):
    item = dict(row)
    item["image_url"] = listing_image(row["id"])
    item["price_formatted"] = money(row["price"])
    item["mileage_formatted"] = number(row["mileage"])
    return item


def query_listings(args=None, limit=None):
    args = args or {}
    clauses, values = ["status = 'active'"], []
    if args.get("q"):
        clauses.append("(title LIKE ? OR make LIKE ? OR model LIKE ? OR neighborhood LIKE ?)")
        like = f"%{args['q'].strip()}%"
        values.extend([like, like, like, like])
    for key, col in [("fuel", "fuel_type"), ("body", "body_type")]:
        if args.get(key) and args[key] != "all":
            clauses.append(f"LOWER({col}) = LOWER(?)")
            values.append(args[key])
    min_price, max_price = parse_int(args.get("min_price")), parse_int(args.get("max_price"))
    if min_price is not None:
        clauses.append("price >= ?")
        values.append(min_price)
    if max_price is not None:
        clauses.append("price <= ?")
        values.append(min(max_price, 1_000_000_000))
    order = {
        "price_asc": "price ASC",
        "price_desc": "price DESC",
        "year_desc": "year DESC",
        "mileage_asc": "mileage ASC",
    }.get(args.get("sort"), "verified DESC, id DESC")
    sql = f"SELECT * FROM listings WHERE {' AND '.join(clauses)} ORDER BY {order}"
    if limit:
        sql += " LIMIT ?"
        values.append(limit)
    return db().execute(sql, values).fetchall()


def score_listing(row, profile):
    budget = parse_int(profile.get("budget"), 150000000)
    people = parse_int(profile.get("people"), 4)
    usage = profile.get("usage", "city")
    priority = profile.get("priority", "economy")
    fuel = (row["fuel_type"] or "").lower()
    body = (row["body_type"] or "").lower()

    score, reasons = 0, []
    if row["price"] <= budget:
        score += 24
        reasons.append("Entra en tu presupuesto.")
    else:
        score += max(0, 24 * (1 - ((row["price"] - budget) / max(budget, 1)) * 1.8))
        reasons.append("Supera el presupuesto y baja conveniencia.")
    score += 12 if (row["seats"] or 0) >= people else 6

    body_map = {
        "city": {"hatchback": 1, "sedan": .9, "suv": .75},
        "family": {"suv": 1, "van": 1, "sedan": .75},
        "work": {"pickup": 1, "suv": .8, "van": .8},
        "travel": {"suv": 1, "van": .85, "sedan": .8},
    }
    score += 14 * body_map.get(usage, {}).get(body, .6)
    score += 20 * ((row[f"{priority}_score"] if f"{priority}_score" in row.keys() else row["economy_score"]) / 100)
    if parse_int(profile.get("daily_km"), 40) >= 70 and fuel in {"electrico", "hibrido", "diesel"}:
        score += 10
        reasons.append("Buen perfil para recorridos altos.")
    else:
        score += 7
    if fuel == "electrico" and profile.get("charging_access") == "home":
        score += 8
        reasons.append("Electrico viable si tienes carga en casa o trabajo.")
    elif fuel == "hibrido":
        score += 7
    else:
        score += 5
    score += 5 if profile.get("preferred_type", "any") in {"any", body, "electric" if fuel == "electrico" else ""} else 2
    if row["verified"]:
        score += 8
        reasons.append("Concesionario verificado.")
    return int(max(0, min(100, round(score)))), reasons[:4]


def recommendations(profile):
    ranked = []
    for row in query_listings({}, limit=40):
        score, reasons = score_listing(row, profile)
        item = serialize(row)
        item["fit_score"], item["fit_reasons"] = score, reasons
        ranked.append(item)
    return sorted(ranked, key=lambda x: x["fit_score"], reverse=True)[:4]


def chat_budget(message):
    text = normalize_key(message)
    if "mil millones" in text or "1000 millones" in text:
        return 1_000_000_000
    for match in re.finditer(r"(\d+(?:[\.,]\d+)?)\s*(?:m|mm|millon|millones)\b", text):
        amount = float(match.group(1).replace(",", "."))
        return min(1_000_000_000, int(amount * 1_000_000))
    amounts = []
    for match in re.finditer(r"\$?\s*\d[\d\.\,\s]{6,}", message):
        value = parse_int(match.group(0))
        if value and value >= 20_000_000:
            amounts.append(value)
    if amounts:
        return min(1_000_000_000, max(amounts))
    if any(word in text for word in ["barato", "economico", "bajo presupuesto"]):
        return 80_000_000
    if any(word in text for word in ["premium", "lujo", "alta gama"]):
        return 1_000_000_000
    return 150_000_000


def chat_profile(message):
    text = normalize_key(message)
    profile = {
        "usage": "city",
        "budget": str(chat_budget(message)),
        "people": "4",
        "daily_km": "40",
        "charging_access": "none",
        "priority": "economy",
        "preferred_type": "any",
    }
    if any(word in text for word in ["familia", "hijos", "ninos", "bebe", "sillas"]):
        profile.update({"usage": "family", "people": "5", "priority": "family"})
    if any(word in text for word in ["trabajo", "herramienta", "finca", "negocio", "carga pesada", "llevar carga", "mercancia"]):
        profile["usage"] = "work"
    if any(word in text for word in ["viaje", "carretera", "viajar", "intermunicipal", "ruta"]):
        profile["usage"] = "travel"
    if match := re.search(r"(\d+)\s*(?:personas|pasajeros|puestos|sillas)", text):
        profile["people"] = str(min(7, max(2, int(match.group(1)))))
    elif "familia grande" in text:
        profile["people"] = "7"
    if match := re.search(r"(\d+)\s*km", text):
        profile["daily_km"] = str(min(180, max(10, int(match.group(1)))))
    if any(word in text for word in ["seguro", "seguridad", "confiable", "familia"]):
        profile["priority"] = "safety" if "familia" not in text else profile["priority"]
    if any(word in text for word in ["ahorro", "economia", "economico", "consumo", "gasolina"]):
        profile["priority"] = "economy"
    if any(word in text for word in ["comodo", "comodidad", "confort", "silencioso"]):
        profile["priority"] = "comfort"
    if any(word in text for word in ["potente", "rapido", "deportivo", "desempeno"]):
        profile["priority"] = "performance"
    if any(word in text for word in ["suv", "camioneta"]):
        profile["preferred_type"] = "suv"
    if "sedan" in text:
        profile["preferred_type"] = "sedan"
    if any(word in text for word in ["hatchback", "compacto", "pequeno"]):
        profile["preferred_type"] = "hatchback"
    if any(word in text for word in ["pickup", "pick up", "camioneta de trabajo"]):
        profile["preferred_type"] = "pickup"
    if "electrico" in text or re.search(r"\bev\b", text) or "cero emisiones" in text:
        profile["preferred_type"] = "electric"
    if any(word in text for word in ["cargador en casa", "carga en casa", "wallbox", "parqueadero con carga", "carga en el trabajo"]):
        profile["charging_access"] = "home"
    elif any(word in text for word in ["electrolinera", "carga publica", "estacion de carga"]):
        profile["charging_access"] = "public"
    return profile


def chat_reply(message, profile, recs):
    text = normalize_key(message)
    if not text:
        return "Cuentame presupuesto, uso principal y cuantas personas van normalmente. Con eso te recomiendo carros del inventario."
    if not recs:
        return "No encontre carros activos para ese perfil. Prueba ampliar presupuesto, tipo de carro o uso principal."
    top = recs[0]
    alternatives = ", ".join(item["title"] for item in recs[1:3]) or "otras opciones similares"
    reasons = top.get("fit_reasons") or ["es la opcion con mayor afinidad frente a lo que escribiste"]
    return (
        f"Te llevaria primero a {top['title']}: marca {top['fit_score']}/100 para tu perfil. "
        f"Lo favorece que {reasons[0].lower()} Precio de referencia en CarTrust: {top['price_formatted']}. "
        f"Tambien miraria {alternatives}. Si me dices cuota mensual ideal o si tienes carga EV en casa, lo afino mas."
    )


def account_home(role):
    return {
        "customer": "customer_dashboard",
        "dealer": "dealer_dashboard",
        "insurer": "insurer_dashboard",
    }.get(role, "index")


@app.route("/registro", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", scope=SCOPE)
    form = request.form
    role = form.get("role", "customer")
    email = clean_text(form.get("email")).lower()
    password = form.get("password") or ""
    city = clean_text(form.get("city")) or "Medellin"
    name = clean_text(form.get("name"))
    phone = clean_text(form.get("phone"))
    address = clean_text(form.get("address"))
    document_number = clean_identifier(form.get("document_number"))
    business_name = clean_text(form.get("business_name"))
    nit = clean_identifier(form.get("nit"))
    commercial_registry = clean_identifier(form.get("commercial_registry"))
    chamber_of_commerce = clean_text(form.get("chamber_of_commerce"))
    business_kind = clean_text(form.get("business_kind"))
    legal_representative = clean_text(form.get("legal_representative"))
    representative_document = clean_identifier(form.get("representative_document"))
    sfc_code = clean_identifier(form.get("sfc_code"))
    sfc_entity_type = clean_text(form.get("sfc_entity_type"))
    if role not in USER_ROLES:
        flash("Selecciona un tipo de cuenta valido.", "error")
        return render_template("register.html", scope=SCOPE, form=form), 400
    if not name or not phone or not city:
        flash("Completa nombre, celular y ciudad.", "error")
        return render_template("register.html", scope=SCOPE, form=form), 400
    if not email or "@" not in email or len(password) < 8:
        flash("Usa un correo valido y una clave de minimo 8 caracteres.", "error")
        return render_template("register.html", scope=SCOPE, form=form), 400
    if form.get("privacy_acceptance") != "on" or form.get("terms_acceptance") != "on":
        flash("Debes aceptar tratamiento de datos y terminos para crear cuenta.", "error")
        return render_template("register.html", scope=SCOPE, form=form), 400
    if role == "customer":
        if not document_number:
            flash("Los particulares deben registrar cedula de ciudadania.", "error")
            return render_template("register.html", scope=SCOPE, form=form), 400
        verification_status = "verified"
    else:
        required_business = [
            business_name, nit, address, commercial_registry, chamber_of_commerce,
            business_kind, legal_representative, representative_document,
        ]
        if not all(required_business):
            flash("Completa razon social, NIT, direccion, matricula mercantil, camara de comercio y representante legal.", "error")
            return render_template("register.html", scope=SCOPE, form=form), 400
        if role == "dealer" and business_kind != "dealer_used":
            flash("Una cuenta de concesionario debe registrar actividad de compraventa/concesionario de usados.", "error")
            return render_template("register.html", scope=SCOPE, form=form), 400
        if role == "insurer" and business_kind not in {"insurance_company", "insurance_intermediary"}:
            flash("Una cuenta de aseguradora debe registrar actividad aseguradora o de intermediacion.", "error")
            return render_template("register.html", scope=SCOPE, form=form), 400
        if form.get("compliance_acceptance") != "on":
            flash("Debes declarar que la informacion empresarial esta vigente y autorizas su verificacion.", "error")
            return render_template("register.html", scope=SCOPE, form=form), 400
        if role == "insurer" and (not sfc_entity_type or not sfc_code):
            flash("Las aseguradoras o intermediarios deben registrar tipo de entidad y codigo/registro SFC o SUCIS.", "error")
            return render_template("register.html", scope=SCOPE, form=form), 400
        verification_status = "pending_review"
    if role == "dealer" and normalize_key(city) not in ALLOWED_CITIES and not SCOPE.get("future_national_enabled"):
        flash("Por ahora los concesionarios habilitados deben estar en Medellin.", "error")
        return render_template("register.html", scope=SCOPE, form=form), 400
    try:
        cur = db().execute(
            """
            INSERT INTO users
            (email, password_hash, role, name, business_name, nit, document_type,
             document_number, address, business_kind, commercial_registry,
             chamber_of_commerce, rut_confirmed, legal_representative,
             representative_document, sfc_code, sfc_entity_type, verification_status,
             privacy_acceptance, terms_acceptance, compliance_acceptance, city, phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                email,
                generate_password_hash(password),
                role,
                name,
                business_name,
                nit,
                "CC" if role == "customer" else "NIT",
                document_number if role == "customer" else nit,
                address,
                business_kind if role in BUSINESS_ROLES else None,
                commercial_registry,
                chamber_of_commerce,
                1 if role in BUSINESS_ROLES else 0,
                legal_representative,
                representative_document,
                sfc_code,
                sfc_entity_type,
                verification_status,
                1,
                1,
                1 if role in BUSINESS_ROLES and form.get("compliance_acceptance") == "on" else 0,
                city,
                phone,
                utc_iso(),
            ),
        )
        db().commit()
    except sqlite3.IntegrityError:
        flash("Ese correo ya tiene una cuenta.", "error")
        return render_template("register.html", scope=SCOPE, form=form), 409
    session["user_id"] = cur.lastrowid
    flash("Cuenta creada correctamente.", "success")
    return redirect(url_for(account_home(role)))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    email = (request.form.get("email") or "").strip().lower()
    user = db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user or not check_password_hash(user["password_hash"], request.form.get("password") or ""):
        flash("Correo o clave incorrectos.", "error")
        return render_template("login.html", email=email), 401
    session["user_id"] = user["id"]
    next_url = request.args.get("next") or request.form.get("next") or ""
    flash("Bienvenido a CarTrust.", "success")
    if next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect(url_for(account_home(user["role"])))


@app.get("/logout")
def logout():
    session.clear()
    flash("Sesion cerrada.", "success")
    return redirect(url_for("index"))


@app.get("/cuenta")
@login_required
def account():
    return redirect(url_for(account_home(current_user()["role"])))


@app.get("/panel/cliente")
@role_required("customer")
def customer_dashboard():
    payments = db().execute(
        "SELECT * FROM payments WHERE user_id = ? ORDER BY id DESC LIMIT 5",
        (current_user()["id"],),
    ).fetchall()
    stats = {
        "vehicles": db().execute("SELECT COUNT(*) total FROM listings WHERE status='active'").fetchone()["total"],
        "ev": db().execute("SELECT COUNT(*) total FROM listings WHERE LOWER(fuel_type)='electrico'").fetchone()["total"],
    }
    return render_template("dashboard_customer.html", payments=payments, stats=stats)


@app.get("/panel/concesionario")
@role_required("dealer")
def dealer_dashboard():
    user = current_user()
    listings = db().execute(
        "SELECT * FROM listings WHERE dealer_nit = ? ORDER BY id DESC",
        (user["nit"],),
    ).fetchall()
    leads = db().execute(
        """
        SELECT leads.*, listings.title
        FROM leads
        JOIN listings ON listings.id = leads.listing_id
        WHERE listings.dealer_nit = ?
        ORDER BY leads.id DESC
        LIMIT 20
        """,
        (user["nit"],),
    ).fetchall()
    return render_template("dashboard_dealer.html", listings=listings, leads=leads)


@app.get("/panel/aseguradora")
@role_required("insurer")
def insurer_dashboard():
    products = db().execute(
        "SELECT * FROM insurer_products WHERE insurer_id = ? ORDER BY id DESC",
        (current_user()["id"],),
    ).fetchall()
    return render_template("dashboard_insurer.html", products=products)


@app.route("/aseguradora/productos/nuevo", methods=["GET", "POST"])
@role_required("insurer")
def publish_insurance():
    if request.method == "GET":
        return render_template("insurer_product_form.html")
    form = request.form
    monthly_price = parse_int(form.get("monthly_price"), 0)
    if monthly_price <= 0 or monthly_price > 100_000_000:
        flash("Ingresa un valor mensual valido para el producto.", "error")
        return render_template("insurer_product_form.html", form=form), 400
    db().execute(
        """
        INSERT INTO insurer_products
        (insurer_id, name, category, monthly_price, coverage_summary, city, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            current_user()["id"],
            form.get("name"),
            form.get("category"),
            monthly_price,
            form.get("coverage_summary"),
            form.get("city") or "Medellin",
            utc_iso(),
        ),
    )
    db().commit()
    flash("Producto de aseguradora publicado.", "success")
    return redirect(url_for("insurer_dashboard"))


@app.route("/pagos", methods=["GET", "POST"])
@login_required
def payments():
    if request.method == "POST":
        method = request.form.get("method")
        amount = parse_int(request.form.get("amount"), 0)
        concept = (request.form.get("concept") or "Reserva o servicio CarTrust").strip()
        allowed_methods = {code for code, _label in PAYMENT_METHODS}
        if method not in allowed_methods:
            flash("Selecciona un metodo digital habilitado. Los pagos fisicos no estan activos.", "error")
            return redirect(url_for("payments"))
        if amount <= 0 or amount > 1_000_000_000:
            flash("El valor debe estar entre $1 y $1.000.000.000 COP.", "error")
            return redirect(url_for("payments"))
        db().execute(
            """
            INSERT INTO payments
            (user_id, concept, amount, method, status, reference, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                current_user()["id"],
                concept,
                amount,
                method,
                "pending_gateway",
                f"CT-{uuid4().hex[:10].upper()}",
                utc_iso(),
            ),
        )
        db().commit()
        flash("Intencion de pago creada. En produccion se conecta a Wompi, PayU o Mercado Pago.", "success")
        return redirect(url_for("payments"))
    rows = db().execute(
        "SELECT * FROM payments WHERE user_id = ? ORDER BY id DESC LIMIT 20",
        (current_user()["id"],),
    ).fetchall()
    return render_template("payments.html", payments=rows)


@app.route("/")
def index():
    listings = [serialize(row) for row in query_listings(request.args)]
    featured = listings[:4]
    stats = {
        "vehicles": db().execute("SELECT COUNT(*) total FROM listings WHERE status='active'").fetchone()["total"],
        "verified": db().execute("SELECT COUNT(*) total FROM listings WHERE verified=1").fetchone()["total"],
        "ev": db().execute("SELECT COUNT(*) total FROM listings WHERE LOWER(fuel_type)='electrico'").fetchone()["total"],
        "refs": db().execute("SELECT COUNT(*) total FROM vehicle_reference").fetchone()["total"],
    }
    return render_template("index.html", listings=listings, featured=featured, stats=stats, filters=request.args)


@app.route("/listing/<int:listing_id>")
def detail(listing_id):
    row = db().execute("SELECT * FROM listings WHERE id=?", (listing_id,)).fetchone()
    if not row:
        return render_template("404.html"), 404
    related = [serialize(item) for item in query_listings({"body": row["body_type"]}, limit=4) if item["id"] != listing_id][:3]
    return render_template("detail.html", listing=dict(row), image=listing_image(listing_id), related=related)


@app.route("/publicar", methods=["GET", "POST"])
@role_required("dealer")
def publish():
    user = current_user()
    if request.method == "GET":
        return render_template("publish.html", scope=SCOPE, dealer=user)
    form = request.form
    city = (form.get("city") or user["city"] or "Medellin").strip()
    if normalize_key(city) not in ALLOWED_CITIES and not SCOPE.get("future_national_enabled"):
        flash("Por ahora solo aceptamos concesionarios de usados en Medellin.", "error")
        return render_template("publish.html", scope=SCOPE, form=form, dealer=user), 400
    if form.get("legal_acceptance") != "on":
        flash("Debes aceptar las politicas y declarar informacion veraz del vehiculo.", "error")
        return render_template("publish.html", scope=SCOPE, form=form, dealer=user), 400
    price = parse_int(form.get("price"), 0)
    if price <= 0 or price > 1_000_000_000:
        flash("El precio debe estar entre $1 y $1.000.000.000 COP.", "error")
        return render_template("publish.html", scope=SCOPE, form=form, dealer=user), 400
    cur = db().execute(
        """
        INSERT INTO listings
        (title, make, model, year, price, mileage, city, neighborhood, dealer_name, dealer_phone,
         dealer_nit, body_type, fuel_type, transmission, seats, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            form.get("title"), form.get("make"), form.get("model"), parse_int(form.get("year")),
            price, parse_int(form.get("mileage"), 0), city, form.get("neighborhood"),
            user["business_name"] or user["name"], user["phone"], user["nit"],
            form.get("body_type"), form.get("fuel_type"), form.get("transmission"),
            parse_int(form.get("seats"), 5), form.get("description"), utc_iso(),
        ),
    )
    files = request.files.getlist("images")
    for idx, file in enumerate(files):
        if file and "." in file.filename and file.filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGES:
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            name = f"{uuid4().hex}_{secure_filename(file.filename)}"
            file.save(UPLOAD_DIR / name)
            db().execute("INSERT INTO listing_images (listing_id, url, is_primary) VALUES (?, ?, ?)", (cur.lastrowid, url_for("static", filename=f"uploads/{name}"), 1 if idx == 0 else 0))
    db().commit()
    flash("Publicacion creada.", "success")
    return redirect(url_for("detail", listing_id=cur.lastrowid))


@app.post("/contacto/<int:listing_id>")
def contact(listing_id):
    if request.form.get("privacy_acceptance") != "on":
        flash("Debes aceptar el tratamiento de datos para enviar tu solicitud.", "error")
        return redirect(url_for("detail", listing_id=listing_id))
    db().execute(
        "INSERT INTO leads (listing_id, name, phone, message, created_at) VALUES (?, ?, ?, ?, ?)",
        (listing_id, request.form.get("name"), request.form.get("phone"), request.form.get("message"), utc_iso()),
    )
    db().commit()
    flash("Solicitud enviada al concesionario.", "success")
    return redirect(url_for("detail", listing_id=listing_id))


@app.route("/asesor")
def advisor():
    featured = [serialize(row) for row in query_listings({}, limit=3)]
    return render_template("advisor.html", featured=featured)


@app.route("/preview-web")
def preview_web():
    preview_path = BASE_DIR / "CarTrust_vista_previa_web.html"
    if preview_path.exists():
        return send_file(preview_path)
    return redirect(url_for("advisor"))


@app.route("/carga")
def charging():
    return render_template("charging.html", cities=CAPITALS)


@app.route("/referencias")
def references():
    rows = db().execute("SELECT * FROM vehicle_reference ORDER BY make, model, year DESC").fetchall()
    return render_template("references.html", references=[dict(row) for row in rows])


@app.get("/api/listings")
def api_listings():
    return jsonify([serialize(row) for row in query_listings(request.args)])


@app.post("/api/quiz/recommend")
def api_recommend():
    profile = request.get_json(silent=True) or {}
    return jsonify({"profile": profile, "recommendations": recommendations(profile)})


@app.post("/api/chat-advisor")
def api_chat_advisor():
    payload = request.get_json(silent=True) or {}
    message = clean_text(payload.get("message"))
    profile = chat_profile(message)
    recs = recommendations(profile)
    return jsonify({
        "reply": chat_reply(message, profile, recs),
        "profile": profile,
        "recommendations": recs[:3],
    })


@app.post("/api/listings/<int:listing_id>/score")
def api_score(listing_id):
    row = db().execute("SELECT * FROM listings WHERE id=?", (listing_id,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    profile = request.get_json(silent=True) or {}
    selected, reasons = score_listing(row, profile)
    best = recommendations(profile)[0]
    return jsonify({"selected_score": selected, "relative_score": min(100, round(selected / max(best["fit_score"], 1) * 100)), "benchmark": best, "reasons": reasons})


def normalize_station(item):
    addr = item.get("AddressInfo") or {}
    conns = item.get("Connections") or []
    labels = []
    powers = []
    for conn in conns:
        ctype = conn.get("ConnectionType") or {}
        if ctype.get("Title"):
            labels.append(ctype["Title"])
        if conn.get("PowerKW"):
            powers.append(conn["PowerKW"])
    return {
        "title": addr.get("Title") or "Punto de carga",
        "address": ", ".join(x for x in [addr.get("AddressLine1"), addr.get("Town")] if x),
        "latitude": addr.get("Latitude"),
        "longitude": addr.get("Longitude"),
        "operator": (item.get("OperatorInfo") or {}).get("Title") or "Operador no informado",
        "status": (item.get("StatusType") or {}).get("Title") or "Estado no informado",
        "connections": ", ".join(sorted(set(labels))) or "Conector no informado",
        "power_kw": max(powers) if powers else None,
    }


@app.get("/api/charging-stations")
def api_stations():
    city = request.args.get("city", "Medellin")
    if city not in CAPITALS:
        city = "Medellin"
    lat, lon = CAPITALS[city]
    key = f"{city}:{request.args.get('refresh')}"
    if key in _station_cache and _station_cache[key]["expires"] > time.time():
        return jsonify(_station_cache[key]["payload"])
    payload = {"city": city, "center": {"latitude": lat, "longitude": lon}, "source": "openchargemap_unavailable", "source_label": "Configure OCM_API_KEY para consultar estaciones reales.", "stations": []}
    api_key = os.getenv("OCM_API_KEY")
    if api_key:
        try:
            response = requests.get(
                "https://api.openchargemap.io/v3/poi/",
                params={"output": "json", "latitude": lat, "longitude": lon, "distance": 40, "distanceunit": "KM", "maxresults": 200, "countrycode": "CO", "key": api_key},
                timeout=8,
                headers={"User-Agent": "CarTrust Colombia/1.0", "X-API-Key": api_key},
            )
            response.raise_for_status()
            stations = [s for s in (normalize_station(item) for item in response.json()) if s["latitude"] and s["longitude"]]
            payload.update({"source": "openchargemap", "source_label": f"Open Charge Map, radio 40 km desde {city}", "stations": stations})
        except requests.RequestException:
            pass
    _station_cache[key] = {"expires": time.time() + 1800, "payload": payload}
    return jsonify(payload)


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
