from flask_login import current_user

from models import CartItem


def register_context_processors(app):
    @app.context_processor
    def inject_cart_count():
        count = 0
        if current_user.is_authenticated:
            count = CartItem.query.filter_by(user_id=current_user.id).count()
        return {'cart_count': count}
