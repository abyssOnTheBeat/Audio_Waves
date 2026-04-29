from flask import render_template

from extensions import db
from models import Beat, CartItem, Favorite


def register_web_routes(app):
    @app.route('/')
    def index():
        featured_beats = Beat.query.filter_by(is_featured=True, status='approved').order_by(Beat.created_at.desc()).limit(3).all()
        beats_count = Beat.query.filter_by(status='approved').count()
        return render_template('index.html', featured_beats=featured_beats, beats_count=beats_count)

    @app.route('/catalog')
    def catalog():
        from flask import request
        from flask_login import current_user

        category = request.args.get('category', '').strip()
        mood = request.args.get('mood', '').strip()
        search = request.args.get('search', '').strip()
        sort = request.args.get('sort', 'new')
        min_price = request.args.get('min_price', '').strip()
        max_price = request.args.get('max_price', '').strip()

        query = Beat.query.filter(Beat.status == 'approved')

        if category:
            query = query.filter(Beat.category == category)
        if mood:
            query = query.filter(Beat.mood == mood)
        if search:
            query = query.filter(Beat.title.ilike(f'%{search}%'))
        if min_price:
            try:
                query = query.filter(Beat.price >= float(min_price))
            except ValueError:
                pass
        if max_price:
            try:
                query = query.filter(Beat.price <= float(max_price))
            except ValueError:
                pass

        if sort == 'price_asc':
            query = query.order_by(Beat.price.asc())
        elif sort == 'price_desc':
            query = query.order_by(Beat.price.desc())
        elif sort == 'title':
            query = query.order_by(Beat.title.asc())
        else:
            query = query.order_by(Beat.created_at.desc())

        beats = query.all()
        categories = [x[0] for x in db.session.query(Beat.category).filter(Beat.status == 'approved').distinct().order_by(Beat.category).all()]
        moods = [x[0] for x in db.session.query(Beat.mood).filter(Beat.status == 'approved').distinct().order_by(Beat.mood).all()]
        featured_beats = Beat.query.filter_by(is_featured=True, status='approved').order_by(Beat.created_at.desc()).limit(3).all()

        favorite_ids = set()
        if current_user.is_authenticated:
            favorite_ids = {x.beat_id for x in Favorite.query.filter_by(user_id=current_user.id).all()}

        return render_template(
            'catalog.html',
            beats=beats,
            categories=categories,
            moods=moods,
            featured_beats=featured_beats,
            favorite_ids=favorite_ids,
            filters={
                'category': category,
                'mood': mood,
                'search': search,
                'sort': sort,
                'min_price': min_price,
                'max_price': max_price,
            },
        )

    @app.route('/beat/<int:beat_id>')
    def beat_detail(beat_id):
        from flask import abort
        from flask_login import current_user

        beat = db.session.get(Beat, beat_id)
        if not beat:
            abort(404)

        allowed_private = current_user.is_authenticated and (current_user.is_admin or beat.submitted_by_user_id == current_user.id)
        if beat.status != 'approved' and not allowed_private:
            abort(404)

        is_favorite = False
        in_cart = False
        if current_user.is_authenticated:
            is_favorite = Favorite.query.filter_by(user_id=current_user.id, beat_id=beat_id).first() is not None
            in_cart = CartItem.query.filter_by(user_id=current_user.id, beat_id=beat_id).first() is not None

        similar_beats = Beat.query.filter(Beat.category == beat.category, Beat.id != beat.id, Beat.status == 'approved').limit(4).all()
        return render_template('beat_detail.html', beat=beat, is_favorite=is_favorite, in_cart=in_cart, similar_beats=similar_beats)
