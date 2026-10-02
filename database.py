import os
import sqlite3
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(DATA_DIR, "app.db"))

SHIPMENT_STATUSES = [
    "Received",
    "Purchasing",
    "Quality check",
    "Shipped",
    "In transit",
    "Customs",
    "Delivered",
]


def _ensure_dir():
    os.makedirs(os.path.dirname(DB_PATH) or DATA_DIR, exist_ok=True)


@contextmanager
def get_db():
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                country TEXT,
                product TEXT,
                quantity TEXT,
                shipping_method TEXT,
                budget TEXT,
                message TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shipments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_id TEXT NOT NULL UNIQUE,
                customer_name TEXT,
                destination TEXT,
                method TEXT,
                status TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        existing = conn.execute(
            "SELECT 1 FROM shipments WHERE tracking_id = ?", ("TJC-DEMO",)
        ).fetchone()
        if not existing:
            conn.execute(
                """
                INSERT INTO shipments (
                    tracking_id, customer_name, destination, method, status, note, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """,
                (
                    "TJC-DEMO",
                    "Demo order",
                    "Accra, Ghana",
                    "Air",
                    "In transit",
                    "Example shipment so you can try tracking. Real orders get a unique TJC code.",
                ),
            )


def save_lead(kind, name, email, phone="", country="", product="", quantity="",
              shipping_method="", budget="", message=""):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO leads (
                kind, name, email, phone, country, product, quantity,
                shipping_method, budget, message, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                kind, name, email, phone, country, product, quantity,
                shipping_method, budget, message,
            ),
        )


def list_leads(limit=200):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_shipment(tracking_id):
    tracking_id = (tracking_id or "").strip().upper()
    if not tracking_id:
        return None
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM shipments WHERE upper(tracking_id) = ?",
            (tracking_id,),
        ).fetchone()
        return dict(row) if row else None


def list_shipments():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM shipments ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def next_tracking_id():
    with get_db() as conn:
        row = conn.execute("SELECT COALESCE(MAX(id), 0) + 1001 AS n FROM shipments").fetchone()
        return f"TJC-{int(row['n'])}"


def upsert_shipment(tracking_id, customer_name, destination, method, status, note):
    tracking_id = (tracking_id or "").strip().upper()
    if not tracking_id:
        tracking_id = next_tracking_id()
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM shipments WHERE upper(tracking_id) = ?", (tracking_id,)
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE shipments
                SET customer_name = ?, destination = ?, method = ?, status = ?, note = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (customer_name, destination, method, status, note, existing["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO shipments (
                    tracking_id, customer_name, destination, method, status, note, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """,
                (tracking_id, customer_name, destination, method, status, note),
            )
    return tracking_id


def delete_shipment(tracking_id):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM shipments WHERE upper(tracking_id) = ?",
            ((tracking_id or "").strip().upper(),),
        )
