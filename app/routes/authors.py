from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from app import db
from app.models import Author

author_bp = Blueprint('authors', __name__)

@author_bp.route('/', methods=['GET'])
def get_authors():
    """Get all authors, with optional filtering"""
    name_filter = request.args.get('name', '')
    
    query = Author.query
    if name_filter:
        query = query.filter(Author.name.ilike(f'%{name_filter}%'))
    
    authors = query.all()
    return jsonify({
        'success': True,
        'data': [author.to_dict() for author in authors],
        'count': len(authors)
    }), 200

@author_bp.route('/<int:author_id>', methods=['GET'])
def get_author(author_id):
    """Get a specific author by ID"""
    author = Author.query.get_or_404(author_id, description=f"Author with id {author_id} not found")
    
    return jsonify({
        'success': True,
        'data': author.to_dict()
    }), 200

@author_bp.route('/', methods=['POST'])
def create_author():
    """Create a new author"""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({
            'success': False,
            'message': 'Name is required'
        }), 400
    
    try:
        # Process birth_date if provided
        birth_date = None
        if data.get('birth_date'):
            try:
                birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid date format. Use YYYY-MM-DD'
                }), 400
        
        # Create new author
        new_author = Author(
            name=data['name'],
            biography=data.get('biography'),
            birth_date=birth_date
        )
        
        db.session.add(new_author)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Author created successfully',
            'data': new_author.to_dict()
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An integrity error occurred'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@author_bp.route('/<int:author_id>', methods=['PUT'])
def update_author(author_id):
    """Update an existing author"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    author = Author.query.get_or_404(author_id, description=f"Author with id {author_id} not found")
    
    try:
        # Update author fields
        if 'name' in data:
            author.name = data['name']
        if 'biography' in data:
            author.biography = data['biography']
        if 'birth_date' in data:
            if data['birth_date']:
                try:
                    author.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid date format. Use YYYY-MM-DD'
                    }), 400
            else:
                author.birth_date = None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Author updated successfully',
            'data': author.to_dict()
        }), 200
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An integrity error occurred'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@author_bp.route('/<int:author_id>', methods=['DELETE'])
def delete_author(author_id):
    """Delete an author and all associated books"""
    author = Author.query.get_or_404(author_id, description=f"Author with id {author_id} not found")
    
    try:
        db.session.delete(author)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Author with id {author_id} and all associated books deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@author_bp.route('/<int:author_id>/books', methods=['GET'])
def get_author_books(author_id):
    """Get all books by a specific author"""
    author = Author.query.get_or_404(author_id, description=f"Author with id {author_id} not found")
    
    books = [book.to_dict() for book in author.books]
    
    return jsonify({
        'success': True,
        'data': books,
        'count': len(books)
    }), 200