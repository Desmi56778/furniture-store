from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')  # user, employee, admin
    phone = db.Column(db.String(20), default='')
    address = db.Column(db.Text, default='')
    payment_method = db.Column(db.String(30), default='')  # "карта", "наличные", "чек оплаты"
    avatar_url = db.Column(db.String(255), default='')
    balance = db.Column(db.Float, default=0.0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), default='https://via.placeholder.com/300')
    stock = db.Column(db.Integer, default=0)         # остаток на складе
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer, default=1)
    product = db.relationship('Product')

class WishlistItem(db.Model):
    __tablename__ = 'wishlist_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    product = db.relationship('Product')

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Новое: детальный статус (текстовый, можно задавать любой)
    status = db.Column(db.String(100), default='В обработке')
    # Комментарий к статусу (например, "Ожидается на складе")
    status_comment = db.Column(db.Text, default='')

    # Предполагаемая дата доставки (генерируется при создании заказа)
    estimated_delivery = db.Column(db.Date, nullable=True)

    is_paid = db.Column(db.Boolean, default=False)
    installment = db.Column(db.Boolean, default=False)
    total = db.Column(db.Float, default=0.0)
    shipping_address = db.Column(db.Text, default='')
    payment_method = db.Column(db.String(30), default='')
    phone = db.Column(db.String(20), default='')
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    user = db.relationship('User', backref='orders')

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    product = db.relationship('Product')

class Request(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='новый')  # новый, в обработке, закрыт
    admin_response = db.Column(db.Text, nullable=True)

    amount = db.Column(db.Float, nullable=True)
    payment_method = db.Column(db.String(30), nullable=True)

    employee = db.relationship('User', backref='requests')
    photos = db.relationship('RequestPhoto', backref='request', lazy=True, cascade='all, delete-orphan')

class RequestPhoto(db.Model):
    __tablename__ = 'request_photos'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)