from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Product, Category, CartItem, WishlistItem, Order, OrderItem, Request, RequestPhoto
from config import Config
from forms import LoginForm, RegisterForm, ProductForm, RequestForm, ProfileForm, ReplenishForm
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import random



app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------- Главная (каталог) ----------
@app.route('/')
def index():
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    products = query.all()
    categories = Category.query.all()
    return render_template('index.html', products=products, categories=categories)

# ---------- Авторизация ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверный email или пароль')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Пользователь с таким email уже существует')
        else:
            user = User(email=form.email.data, name=form.name.data, phone=form.phone.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ---------- Корзина и избранное ----------
@app.route('/cart')
@login_required
def cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    return render_template('cart.html', items=items)

@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        item.quantity += 1
    else:
        item = CartItem(user_id=current_user.id, product_id=product_id)
        db.session.add(item)
    db.session.commit()
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('cart'))

@app.route('/wishlist')
@login_required
def wishlist():
    items = WishlistItem.query.filter_by(user_id=current_user.id).all()
    return render_template('wishlist.html', items=items)

@app.route('/add_to_wishlist/<int:product_id>')
@login_required
def add_to_wishlist(product_id):
    if not WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first():
        db.session.add(WishlistItem(user_id=current_user.id, product_id=product_id))
        db.session.commit()
    return redirect(url_for('wishlist'))

@app.route('/remove_from_wishlist/<int:product_id>')
@login_required
def remove_from_wishlist(product_id):
    item = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('wishlist'))

# ---------- Оформление заказа (пользователь) ----------
@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    if not current_user.name or not current_user.phone or not current_user.address or not current_user.payment_method:
        flash(
            'Пожалуйста, заполните профиль: ФИО, телефон, адрес доставки и способ платежа обязательны для оформления заказа.')
        return redirect(url_for('profile'))

    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Корзина пуста')
        return redirect(url_for('cart'))

    total = sum(item.product.price * item.quantity for item in cart_items)

    # Дата доставки: текущая дата + случайное число дней от 4 до 10
    delivery_date = datetime.now().date() + timedelta(days=random.randint(4, 10))

    order = Order(
        user_id=current_user.id,
        total=total,
        is_paid=False,
        shipping_address=current_user.address,
        payment_method=current_user.payment_method,
        phone=current_user.phone,
        status='В обработке',
        estimated_delivery=delivery_date
    )
    db.session.add(order)
    db.session.flush()

    for item in cart_items:
        db.session.add(OrderItem(order_id=order.id, product_id=item.product_id,
                                 quantity=item.quantity, price=item.product.price))
        db.session.delete(item)
    db.session.commit()
    flash('Заказ оформлен')
    return redirect(url_for('orders'))

@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=user_orders)


@app.route('/employee')
@login_required
def employee_dashboard():
    if current_user.role not in ('employee', 'admin'):
        abort(403)

    # Параметры поиска
    search_order_id = request.args.get('order_id', type=int)
    search_user_id = request.args.get('user_id', type=int)
    search_product = request.args.get('product_search', '').strip()

    # Товары
    products_query = Product.query
    if search_product:
        # Поиск по названию (или можно добавить поиск по ID, если введено число)
        if search_product.isdigit():
            products_query = products_query.filter(
                (Product.name.ilike(f'%{search_product}%')) | (Product.id == int(search_product))
            )
        else:
            products_query = products_query.filter(Product.name.ilike(f'%{search_product}%'))
    products = products_query.all()

    # Пользователи
    users_query = User.query.filter_by(role='user')
    if search_user_id:
        users_query = users_query.filter(User.id == search_user_id)
    users = users_query.all()

    # Заказы
    orders_query = Order.query
    if search_order_id:
        orders_query = orders_query.filter(Order.id == search_order_id)
    orders = orders_query.order_by(Order.created_at.desc()).all()

    return render_template('employee/dashboard.html',
                           products=products,
                           users=users,
                           orders=orders,
                           search_order_id=search_order_id,
                           search_user_id=search_user_id,
                           search_product=search_product)

@app.route('/employee/order/<int:order_id>')
@login_required
def employee_order_detail(order_id):
    if current_user.role not in ('employee', 'admin'):
        abort(403)
    order = Order.query.get_or_404(order_id)
    return render_template('employee/order_detail.html', order=order)

# ---------- Администратор ----------
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        abort(403)
    employees = User.query.filter(User.role.in_(['employee', 'admin'])).all()
    products = Product.query.all()
    return render_template('admin/dashboard.html', employees=employees, products=products)


@app.route('/admin/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'admin':
        abort(403)
    form = ProductForm()
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]
    if form.validate_on_submit():
        # Обработка изображения
        if form.image.data:
            # Безопасное имя файла
            filename = secure_filename(form.image.data.filename)
            # Уникальное имя, чтобы не было конфликтов
            unique_name = f"{int(datetime.utcnow().timestamp())}_{filename}"
            # Путь сохранения
            save_path = os.path.join(app.root_path, 'static', 'uploads', 'products', unique_name)
            # Сохраняем файл
            form.image.data.save(save_path)
            image_url = f'uploads/products/{unique_name}'
        else:
            image_url = 'https://via.placeholder.com/300'  # заглушка, если картинка не загружена

        p = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock=form.stock.data,
            category_id=form.category.data,
            image_url=image_url
        )
        db.session.add(p)
        db.session.commit()
        flash('Товар добавлен')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_product.html', form=form)


@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if current_user.role != 'admin':
        abort(403)

    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)  # Заполняем форму текущими данными товара

    # Заполняем список категорий
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        # Обновляем поля товара
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.stock = form.stock.data
        product.category_id = form.category.data

        # Обработка изображения (если загружено новое)
        if form.image.data:
            # Удаляем старый файл, если это локальное изображение (не http-ссылка)
            if product.image_url and not product.image_url.startswith('http'):
                old_file_path = os.path.join(app.root_path, 'static', product.image_url)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

            # Сохраняем новый файл
            filename = secure_filename(form.image.data.filename)
            unique_name = f"{int(datetime.utcnow().timestamp())}_{filename}"
            save_path = os.path.join(app.root_path, 'static', 'uploads', 'products', unique_name)
            form.image.data.save(save_path)
            product.image_url = f'uploads/products/{unique_name}'

        # Если изображение не загружено, оставляем старое значение без изменений

        db.session.commit()
        flash('Товар обновлён')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/edit_product.html', form=form, product=product)

@app.route('/admin/users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        abort(403)
    employees = User.query.filter(User.role != 'user').all()
    return render_template('admin/manage_users.html', employees=employees)

@app.route('/admin/promote/<int:user_id>')
@login_required
def promote_user(user_id):
    if current_user.role != 'admin':
        abort(403)
    user = User.query.get_or_404(user_id)
    if user.role == 'user':
        user.role = 'employee'
        db.session.commit()
    return redirect(url_for('manage_users'))

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    # Похожие товары (из той же категории, кроме текущего)
    related = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id
    ).limit(4).all()
    return render_template('product.html', product=product, related_products=related)

@app.route('/my_order/<int:order_id>')
@login_required

def user_order_detail(order_id):
    # Ищем заказ, который принадлежит текущему пользователю
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('user_order_detail.html', order=order)

# ---------- Запросы сотрудника ----------
@app.route('/employee/requests')
@login_required
def employee_requests():
    if current_user.role != 'employee':
        abort(403)
    user_requests = Request.query.filter_by(employee_id=current_user.id).order_by(Request.created_at.desc()).all()
    return render_template('employee/requests.html', requests=user_requests)

@app.route('/employee/request/new', methods=['GET', 'POST'])
@login_required
def new_request():
    if current_user.role != 'employee':
        abort(403)
    form = RequestForm()
    if form.validate_on_submit():
        req = Request(
            employee_id=current_user.id,
            subject=form.subject.data,
            body=form.body.data
        )
        db.session.add(req)
        db.session.flush()  # чтобы получить req.id

        # Сохранение фотографий
        if form.images.data:
            for img in form.images.data:
                if img.filename:  # проверка, что файл выбран
                    filename = secure_filename(img.filename)
                    unique_name = f"{int(datetime.utcnow().timestamp())}_{filename}"
                    save_path = os.path.join(app.root_path, 'static', 'uploads', 'requests', unique_name)
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    img.save(save_path)
                    photo = RequestPhoto(request_id=req.id, filename=f'uploads/requests/{unique_name}')
                    db.session.add(photo)
        db.session.commit()
        flash('Запрос отправлен администратору')
        return redirect(url_for('employee_requests'))
    return render_template('employee/request_form.html', form=form)

# ---------- Запросы для администратора ----------
@app.route('/admin/requests')
@login_required
def admin_requests():
    if current_user.role != 'admin':
        abort(403)

    # Получаем параметры фильтрации
    search_id = request.args.get('request_id', type=int)
    search_employee = request.args.get('employee', '').strip()
    search_subject = request.args.get('subject', '').strip()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    status = request.args.get('status', '')
    amount_min = request.args.get('amount_min', type=float)
    amount_max = request.args.get('amount_max', type=float)

    query = Request.query

    if search_id:
        query = query.filter(Request.id == search_id)
    if search_employee:
        # Поиск по имени или ID сотрудника
        if search_employee.isdigit():
            query = query.filter(Request.employee_id == int(search_employee))
        else:
            query = query.join(User, Request.employee_id == User.id).filter(
                User.name.ilike(f'%{search_employee}%')
            )
    if search_subject:
        query = query.filter(Request.subject.ilike(f'%{search_subject}%'))
    if date_from:
        query = query.filter(Request.created_at >= date_from)
    if date_to:
        query = query.filter(Request.created_at <= date_to)
    if status:
        query = query.filter(Request.status == status)
    if amount_min is not None:
        query = query.filter(Request.amount >= amount_min)
    if amount_max is not None:
        query = query.filter(Request.amount <= amount_max)

    requests_list = query.order_by(Request.created_at.desc()).all()

    return render_template('admin/requests.html',
                           requests=requests_list,
                           search_id=search_id,
                           search_employee=search_employee,
                           search_subject=search_subject,
                           date_from=date_from,
                           date_to=date_to,
                           status=status,
                           amount_min=amount_min,
                           amount_max=amount_max)

@app.route('/admin/request/<int:request_id>', methods=['GET', 'POST'])
@login_required
def admin_request_detail(request_id):
    if current_user.role != 'admin':
        abort(403)
    req = Request.query.get_or_404(request_id)
    if request.method == 'POST':
        admin_response = request.form.get('admin_response')
        new_status = request.form.get('status')
        if admin_response:
            req.admin_response = admin_response
        if new_status in ('в обработке', 'закрыт'):
            req.status = new_status
        db.session.commit()
        flash('Ответ сохранён')
        return redirect(url_for('admin_request_detail', request_id=req.id))
    return render_template('admin/request_detail.html', req=req)

@app.route('/employee/request/<int:request_id>')
@login_required
def employee_request_detail(request_id):
    if current_user.role != 'employee':
        abort(403)
    req = Request.query.filter_by(id=request_id, employee_id=current_user.id).first_or_404()
    return render_template('employee/request_detail.html', req=req)

@app.route('/employee/request/delete/<int:request_id>', methods=['POST'])
@login_required
def delete_request(request_id):
    if current_user.role != 'employee':
        abort(403)
    # Ищем запрос, принадлежащий текущему сотруднику
    req = Request.query.filter_by(id=request_id, employee_id=current_user.id).first_or_404()
    # Удаляем файлы фотографий с диска
    for photo in req.photos:
        file_path = os.path.join(app.root_path, 'static', photo.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    db.session.delete(req)
    db.session.commit()
    flash('Запрос удалён.')
    return redirect(url_for('employee_requests'))

@app.route('/employee/user/<int:user_id>/orders')
@login_required
def employee_user_orders(user_id):
    if current_user.role not in ('employee', 'admin'):
        abort(403)
    user = User.query.get_or_404(user_id)
    if user.role != 'user':
        flash('Это не обычный пользователь')
        return redirect(url_for('employee_dashboard'))
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    return render_template('employee/user_orders.html', user=user, orders=orders)

@app.route('/order/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    # Проверяем права: либо владелец заказа, либо администратор
    if current_user.id != order.user_id and current_user.role != 'admin':
        abort(403)
    # Нельзя отменить доставленный или уже отменённый заказ
    if order.status in ['доставлен', 'отменен']:
        flash('Заказ в текущем статусе отменить нельзя.')
        return redirect(request.referrer or url_for('orders'))
    order.status = 'отменен'
    db.session.commit()
    flash('Заказ отменён.')
    return redirect(request.referrer or url_for('orders'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        current_user.payment_method = form.payment_method.data

        # Обработка аватара
        if form.avatar.data:
            filename = secure_filename(form.avatar.data.filename)
            unique_name = f"{int(datetime.utcnow().timestamp())}_{filename}"
            save_path = os.path.join(app.root_path, 'static', 'uploads', 'avatars', unique_name)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            form.avatar.data.save(save_path)
            # Удалить старый аватар, если был
            if current_user.avatar_url and current_user.avatar_url != 'default.png':
                old_path = os.path.join(app.root_path, 'static', current_user.avatar_url)
                if os.path.exists(old_path):
                    os.remove(old_path)
            current_user.avatar_url = f'uploads/avatars/{unique_name}'

        db.session.commit()
        flash('Профиль обновлён')
        return redirect(url_for('profile'))
    return render_template('profile.html', form=form, user=current_user)

@app.route('/admin/add_balance/<int:user_id>', methods=['POST'])
@login_required
def add_balance(user_id):
    if current_user.role != 'admin':
        abort(403)
    user = User.query.get_or_404(user_id)
    amount = request.form.get('amount', type=float)
    if amount is None or amount <= 0:
        flash('Введите положительную сумму')
        return redirect(url_for('admin_dashboard'))
    user.balance += amount
    db.session.commit()
    flash(f'Баланс пользователя {user.name} пополнен на {amount} ₽')
    return redirect(url_for('admin_dashboard'))


@app.route('/replenish', methods=['GET', 'POST'])
@login_required
def replenish():
    form = ReplenishForm()
    if form.validate_on_submit():
        # Формируем описание запроса
        if form.payment_method.data == 'card':
            details = (f"Пользователь хочет пополнить баланс на {form.amount.data} ₽.\n"
                       f"Способ: банковская карта.\n"
                       f"Номер карты: {form.card_number.data}\n"
                       f"Срок действия: {form.card_expiry.data}\n"
                       f"CVV: {form.card_cvv.data}")
        else:  # phone
            details = (f"Пользователь хочет пополнить баланс на {form.amount.data} ₽.\n"
                       f"Способ: перевод на номер телефона +7 961 731 62 14.\n"
                       f"Ожидайте подтверждения администратора.")

        req = Request(
            employee_id=current_user.id,  # отправитель – текущий пользователь (может быть любая роль)
            subject=f"Пополнение баланса на {form.amount.data} ₽",
            body=details,
            amount=form.amount.data,
            payment_method=form.payment_method.data,
            status='новый'
        )
        db.session.add(req)
        db.session.commit()
        flash('Запрос на пополнение отправлен администратору.')
        return redirect(url_for('profile'))
    return render_template('replenish.html', form=form)

@app.route('/admin/request/<int:request_id>/approve', methods=['POST'])
@login_required
def approve_replenish(request_id):
    if current_user.role != 'admin':
        abort(403)
    req = Request.query.get_or_404(request_id)
    # Проверяем, что это запрос на пополнение (amount > 0)
    if not req.amount or req.amount <= 0:
        flash('Этот запрос не является пополнением баланса.')
        return redirect(url_for('admin_request_detail', request_id=req.id))
    # Начисляем баланс отправителю запроса
    user = User.query.get(req.employee_id)
    if user:
        user.balance += req.amount
        req.status = 'закрыт'
        req.admin_response = f"Пополнение на {req.amount} ₽ подтверждено. Баланс обновлён."
        db.session.commit()
        flash(f'Баланс пользователя {user.name} пополнен на {req.amount} ₽.')
    else:
        flash('Пользователь не найден.')
    return redirect(url_for('admin_request_detail', request_id=req.id))

@app.route('/order/<int:order_id>/pay', methods=['POST'])
@login_required
def pay_order(order_id):
    order = Order.query.get_or_404(order_id)
    # Только владелец заказа
    if current_user.id != order.user_id:
        abort(403)
    if order.is_paid:
        flash('Заказ уже оплачен.')
        return redirect(url_for('orders'))
    if order.status == 'отменен':
        flash('Нельзя оплатить отменённый заказ.')
        return redirect(url_for('orders'))
    if current_user.balance < order.total:
        flash('Недостаточно средств на балансе.')
        return redirect(url_for('orders'))
    # Списываем деньги
    current_user.balance -= order.total
    order.is_paid = True
    db.session.commit()
    flash('Спасибо за покупку!')
    return redirect(url_for('orders'))

@app.route('/order/<int:order_id>/update_status', methods=['POST'])
@login_required
def update_order_status(order_id):
    if current_user.role not in ('employee', 'admin'):
        abort(403)
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status', '').strip()
    comment = request.form.get('status_comment', '').strip()
    if new_status:
        order.status = new_status
    if comment:
        order.status_comment = comment
    db.session.commit()
    flash('Статус заказа обновлён.')
    return redirect(request.referrer or url_for('employee_dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)