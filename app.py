import uuid
from utils.utils import *
from utils.database import *
from utils.cal_utils import *
from flask import Flask, render_template, request, redirect, url_for


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'


@app.route('/', methods=['GET'])
@app.route('/home', methods=['GET'])
def home():
    if not os.path.exists(DATABASE):
        create_database()
    closest_items = list_to_dict(get_closest_expiration())
    recent_items = list_to_dict(get_recent_items())

    return render_template('home.html', closest_items=closest_items, recent_items=recent_items)


@app.route('/add', methods=['GET', 'POST'])
def add_item_route():
    if request.method == 'POST':
        name = request.form['name']
        warranty_dur = int(request.form['warranty_dur'])
        date_bought = request.form['date_bought']
        warranty_expiration_date = calculate_expiration_date(warranty_dur=warranty_dur, duration_type='months')

        thumbnail = request.files.get('thumbnail')
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


@app.route('/item_page/<int:item_id>', methods=['GET'])
def item_page(item_id):
    item = get_item_by_id(item_id)
    if item:
        expiration_date = datetime.datetime.strptime(item[5], "%Y-%m-%d").date()
        buying_date = datetime.datetime.strptime(item[3], "%Y-%m-%d").date()

        days_to_expiration = days_until_expiration(expiration_date)
        total_warranty_days = (expiration_date - buying_date).days

        progress_width = (days_to_expiration / total_warranty_days) * 100
        
        if item[4]:
            thumbnail_file = os.path.basename(item[4])
            thumbnail_path = os.path.join('uploads/' 'products_thumbnails/', thumbnail_file)
        else: 
            thumbnail_path = os.path.join('uploads/' 'products_thumbnails/', 'default_product.png')
        
        return render_template('item_page.html', item=item, file_path=thumbnail_path, days_to_expiration=days_to_expiration,
                               progress_width=progress_width)
        
    else:
        return "Item not found", 404
    

@app.route('/update/<int:item_id>', methods=['GET', 'POST'])
def update_item_route(item_id):
    item = get_item_by_id(item_id)
    if item:
        if request.method == 'POST':
            name = request.form['name']
            warranty_dur = int(request.form['warranty_dur'])
            date_bought = request.form['date_bought']
            warranty_expiration_date = calculate_expiration_date(warranty_dur=warranty_dur, duration_type='months')

            thumbnail_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'products_thumbnails')

            if request.files.get('thumbnail').close:
                random_filename = str(uuid.uuid4())+'.png'
                os.makedirs(thumbnail_dir, exist_ok=True) 
                thumbnail_path = os.path.join(thumbnail_dir, random_filename)
                
            else:
                thumbnail_path = os.path.join(thumbnail_dir, 'default_product.png')
            
            thumbnail_path = thumbnail_path.replace(os.sep, '/')
            save_resize_thumbnail(thumbnail_path, 100)
            update_item_database(item_id, name, warranty_dur, date_bought, thumbnail_path, warranty_expiration_date)
            return redirect(url_for('item_page', item_id=item_id))
        
        item = get_item_by_id(item_id)
        return render_template('update_item.html', item=item)


@app.route('/delete/<int:item_id>', methods=['POST', 'GET'])
def delete_item_route(item_id):
    delete_item_database(item_id)
    return redirect('/full_list')


@app.route('/delete_all', methods=['POST', 'GET'])
def delete_all_items_route():
    delete_all_items()
    return redirect('/')


@app.route('/full_list', methods=['GET'])
def full_list_route():
    items_list = get_all_items()
    items_dict = list_to_dict(items_list=items_list)
    return render_template('full_list.html', items=items_dict)


@app.route('/closest_expiry')
def closest_expiry_route():
    items_list = get_closest_expiration()
    items_dict = list_to_dict(items_list=items_list)
    return render_template('closest_to_expiry.html', closest_items=items_dict)


@app.route('/recently_added')
def recently_added_route():
    items_list = get_recent_items()
    items_dict = list_to_dict(items_list=items_list)
    return render_template('recently_added.html', recent_items=items_dict)


@app.route('/add_calendar_reminder/<int:item_id>', methods=['GET', 'POST'])
def add_calendar_reminder_route(item_id):
    item = get_item_by_id(item_id)

    if item:
        if request.method == 'POST':
            reminder_number = int(request.form['reminder_number'])
            reminder_type = request.form['reminder_type']
            additional_reminder = 'additional_reminder' in request.form

            warranty_expiration_date = datetime.datetime.strptime(item[5], '%Y-%m-%d').date()

            if reminder_type == "days":
                reminder_date = warranty_expiration_date - relativedelta(days=reminder_number)
            elif reminder_type == "months":
                reminder_date = warranty_expiration_date - relativedelta(months=reminder_number)
            else:
                reminder_date = None 

            print(f"Warranty Expiration Date: {warranty_expiration_date}")
            print(f"Reminder Date: {reminder_date}")
            print(f"Additional Event: {additional_reminder}")

            summary = f"Warranty Reminder For {item[1]}"
            description = f"""Warranty for item: {item[1]} will expire in {reminder_number} {reminder_type} at {warranty_expiration_date}. 
            We recommend to check the device for issues and use the warranty if necessary!."""
            
            params = EventParams(summary=summary, start_date_input=reminder_date, end_date_input=reminder_date, description=description)

            creds = verify_token(credentials_source_path)
            event = create_events(params, creds)
            return redirect(url_for('item_page', item_id=item_id, cal_event_link=event['htmlLink']))
    else:
        return "Item not found", 404

    return render_template('add_calendar_reminder.html', item_id=item_id)


if __name__ == '__main__':
    app.run(debug=True)
