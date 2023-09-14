from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy


from app import app

db = SQLAlchemy(app)

class List(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    items = db.relationship('Item', backref='list', lazy=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    warranty_dur = db.Column(db.Integer, nullable=False)
    date_bought = db.Column(db.DateTime, nullable=False)
    thumbnail = db.Column(db.String(100), nullable=False)
    warranty_expiration_date = db.Column(db.DateTime, nullable=False)


db.create_all()
