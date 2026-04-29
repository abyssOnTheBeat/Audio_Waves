from routes.admin import register_admin_routes
from routes.api import register_api_routes
from routes.auth import register_auth_routes
from routes.store import register_store_routes
from routes.web import register_web_routes


def register_routes(app):
    register_web_routes(app)
    register_auth_routes(app)
    register_store_routes(app)
    register_admin_routes(app)
    register_api_routes(app)
