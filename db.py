import sqlite3
from config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id TEXT PRIMARY KEY,
            source TEXT,
            title TEXT,
            price TEXT,
            url TEXT,
            image_url TEXT,
            address TEXT,
            lat REAL,
            lon REAL,
            seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def is_seen(listing_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT 1 FROM listings WHERE id = ?", (listing_id,)).fetchone()
    conn.close()
    return row is not None


def mark_seen(listing: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT OR IGNORE INTO listings (id, source, title, price, url, image_url, address, lat, lon)
        VALUES (:id, :source, :title, :price, :url, :image_url, :address, :lat, :lon)
    """, listing)
    conn.commit()
    conn.close()
