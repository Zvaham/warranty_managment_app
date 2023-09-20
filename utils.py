import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from PIL import Image


def calculate_expiration_date(warranty_dur, duration_type):
    current_date = datetime.now()
    if duration_type == "days":
        future_date = (current_date + relativedelta(days=warranty_dur)).date()
    elif duration_type == "months":
        future_date = (current_date + relativedelta(months=warranty_dur)).date()
    else:
        future_date = None
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
