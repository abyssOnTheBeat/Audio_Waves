from flask import Flask

from config import Config, prepare_folders
from context_processors import register_context_processors
from extensions import db, login_manager
from models import User
from routes import register_routes
from services import seed_data


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    prepare_folders()

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Сначала войдите в аккаунт.'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    register_context_processors(app)
    register_routes(app)

    with app.app_context():
        db.create_all()
        seed_data()

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
