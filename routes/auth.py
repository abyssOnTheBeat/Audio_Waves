from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from extensions import db
from models import User


ALLOWED_ROLES = {'user', 'beatmaker'}


def register_auth_routes(app):
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            selected_role = request.form.get('role', 'user').strip().lower()

            if not username or not email or not password:
                flash('Заполните все поля.', 'danger')
                return redirect(url_for('register'))
            if password != confirm_password:
                flash('Пароли не совпадают.', 'danger')
                return redirect(url_for('register'))
            if len(password) < 6:
                flash('Пароль должен быть не короче 6 символов.', 'danger')
                return redirect(url_for('register'))
            if User.query.filter((User.username == username) | (User.email == email)).first():
                flash('Такой пользователь уже существует.', 'danger')
                return redirect(url_for('register'))
            if selected_role not in ALLOWED_ROLES:
                selected_role = 'user'

            role = 'admin' if User.query.count() == 0 else selected_role
            user = User(username=username, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Регистрация прошла успешно.', 'success')
            return redirect(url_for('profile'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':
            login_value = request.form.get('login', '').strip().lower()
            password = request.form.get('password', '')
            remember = bool(request.form.get('remember'))

            user = User.query.filter((User.email == login_value) | (User.username == login_value)).first()
            if user and user.check_password(password):
                login_user(user, remember=remember)
                flash('Вы вошли в аккаунт.', 'success')
                return redirect(url_for('profile'))

            flash('Неверный логин или пароль.', 'danger')
            return redirect(url_for('login'))

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Вы вышли из аккаунта.', 'success')
        return redirect(url_for('index'))
