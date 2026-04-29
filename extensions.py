from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# Общие расширения приложения.
# Они создаются отдельно, а подключаются к Flask в app.py.
db = SQLAlchemy()
login_manager = LoginManager()
