from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from config import UPLOAD_COVERS, UPLOAD_PREVIEWS
from extensions import db
from models import Beat, CartItem, Favorite
from services import allowed_audio, allowed_image, save_uploaded_file


def register_store_routes(app):
    @app.route('/profile')
    @login_required
    def profile():
        favorites = Beat.query.join(Favorite, Favorite.beat_id == Beat.id).filter(Favorite.user_id == current_user.id).all()
        cart_items = Beat.query.join(CartItem, CartItem.beat_id == Beat.id).filter(CartItem.user_id == current_user.id).all()
        cart_total = sum(item.price for item in cart_items)
        submitted_beats = []
        if current_user.is_beatmaker:
            submitted_beats = Beat.query.filter_by(submitted_by_user_id=current_user.id).order_by(Beat.created_at.desc()).all()
        return render_template('profile.html', favorites=favorites, cart_items=cart_items, cart_total=cart_total, submitted_beats=submitted_beats)

    @app.route('/beatmaker/upload', methods=['POST'])
    @login_required
    def beatmaker_upload():
        if not current_user.is_beatmaker and not current_user.is_admin:
            abort(403)

        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        mood = request.form.get('mood', '').strip()
        bpm = request.form.get('bpm', '').strip()
        beat_key = request.form.get('beat_key', '').strip()
        price = request.form.get('price', '').strip()
        description = request.form.get('description', '').strip()
        preview = request.files.get('preview')
        cover = request.files.get('cover')

        if not title or not category or not mood or not bpm or not beat_key or not price or not preview:
            flash('Для отправки на модерацию заполните все обязательные поля и загрузите превью.', 'danger')
            return redirect(url_for('profile'))
        if not allowed_audio(preview.filename):
            flash('Превью должно быть в формате mp3, wav, ogg или m4a.', 'danger')
            return redirect(url_for('profile'))
        if cover and cover.filename and not allowed_image(cover.filename):
            flash('Обложка должна быть в формате png, jpg, jpeg или webp.', 'danger')
            return redirect(url_for('profile'))

        preview_name = save_uploaded_file(preview, UPLOAD_PREVIEWS)
        cover_name = 'default-cover.jpg'
        if cover and cover.filename:
            saved_cover = save_uploaded_file(cover, UPLOAD_COVERS)
            if saved_cover:
                cover_name = saved_cover

        beat = Beat(
            title=title,
            category=category,
            mood=mood,
            bpm=int(bpm),
            beat_key=beat_key,
            price=float(price),
            description=description,
            preview_file=preview_name,
            cover_file=cover_name,
            is_featured=False,
            status='pending',
            submitted_by_user_id=current_user.id,
            moderation_note='Ожидает проверки администратора',
        )
        db.session.add(beat)
        db.session.commit()
        flash('Бит отправлен на модерацию.', 'success')
        return redirect(url_for('profile'))

    @app.route('/favorite/<int:beat_id>')
    @login_required
    def toggle_favorite(beat_id):
        beat = db.session.get(Beat, beat_id)
        if not beat or beat.status != 'approved':
            abort(404)

        item = Favorite.query.filter_by(user_id=current_user.id, beat_id=beat_id).first()
        if item:
            db.session.delete(item)
            flash('Бит убран из избранного.', 'success')
        else:
            db.session.add(Favorite(user_id=current_user.id, beat_id=beat_id))
            flash('Бит добавлен в избранное.', 'success')
        db.session.commit()
        return redirect(request.referrer or url_for('index'))

    @app.route('/cart/add/<int:beat_id>')
    @login_required
    def add_to_cart(beat_id):
        beat = db.session.get(Beat, beat_id)
        if not beat or beat.status != 'approved':
            abort(404)

        item = CartItem.query.filter_by(user_id=current_user.id, beat_id=beat_id).first()
        if item:
            flash('Этот бит уже есть в корзине.', 'danger')
            return redirect(request.referrer or url_for('catalog'))

        db.session.add(CartItem(user_id=current_user.id, beat_id=beat_id))
        db.session.commit()
        flash('Бит добавлен в корзину.', 'success')
        return redirect(request.referrer or url_for('catalog'))

    @app.route('/cart/remove/<int:beat_id>')
    @login_required
    def remove_from_cart(beat_id):
        item = CartItem.query.filter_by(user_id=current_user.id, beat_id=beat_id).first()
        if not item:
            abort(404)
        db.session.delete(item)
        db.session.commit()
        flash('Бит удален из корзины.', 'success')
        return redirect(url_for('profile'))

    @app.route('/checkout')
    @login_required
    def checkout():
        items = Beat.query.join(CartItem, CartItem.beat_id == Beat.id).filter(CartItem.user_id == current_user.id).all()
        total = sum(item.price for item in items)
        return render_template('checkout.html', items=items, total=total)
