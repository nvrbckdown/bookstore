from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes.authors import author_bp
    from app.routes.books import book_bp
    
    app.register_blueprint(author_bp, url_prefix='/api/authors')
    app.register_blueprint(book_bp, url_prefix='/api/books')
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}, 200
    
    return app