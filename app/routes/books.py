from flask import Blueprint, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError, errors
from datetime import datetime
from app import get_db_connection

book_bp = Blueprint('books', __name__)

@book_bp.route('/', methods=['GET'])
def get_books():
    """Get all books, with optional filtering"""
    title_filter = request.args.get('title', '')
    author_id = request.args.get('author_id')
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Build query based on filters
                query_parts = ["SELECT b.*, a.name as author_name FROM books b JOIN authors a ON b.author_id = a.id"]
                params = []
                
                where_clauses = []
                if title_filter:
                    where_clauses.append("b.title ILIKE %s")
                    params.append(f'%{title_filter}%')
                
                if author_id:
                    where_clauses.append("b.author_id = %s")
                    params.append(author_id)
                
                if where_clauses:
                    query_parts.append("WHERE " + " AND ".join(where_clauses))
                
                query_parts.append("ORDER BY b.title")
                
                final_query = " ".join(query_parts)
                cur.execute(final_query, params)
                books = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'data': books,
                    'count': len(books)
                }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@book_bp.route('/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """Get a specific book by ID"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT b.*, a.name as author_name
                    FROM books b
                    JOIN authors a ON b.author_id = a.id
                    WHERE b.id = %s
                """
                cur.execute(query, (book_id,))
                book = cur.fetchone()
                
                if not book:
                    return jsonify({
                        'success': False,
                        'message': f'Book with id {book_id} not found'
                    }), 404
                
                return jsonify({
                    'success': True,
                    'data': book
                }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@book_bp.route('/', methods=['POST'])
def create_book():
    """Create a new book"""
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('author_id'):
        return jsonify({
            'success': False,
            'message': 'Title and author_id are required'
        }), 400
    
    try:
        # Process publication_date if provided
        publication_date = None
        if data.get('publication_date'):
            try:
                publication_date = datetime.strptime(data['publication_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid date format. Use YYYY-MM-DD'
                }), 400
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if author exists
                cur.execute("SELECT id FROM authors WHERE id = %s", (data['author_id'],))
                if not cur.fetchone():
                    return jsonify({
                        'success': False,
                        'message': f"Author with id {data['author_id']} not found"
                    }), 404
                
                query = """
                    INSERT INTO books (title, description, isbn, publication_date, price, author_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *
                """
                cur.execute(query, (
                    data['title'],
                    data.get('description'),
                    data.get('isbn'),
                    publication_date,
                    data.get('price'),
                    data['author_id']
                ))
                new_book = cur.fetchone()
                
                # Add author name to response
                cur.execute("SELECT name FROM authors WHERE id = %s", (data['author_id'],))
                author = cur.fetchone()
                new_book['author_name'] = author['name']
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Book created successfully',
                    'data': new_book
                }), 201
    except psycopg2.errors.UniqueViolation:
        return jsonify({
            'success': False,
            'message': 'ISBN already exists'
        }), 400
    except IntegrityError:
        return jsonify({
            'success': False,
            'message': 'An integrity error occurred'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@book_bp.route('/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    """Update an existing book"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    try:
        # Process publication_date if provided
        publication_date = None
        if 'publication_date' in data:
            if data['publication_date']:
                try:
                    publication_date = datetime.strptime(data['publication_date'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid date format. Use YYYY-MM-DD'
                    }), 400
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if book exists
                cur.execute("SELECT id FROM books WHERE id = %s", (book_id,))
                if not cur.fetchone():
                    return jsonify({
                        'success': False,
                        'message': f'Book with id {book_id} not found'
                    }), 404
                
                # If author_id is provided, check if the author exists
                if data.get('author_id'):
                    cur.execute("SELECT id FROM authors WHERE id = %s", (data['author_id'],))
                    if not cur.fetchone():
                        return jsonify({
                            'success': False,
                            'message': f"Author with id {data['author_id']} not found"
                        }), 404
                
                # Build update query dynamically based on provided fields
                update_parts = []
                params = []
                
                if 'title' in data:
                    update_parts.append("title = %s")
                    params.append(data['title'])
                
                if 'description' in data:
                    update_parts.append("description = %s")
                    params.append(data['description'])
                
                if 'isbn' in data:
                    update_parts.append("isbn = %s")
                    params.append(data['isbn'])
                
                if 'publication_date' in data:
                    update_parts.append("publication_date = %s")
                    params.append(publication_date)
                
                if 'price' in data:
                    update_parts.append("price = %s")
                    params.append(data['price'])
                
                if 'author_id' in data:
                    update_parts.append("author_id = %s")
                    params.append(data['author_id'])
                
                if not update_parts:
                    return jsonify({
                        'success': False,
                        'message': 'No fields to update'
                    }), 400