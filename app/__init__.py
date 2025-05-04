from flask import Flask
import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import Config

def get_db_connection():
    """Create a database connection"""
    conn = psycopg2.connect(
        host=Config.DB_HOST,
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD
    )
    conn.autocommit = False
    return conn

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize database tables if they don't exist
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Create authors table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS authors (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    biography TEXT,
                    birth_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create books table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    isbn VARCHAR(20) UNIQUE,
                    publication_date DATE,
                    price FLOAT,
                    author_id INTEGER NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create function for automatically updating updated_at timestamp
            cur.execute('''
                CREATE OR REPLACE FUNCTION update_modified_column()
                RETURNS TRIGGER AS $
                BEGIN
                    NEW.updated_at = now();
                    RETURN NEW;
                END;
                $ language 'plpgsql';
            ''')
            
            # Create triggers for automatically updating updated_at timestamp
            cur.execute('''
                DROP TRIGGER IF EXISTS update_authors_modtime ON authors;
                CREATE TRIGGER update_authors_modtime
                BEFORE UPDATE ON authors
                FOR EACH ROW
                EXECUTE FUNCTION update_modified_column();
            ''')
            
            cur.execute('''
                DROP TRIGGER IF EXISTS update_books_modtime ON books;
                CREATE TRIGGER update_books_modtime
                BEFORE UPDATE ON books
                FOR EACH ROW
                EXECUTE FUNCTION update_modified_column();
            ''')
            
            conn.commit()
    
    # Register blueprints
    from app.routes.authors import author_bp
    from app.routes.books import book_bp
    
    app.register_blueprint(author_bp, url_prefix='/api/authors')
    app.register_blueprint(book_bp, url_prefix='/api/books')
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}, 200
    
    return app