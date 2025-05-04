from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from app import db
from app.models import Book, Author

book_bp = Blueprint('books', __name__)

@book_bp.route('/', methods=['GET'])
def get_books():
    """Get all books, with optional filtering"""
    title_filter = request.args.get('title', '')
    author_id = request.args.get('author_id')
    
    query = Book.query
    if title_filter:
        query = query.filter(Book.title.ilike(f'%{title_filter}%'))
    if author_id:
        query = query.filter(Book.author_id == author_id)
    
    books = query.all()
    return jsonify({
        'success': True,
        'data': [book.to_dict() for book in books],
        'count': len(books)
    }), 200

@book_bp.route('/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """Get a specific book by ID"""
    book = Book.query.get_or_404(book_id, description=f"Book with id {book_id} not found")
    
    return jsonify({
        'success': True,
        'data': book.to_dict()
    }), 200

@book_bp.route('/', methods=['POST'])
def create_book():
    """Create a new book"""
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('author_id'):
        return jsonify({
            'success': False,
            'message': 'Title and author_id are required'
        }), 400
    
    # Check if author exists
    author = Author.query.get(data['author_id'])
    if not author:
        return jsonify({
            'success': False,
            'message': f"Author with id {data['author_id']} not found"
        }), 404
    
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
        
        # Create new book
        new_book = Book(
            title=data['title'],
            description=data.get('description'),
            isbn=data.get('isbn'),
            publication_date=publication_date,
            price=data.get('price'),
            author_id=data['author_id']
        )
        
        db.session.add(new_book)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Book created successfully',
            'data': new_book.to_dict()
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An integrity error occurred. ISBN may be duplicate.'
        }), 400
    except Exception as e:
        db.session.rollback()
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
    
    book = Book.query.get_or_404(book_id, description=f"Book with id {book_id} not found")
    
    # If author_id is provided, check if the author exists
    if data.get('author_id'):
        author = Author.query.get(data['author_id'])
        if not author:
            return jsonify({
                'success': False,
                'message': f"Author with id {data['author_id']} not found"
            }), 404
    
    try:
        # Update book fields
        if 'title' in data:
            book.title = data['title']
        if 'description' in data:
            book.description = data['description']
        if 'isbn' in data:
            book.isbn = data['isbn']
        if 'publication_date' in data:
            if data['publication_date']:
                try:
                    book.publication_date = datetime.strptime(data['publication_date'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid date format. Use YYYY-MM-DD'
                    }), 400
            else:
                book.publication_date = None
        if 'price' in data:
            book.price = data['price']
        if 'author_id' in data:
            book.author_id = data['author_id']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Book updated successfully',
            'data': book.to_dict()
        }), 200
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An integrity error occurred. ISBN may be duplicate.'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@book_bp.route('/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    """Delete a book"""
    book = Book.query.get_or_404(book_id, description=f"Book with id {book_id} not found")
    
    try:
        db.session.delete(book)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Book with id {book_id} deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500