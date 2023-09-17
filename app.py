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

def get_item_by_id(item_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM items WHERE id=?", (item_id,))
        item = c.fetchone()
        return item

    except sqlite3.Error as e:
        app.logger.info("SQLite error:", e)
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
        app.logger.info("SQLite error:", e)
    
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
        app.logger.info("SQLite error:", e)
    
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
        app.logger.info(f"SQLite error:", e)
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
    return future_date

def days_until_expiration(future_date):
    current_date = datetime.now().date()
    return (future_date - current_date).days

def save_resize_thumbnail(thumbnail_path, thumbnail_size_px=150):
    output_size = (thumbnail_size_px, thumbnail_size_px)
    i = Image.open(thumbnail_path)
    i.thumbnail(output_size)
    i.save(thumbnail_path)
    return thumbnail_path

def list_to_dict(items_list):
    items_dict = [{'id': item[0], 'name': item[1], 'warranty_dur': item[2],'date_bought': item[3], 'thumbnail': item[4], 'warranty_expiration_date': item[5]} for item in items_list]
    for item in items_dict:

        if item['thumbnail']:
            item['thumbnail'] = item['thumbnail'].replace(os.sep, '/')
    return items_dict


@app.route('/', methods=['GET'])
@app.route('/home', methods=['GET'])
def home():
    if not os.path.exists(DATABASE):
        create_database()
    closest_items = list_to_dict(get_closest_expiration())
    recent_items = list_to_dict(get_recent_items())
    app.logger.info(f"Closest items: {closest_items}")
    app.logger.info("################################")
    app.logger.info(f"Recent items: {recent_items}")
    return render_template('home.html', closest_items=closest_items, recent_items=recent_items)

@app.route('/item_page/<int:item_id>', methods=['GET']) # TODO: Move 
def item_page(item_id):
    item = get_item_by_id(item_id)
    if item:
        expiration_date = datetime.strptime(item[5], "%Y-%m-%d").date()
        buying_date = datetime.strptime(item[3], "%Y-%m-%d").date()

        days_to_expiration = days_until_expiration(expiration_date)
        total_warranty_days = (expiration_date - buying_date).days

        progress_width = (days_to_expiration / total_warranty_days) * 100
        
        if item[4]:
            thumbnail_file = os.path.basename(item[4])
            thumbnail_path = os.path.join('uploads/' 'products_thumbnails/', thumbnail_file)
        else: 
            thumbnail_path = os.path.join('uploads/' 'products_thumbnails/', 'default_product.png')
        
        return render_template('item_page.html', item=item, file_path=thumbnail_path, days_to_expiration=days_to_expiration, progress_width=progress_width)
        
    else:
        return "Item not found", 404
    
@app.route('/add', methods=['GET', 'POST'])
def add_item_route():
    if request.method == 'POST':
        name = request.form['name']
        warranty_dur = int(request.form['warranty_dur'])
        date_bought = request.form['date_bought']
        warranty_expiration_date = calculate_expiration_date(warranty_dur)
        
        thumbnail = request.files.get('thumbnail')
        thumbnail_path = None
        thumbnail_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'products_thumbnails')

        if thumbnail:
            random_filename = str(uuid.uuid4()) + os.path.splitext(thumbnail.filename)[1]
            os.makedirs(thumbnail_dir, exist_ok=True) 
            thumbnail_path = os.path.join(thumbnail_dir, random_filename)
            thumbnail.save(thumbnail_path)
            save_resize_thumbnail(thumbnail_path, 100)

        else: 
            thumbnail_path = os.path.join(thumbnail_dir, 'default_product.png')
            save_resize_thumbnail(thumbnail_path, 100)
            
        thumbnail_path = thumbnail_path.replace(os.sep, '/')
        add_item_database(name, warranty_dur, date_bought, thumbnail_path, warranty_expiration_date)
        return redirect('/')
    return render_template('add_item.html')

@app.route('/update/<int:item_id>', methods=['GET', 'POST'])
def update_item_route(item_id):
    item = get_item_by_id(item_id)
    if item:
        if request.method == 'POST':
            name = request.form['name']
            warranty_dur = int(request.form['warranty_dur'])
            date_bought = request.form['date_bought']
            warranty_expiration_date = calculate_expiration_date(warranty_dur)

            thumbnail_img = request.files.get('thumbnail').close
            thumbnail_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'products_thumbnails')
            thumbnail_img = None

            if thumbnail_img:
                random_filename = str(uuid.uuid4())+'.png'
                os.makedirs(thumbnail_dir, exist_ok=True) 
                thumbnail_path = os.path.join(thumbnail_dir, random_filename)
                
            else:
                thumbnail_path = os.path.join(thumbnail_dir, 'default_product.png')
            
            thumbnail_path = thumbnail_path.replace(os.sep, '/')
            save_resize_thumbnail(thumbnail_path, 100)
            update_item_database(item_id, name, warranty_dur, date_bought, thumbnail_path, warranty_expiration_date)
            return redirect('/')
        
        item = get_item_by_id(item_id)
        return render_template('update_item.html', item=item)

@app.route('/full_list', methods=['GET'])
def full_list():
    items_list = get_all_items()
    items_dict = list_to_dict(items_list=items_list)
    return render_template('full_list.html', items=items_dict)


@app.route('/delete/<int:item_id>', methods=['POST', 'GET'])
def delete_item_route(item_id):
    delete_item_database(item_id)
    return redirect('/full_list')


@app.route('/delete_all', methods=['POST', 'GET'])
def delete_all_items_route():
    delete_all_items()
    return redirect('/')

@app.route('/closest_to_expiry')
def closest_to_expiry():
    items_list =  get_closest_expiration() 
    items_dict = list_to_dict(items_list=items_list)
    return render_template('closest_to_expiry.html', closest_items=items_dict)

@app.route('/recently_added')
def recently_added():
    items_list = get_recent_items()
    items_dict = list_to_dict(items_list=items_list)
    return render_template('recently_added.html', recent_items=items_dict)

if __name__ == '__main__':
    app.run(debug=True)