from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from config import UPLOAD_COVERS, UPLOAD_PREVIEWS
from extensions import db
from models import Beat, User
from services import allowed_audio, allowed_image, save_uploaded_file


def register_admin_routes(app):
    @app.route('/admin', methods=['GET', 'POST'])
    @login_required
    def admin_panel():
        if not current_user.is_admin:
            abort(403)

        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            category = request.form.get('category', '').strip()
            mood = request.form.get('mood', '').strip()
            bpm = request.form.get('bpm', '').strip()
            beat_key = request.form.get('beat_key', '').strip()
            price = request.form.get('price', '').strip()
            description = request.form.get('description', '').strip()
            featured = bool(request.form.get('is_featured'))
            preview = request.files.get('preview')
            cover = request.files.get('cover')

            if not title or not category or not mood or not bpm or not beat_key or not price or not preview:
                flash('Заполните обязательные поля и загрузите превью.', 'danger')
                return redirect(url_for('admin_panel'))
            if not allowed_audio(preview.filename):
                flash('Превью должно быть в формате mp3, wav, ogg или m4a.', 'danger')
                return redirect(url_for('admin_panel'))
            if cover and cover.filename and not allowed_image(cover.filename):
                flash('Обложка должна быть в формате png, jpg, jpeg или webp.', 'danger')
                return redirect(url_for('admin_panel'))

            preview_name = save_uploaded_file(preview, UPLOAD_PREVIEWS)
            cover_name = 'default-cover.jpg'
            if cover and cover.filename:
                cover_name = save_uploaded_file(cover, UPLOAD_COVERS)

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
                is_featured=featured,
                status='approved',
                moderation_note='Добавлено администратором',
                submitted_by_user_id=current_user.id,
            )
            db.session.add(beat)
            db.session.commit()
            flash('Бит добавлен.', 'success')
            return redirect(url_for('admin_panel'))

        beats = Beat.query.order_by(Beat.created_at.desc()).all()
        users = User.query.order_by(User.created_at.desc()).all()
        pending_beats = Beat.query.filter_by(status='pending').order_by(Beat.created_at.desc()).all()
        return render_template('admin.html', beats=beats, users=users, pending_beats=pending_beats)

    @app.route('/admin/moderate/<int:beat_id>/<action>')
    @login_required
    def moderate_beat(beat_id, action):
        if not current_user.is_admin:
            abort(403)

        beat = db.session.get(Beat, beat_id)
        if not beat:
            abort(404)

        if action == 'approve':
            beat.status = 'approved'
            beat.moderation_note = 'Одобрено администратором'
            flash('Бит опубликован.', 'success')
        elif action == 'reject':
            beat.status = 'rejected'
            beat.is_featured = False
            beat.moderation_note = 'Отклонено администратором'
            flash('Бит отклонен.', 'success')
        else:
            abort(404)

        db.session.commit()
        return redirect(url_for('admin_panel'))

    @app.route('/admin/delete/<int:beat_id>')
    @login_required
    def delete_beat(beat_id):
        if not current_user.is_admin:
            abort(403)

        beat = db.session.get(Beat, beat_id)
        if not beat:
            abort(404)

        db.session.delete(beat)
        db.session.commit()
        flash('Бит удален.', 'success')
        return redirect(url_for('admin_panel'))
