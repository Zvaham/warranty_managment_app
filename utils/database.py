import sqlite3
from datetime import datetime
from app import current_app

DATABASE = f'database\\list.db'


def create_database():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS items
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    warranty_dur INTEGER NOT NULL,
                    date_bought TEXT NOT NULL,
                    thumbnail TEXT,
                    warranty_expiration_date TEXT)''')
        conn.commit()

    except sqlite3.Error as e:
        current_app.logger.info(f"SQLite error:", e)

    finally:
        conn.close()


def get_item_by_id(item_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM items WHERE id=?", (item_id,))
        item = c.fetchone()
        return item

    except sqlite3.Error as e:
        current_app.logger.info("SQLite error:", e)
        print("SQLite error:", e)
        return None

    finally:
        conn.close()


def get_all_items():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM items")
        items = c.fetchall()
        return items

    except sqlite3.Error as e:
        current_app.logger.info(f"SQLite error:", e)
        return None

    finally:
        conn.close()


def get_closest_expiration():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        current_date = datetime.now().date()
        c.execute(
            "SELECT id, name, warranty_dur, date_bought, '' || thumbnail, warranty_expiration_date "
            "FROM items "
            "WHERE warranty_expiration_date >= ? "
            "ORDER BY warranty_expiration_date "
            "LIMIT 5",
            (current_date,)
        )
        items = c.fetchall()
        return items

    except sqlite3.Error as e:
        current_app.logger.info("SQLite error:", e)

    finally:
        conn.close()


def get_recent_items():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute(
            "SELECT id, name, warranty_dur, date_bought, '' || thumbnail, strftime('%Y-%m-%d', date_bought) as formatted_date "
            "FROM items "
            "ORDER BY date_bought DESC "
            "LIMIT 5"
        )
        items = c.fetchall()
        return items

    except sqlite3.Error as e:
        current_app.logger.info("SQLite error:", e)

    finally:
        conn.close()


def add_item_database(name, warranty_dur, date_bought, thumbnail, warranty_expiration_date):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO items (name, warranty_dur, date_bought, thumbnail, warranty_expiration_date) VALUES (?, ?, ?, ?, ?)",
                  (name, warranty_dur, date_bought, thumbnail, warranty_expiration_date))
        conn.commit()

    except sqlite3.Error as e:
        current_app.logger.info(f"SQLite error:", e)
        print("SQLite error:", e)

    finally:
        conn.close()


def update_item_database(item_id, name, warranty_dur, date_bought, thumbnail, warranty_expiration_date):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute(
            "UPDATE items SET name=?, warranty_dur=?, date_bought=?, thumbnail=?, warranty_expiration_date=? WHERE id=?",
            (name, warranty_dur, date_bought, thumbnail, warranty_expiration_date, item_id)
        )
        conn.commit()
        print(f"Updated item with ID {item_id}")

    except sqlite3.Error as e:
        current_app.logger.info(f"SQLite error:", e)
        print("SQLite error:", e)

    finally:
        conn.close()


def delete_item_database(item_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("DELETE FROM items WHERE id=?", (item_id,))
        conn.commit()
        print(f"Deleted item with ID {item_id}")

    except sqlite3.Error as e:
        conn.rollback()
        current_app.logger.info(f"SQLite error:", e)
        print("SQLite error:", e)

    finally:
        conn.close()


def delete_all_items():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("DELETE FROM items")
        conn.commit()

    except sqlite3.Error as e:
        conn.rollback()
        current_app.logger.info(f"SQLite error:", e)
        print("SQLite error:", e)

    finally:
        conn.close()
