import os
import webbrowser
from flask import Flask
from dotenv import load_dotenv
from extensions import db, migrate
from routes import main_bp

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_PERMANENT'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(main_bp)

    return app

app = create_app()

if __name__ == '__main__':

    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        webbrowser.open('http://127.0.0.1:5000/')
    app.run(debug=True)