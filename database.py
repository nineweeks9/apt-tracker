import aiosqlite
import os
from config import DB_PATH

async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("""CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS apartments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            apt_name TEXT NOT NULL, sigungu_code TEXT NOT NULL,
            dong TEXT, sigungu_name TEXT, last_updated TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(apt_name, sigungu_code))""")
        await db.execute("""CREATE TABLE IF NOT EXISTS folder_apartments (
            folder_id INTEGER REFERENCES folders(id) ON DELETE CASCADE,
            apartment_id INTEGER REFERENCES apartments(id) ON DELETE CASCADE,
            PRIMARY KEY (folder_id, apartment_id))""")
        await db.execute("""CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            apartment_id INTEGER REFERENCES apartments(id) ON DELETE CASCADE,
            deal_amount INTEGER NOT NULL, area REAL NOT NULL,
            floor INTEGER, build_year INTEGER,
            deal_year INTEGER NOT NULL, deal_month INTEGER NOT NULL, deal_day INTEGER,
            UNIQUE(apartment_id, deal_year, deal_month, deal_day, area, floor, deal_amount))""")
        await db.commit()
        print("DB init done")
