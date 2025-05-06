from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, current_user, login_user, logout_user
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DecimalField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'секретный-ключ-для-разработки'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///swagcraft.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
limiter = Limiter(app=app, key_func=get_remote_address)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    orders = db.relationship('Order', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(20), nullable=False)
    image = db.Column(db.String(100), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='в обработке')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class ProductForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    price = DecimalField('Цена', validators=[DataRequired()])
    category = SelectField('Категория', choices=[('футболка', 'Футболка'), ('толстовка', 'Толстовка')])
    stock = IntegerField('Количество', validators=[DataRequired()])
    image = StringField('Изображение', validators=[DataRequired()])
    submit = SubmitField('Сохранить')

class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('login'))
        return super(MyAdminIndexView, self).index()

admin = Admin(app, name='SWAGcraft Админ', template_mode='bootstrap4', index_view=MyAdminIndexView())
admin.add_view(SecureModelView(User, db.session))
admin.add_view(SecureModelView(Product, db.session))
admin.add_view(SecureModelView(Order, db.session))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    featured_products = Product.query.limit(4).all()
    return render_template('index.html', products=featured_products)

@app.route('/catalog')
def catalog():
    category = request.args.get('category')
    if category:
        products = Product.query.filter_by(category=category).all()
    else:
        products = Product.query.all()
    return render_template('catalog.html', products=products)

@app.route('/cart')
@login_required
def cart():
    if 'cart' not in session:
        session['cart'] = []
    products = []
    total = 0
    for item in session['cart']:
        product = Product.query.get(item['product_id'])
        if product:
            products.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': item['quantity'],
                'image': product.image,
                'description': product.description
            })
            total += product.price * item['quantity']
    return render_template('cart.html', products=products, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []
    quantity = int(request.form.get('quantity', 1))
    product = Product.query.get_or_404(product_id)
    if quantity > product.stock:
        flash('Недостаточно товара в наличии', 'danger')
        return redirect(url_for('catalog'))
    for item in session['cart']:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            if item['quantity'] > product.stock:
                flash('Недостаточно товара в наличии', 'danger')
                return redirect(url_for('catalog'))
            break
    else:
        session['cart'].append({
            'product_id': product_id,
            'quantity': quantity
        })
    session.modified = True
    flash('Товар добавлен в корзину', 'success')
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if item['product_id'] != product_id]
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if not session.get('cart'):
        return redirect(url_for('cart'))
    if request.method == 'POST':
        order = Order(
            user_id=current_user.id,
            total=sum(item['price'] * item['quantity'] for item in session['cart'])
        )
        db.session.add(order)
        for item in session['cart']:
            product = Product.query.get(item['product_id'])
            if product:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=item['quantity'],
                    price=product.price
                )
                product.stock -= item['quantity']
                db.session.add(order_item)
        db.session.commit()
        session.pop('cart')
        flash('Заказ успешно оформлен!', 'success')
        return redirect(url_for('index'))
    products = []
    total = 0
    for item in session['cart']:
        product = Product.query.get(item['product_id'])
        if product:
            products.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': item['quantity'],
                'image': product.image
            })
            total += product.price * item['quantity']
    return render_template('checkout.html', products=products, total=total)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/') or next_page.startswith('/add_to_cart'):
                next_page = url_for('index')
            return redirect(next_page)
        flash('Неверный email или пароль', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("Сайт доступен по адресу: http://127.0.0.1:8080")
    app.run(host='127.0.0.1', port=8080, debug=True) 