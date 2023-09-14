import sqlite3
from datetime import datetime, timedelta

DATABASE = 'list.db'

def create_database():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS lists
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 list_id INTEGER NOT NULL,
                 name TEXT NOT NULL,
                 warranty_dur INTEGER NOT NULL,
                 date_bought TEXT NOT NULL,
                 thumbnail TEXT NOT NULL,
                 FOREIGN KEY (list_id) REFERENCES lists (id))''')
    conn.commit()
    conn.close()

def create_list(name):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO lists (name) VALUES (?)", (name,))
    list_id = c.lastrowid
    conn.commit()
    conn.close()
    return list_id

def get_list(list_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM lists WHERE id=?", (list_id,))
    list_data = c.fetchone()
    conn.close()
    return list_data

def get_items(list_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM items WHERE list_id=?", (list_id,))
    items = c.fetchall()
    conn.close()
    return items

def get_closest_items(list_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM items WHERE list_id=? ORDER BY date_bought DESC LIMIT 5", (list_id,))
    items = c.fetchall()
    conn.close()
    return items

def get_recent_items(list_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM items WHERE list_id=? ORDER BY id DESC LIMIT 3", (list_id,))
    items = c.fetchall()
    conn.close()
    return items

def add_item(list_id, name, warranty_dur, date_bought, thumbnail):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO items (list_id, name, warranty_dur, date_bought, thumbnail) VALUES (?, ?, ?, ?, ?)",
              (list_id, name, warranty_dur, date_bought, thumbnail))
    conn.commit()
    conn.close()

def delete_item(item_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

def calculate_expiration_date(date_bought, warranty_dur):
    date_bought = datetime.strptime(date_bought, '%Y-%m-%d')
    expiration_date = date_bought + timedelta(days=warranty_dur)
    return expiration_date.strftime('%Y-%m-%d')
