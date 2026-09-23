import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "sklad.db"
IMAGES_DIR = Path(__file__).parent / "images"
IMAGES_DIR.mkdir(exist_ok=True)


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Справочник товаров
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            purpose TEXT,
            unit TEXT NOT NULL DEFAULT 'шт',
            storage_place TEXT,
            notes TEXT,
            category TEXT,
            photo_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Справочник машин / механизмов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            inventory_number TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Места хранения (опционально, можно расширять)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS storage_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    """)

    # Движения (приход и расход)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL CHECK(movement_type IN ('приход', 'расход')),
            quantity REAL NOT NULL,
            document_number TEXT,
            price_per_unit REAL,
            vat_percent REAL DEFAULT 0,
            vat_amount REAL DEFAULT 0,
            total_with_vat REAL DEFAULT 0,
            machine_id INTEGER,
            destination TEXT,
            comment TEXT,
            movement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (machine_id) REFERENCES machines(id)
        )
    """)

    # Текущие остатки (вычисляемая, но для скорости можно хранить)
    # Будем считать остатки через SUM по movements

    conn.commit()
    conn.close()
    print("База данных успешно создана/обновлена")


if __name__ == "__main__":
    init_db()
