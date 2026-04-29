from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    favorites = db.relationship('Favorite', backref='user', cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='user', cascade='all, delete-orphan')
    submitted_beats = db.relationship('Beat', backref='submitted_by', cascade='all', foreign_keys='Beat.submitted_by_user_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_beatmaker(self):
        return self.role == 'beatmaker'


class Beat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    mood = db.Column(db.String(80), nullable=False)
    bpm = db.Column(db.Integer, nullable=False)
    beat_key = db.Column(db.String(30), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, default='')
    preview_file = db.Column(db.String(255), nullable=False)
    cover_file = db.Column(db.String(255), nullable=False, default='default-cover.jpg')
    is_featured = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='approved', nullable=False)
    submitted_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    moderation_note = db.Column(db.String(255), default='', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    favorites = db.relationship('Favorite', backref='beat', cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='beat', cascade='all, delete-orphan')

    @property
    def is_visible(self):
        return self.status == 'approved'


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    beat_id = db.Column(db.Integer, db.ForeignKey('beat.id'), nullable=False)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    beat_id = db.Column(db.Integer, db.ForeignKey('beat.id'), nullable=False)
