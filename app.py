from flask import Flask, render_template, request, redirect
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import uuid
import sqlite3
from PIL import Image


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

DATABASE = 'list.db'

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
        app.logger.info(f"SQLite error:", e)

    finally:
        conn.close()

def get_items():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM items")
        items = c.fetchall()
        return items

    except sqlite3.Error as e:
        app.logger.info(f"SQLite error:", e)
        return None
    
    finally:
        conn.close()

def get_closest_expiration():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        current_date = datetime.now().date()
        c.execute(
            "SELECT id, name, date_bought, '' || thumbnail, warranty_expiration_date "
            "FROM items "
            "WHERE warranty_expiration_date >= ? "
            "ORDER BY warranty_expiration_date "
            "LIMIT 5",
            (current_date,)
        )
        items = c.fetchall()
        return items
    
    except sqlite3.Error as e:
        app.logger.info("SQLite error:", e)
    
    finally:
        conn.close()
    
def get_recent_items():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute(
            "SELECT id, name, date_bought, '' || thumbnail, strftime('%Y-%m-%d', date_bought) as formatted_date "
            "FROM items "
            "ORDER BY date_bought DESC "
            "LIMIT 5"
        )
        items = c.fetchall()
        return items
    
    except sqlite3.Error as e:
        app.logger.info("SQLite error:", e)
    
    finally:
        conn.close()

def add_item(name, warranty_dur, date_bought, thumbnail, warranty_expiration_date):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO items (name, warranty_dur, date_bought, thumbnail, warranty_expiration_date) VALUES (?, ?, ?, ?, ?)",
                (name, warranty_dur, date_bought, thumbnail, warranty_expiration_date))
        conn.commit()
        
    except sqlite3.Error as e:
        app.logger.info(f"SQLite error:", e)
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
        app.logger.info(f"SQLite error:", e)
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
        app.logger.info(f"SQLite error:", e)
        print("SQLite error:", e)

    finally:
        conn.close()

def calculate_expiration_date(warranty_dur):
    current_date = datetime.now()
    future_date = (current_date + relativedelta(months=warranty_dur)).date()
    return(future_date)

def save_resize_thumbnail(thumbnail_path, thumbnail_size_px=100):
    try:           
        output_size = (thumbnail_size_px, thumbnail_size_px)
        i = Image.open(thumbnail_path)
        i.thumbnail(output_size)
        i.save(thumbnail_path)
    except Exception as e:
        app.logger.info(f"Error saving thumbnail: {e}")
        print(f"Error saving thumbnail: {e}")
        return None
    finally:
        return thumbnail_path


@app.route('/', methods=['GET'])
def home():
    if not os.path.exists(DATABASE):
        create_database()
    closest_items = get_closest_expiration()
    recent_items = get_recent_items()
    return render_template('home.html', closest_items=closest_items, recent_items=recent_items)

@app.route('/item_page/<int:item_id>', methods=['GET'])
def item_page(item_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute(
            "SELECT id, name, date_bought, '' || thumbnail, warranty_expiration_date "
            "FROM items "
            "WHERE id = ?",
            (item_id,)
        )
        item = c.fetchone()
        if item:
            thumbnail_file = os.path.basename(item[3])
            thumbnail_path = os.path.join('uploads/' 'products_thumbnails/', thumbnail_file)
            return render_template('item_page.html', item=item, file_path=thumbnail_path)
        else:
            return "Item not found", 404
    
    except sqlite3.Error as e:
        app.logger.info("SQLite error:", e)
    
    finally:
        conn.close()


@app.route('/add', methods=['GET', 'POST'])
def add_item_route():
    if request.method == 'POST':
        name = request.form['name']
        warranty_dur = int(request.form['warranty_dur'])
        date_bought = request.form['date_bought']
        warranty_expiration_date = calculate_expiration_date(warranty_dur)
        
        thumbnail = request.files.get('thumbnail')
        thumbnail_path = None
        if thumbnail:
            random_filename = str(uuid.uuid4()) + os.path.splitext(thumbnail.filename)[1]
            thumbnail_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'products_thumbnails')
            os.makedirs(thumbnail_dir, exist_ok=True) 
            thumbnail_path = os.path.join(thumbnail_dir, random_filename)
            thumbnail.save(thumbnail_path)
            save_resize_thumbnail(thumbnail_path, 95)

        add_item(name, warranty_dur, date_bought, thumbnail_path, warranty_expiration_date)
        return redirect('/')
    return render_template('add_item.html')

@app.route('/full_list', methods=['GET'])
def full_list():
    items_list = get_items()
    items_dict = [{'id': item[0], 'name': item[1], 'warranty_dur': item[2], 'date_bought': item[3], 'thumbnail': item[4], 'timestamp': item[5]} for item in items_list]
    for item in items_dict:
        if item['thumbnail']:
            item['thumbnail'] = item['thumbnail'].replace(os.sep, '/')

    return render_template('full_list.html', items=items_dict)


@app.route('/delete/<int:item_id>', methods=['POST', 'GET'])
def delete_item_route(item_id):
    delete_item_database(item_id)
    return redirect('/full_list')


@app.route('/delete_all', methods=['POST', 'GET'])
def delete_all_items_route():
    delete_all_items()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
