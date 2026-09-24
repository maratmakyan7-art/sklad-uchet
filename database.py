import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "sklad.db"
IMAGES_DIR = Path(__file__).parent / "images"
UPLOADS_DIR = Path(__file__).parent / "uploads"

IMAGES_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
DB_PATH.parent.mkdir(exist_ok=True)


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # ===== Склады =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS warehouses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            sort_order INTEGER DEFAULT 0
        )
    """)

    # Предустановленные склады
    warehouses = [
        (1, "Основной склад", 1),
        (2, "Склад импортных и новых запчастей", 2),
        (3, "Склад горюче-смазочные материалы", 3),
    ]
    for wid, name, order in warehouses:
        c.execute("""
            INSERT OR IGNORE INTO warehouses (id, name, sort_order) VALUES (?, ?, ?)
        """, (wid, name, order))

    # ===== Товары (справочник) =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            purpose TEXT,
            size TEXT,
            weight_volume TEXT,
            unit TEXT NOT NULL DEFAULT 'шт',
            condition TEXT DEFAULT 'Новый',
            category TEXT,
            photo_path TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ===== Остатки (товар + склад + место + количество) =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            warehouse_id INTEGER NOT NULL,
            quantity REAL NOT NULL DEFAULT 0,
            storage_place TEXT,
            UNIQUE(product_id, warehouse_id, storage_place),
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
        )
    """)

    # ===== Машины / Механизмы =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            model TEXT,
            plate_number TEXT,
            vin TEXT,
            driver TEXT,
            owner TEXT,
            photo_path TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ===== Поставщики =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            inn TEXT,
            address TEXT,
            contacts TEXT,
            shop TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ===== Приходные документы (шапка) =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS incoming_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_number TEXT NOT NULL,
            document_date DATE NOT NULL,
            supplier_id INTEGER,
            file_path TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )
    """)

    # ===== Строки прихода =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS incoming_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            warehouse_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            price REAL DEFAULT 0,
            vat_percent REAL DEFAULT 0,
            vat_amount REAL DEFAULT 0,
            total_with_vat REAL DEFAULT 0,
            storage_place TEXT,
            FOREIGN KEY (document_id) REFERENCES incoming_documents(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
        )
    """)

    # ===== Расходные документы (шапка) =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS outgoing_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_date DATE NOT NULL,
            machine_id INTEGER,
            destination TEXT,
            issued_to TEXT,
            file_path TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (machine_id) REFERENCES machines(id)
        )
    """)

    # ===== Строки расхода =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS outgoing_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            warehouse_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            storage_place TEXT,
            FOREIGN KEY (document_id) REFERENCES outgoing_documents(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
        )
    """)

    conn.commit()
    conn.close()
    print("База данных v3 успешно создана/обновлена")


if __name__ == "__main__":
    init_db()
