from flask import Blueprint, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError, errors
from datetime import datetime
from app import get_db_connection

author_bp = Blueprint('authors', __name__)

@author_bp.route('/', methods=['GET'])
def get_authors():
    """Get all authors, with optional filtering"""
    name_filter = request.args.get('name', '')
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if name_filter:
                    query = "SELECT * FROM authors WHERE name ILIKE %s ORDER BY name"
                    cur.execute(query, (f'%{name_filter}%',))
                else:
                    query = "SELECT * FROM authors ORDER BY name"
                    cur.execute(query)
                
                authors = cur.fetchall()
                
                # Get book counts for each author
                for author in authors:
                    count_query = "SELECT COUNT(*) FROM books WHERE author_id = %s"
                    cur.execute(count_query, (author['id'],))
                    author['books_count'] = cur.fetchone()['count']
                
                return jsonify({
                    'success': True,
                    'data': authors,
                    'count': len(authors)
                }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@author_bp.route('/<int:author_id>', methods=['GET'])
def get_author(author_id):
    """Get a specific author by ID"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM authors WHERE id = %s"
                cur.execute(query, (author_id,))
                author = cur.fetchone()
                
                if not author:
                    return jsonify({
                        'success': False,
                        'message': f'Author with id {author_id} not found'
                    }), 404
                
                # Get book count
                count_query = "SELECT COUNT(*) FROM books WHERE author_id = %s"
                cur.execute(count_query, (author_id,))
                author['books_count'] = cur.fetchone()['count']
                
                return jsonify({
                    'success': True,
                    'data': author
                }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

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
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    INSERT INTO authors (name, biography, birth_date)
                    VALUES (%s, %s, %s)
                    RETURNING *
                """
                cur.execute(query, (
                    data['name'],
                    data.get('biography'),
                    birth_date
                ))
                new_author = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Author created successfully',
                    'data': new_author
                }), 201
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

@author_bp.route('/<int:author_id>', methods=['PUT'])
def update_author(author_id):
    """Update an existing author"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    try:
        # Process birth_date if provided
        birth_date = None
        if 'birth_date' in data:
            if data['birth_date']:
                try:
                    birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid date format. Use YYYY-MM-DD'
                    }), 400
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if author exists
                cur.execute("SELECT * FROM authors WHERE id = %s", (author_id,))
                if not cur.fetchone():
                    return jsonify({
                        'success': False,
                        'message': f'Author with id {author_id} not found'
                    }), 404
                
                # Build update query dynamically based on provided fields
                update_parts = []
                params = []
                
                if 'name' in data:
                    update_parts.append("name = %s")
                    params.append(data['name'])
                
                if 'biography' in data:
                    update_parts.append("biography = %s")
                    params.append(data['biography'])
                
                if 'birth_date' in data:
                    update_parts.append("birth_date = %s")
                    params.append(birth_date)
                
                if not update_parts:
                    return jsonify({
                        'success': False,
                        'message': 'No fields to update'
                    }), 400
                
                # Construct final query
                query = f"""
                    UPDATE authors
                    SET {', '.join(update_parts)}
                    WHERE id = %s
                    RETURNING *
                """
                params.append(author_id)
                
                cur.execute(query, params)
                updated_author = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Author updated successfully',
                    'data': updated_author
                }), 200
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

@author_bp.route('/<int:author_id>', methods=['DELETE'])
def delete_author(author_id):
    """Delete an author and all associated books"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if author exists
                cur.execute("SELECT id FROM authors WHERE id = %s", (author_id,))
                if not cur.fetchone():
                    return jsonify({
                        'success': False,
                        'message': f'Author with id {author_id} not found'
                    }), 404
                
                # Delete author (books will be deleted via CASCADE)
                cur.execute("DELETE FROM authors WHERE id = %s", (author_id,))
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Author with id {author_id} and all associated books deleted successfully'
                }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@author_bp.route('/<int:author_id>/books', methods=['GET'])
def get_author_books(author_id):
    """Get all books by a specific author"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if author exists
                cur.execute("SELECT id FROM authors WHERE id = %s", (author_id,))
                if not cur.fetchone():
                    return jsonify({
                        'success': False,
                        'message': f'Author with id {author_id} not found'
                    }), 404
                
                # Get books by this author
                query = """
                    SELECT b.*, a.name as author_name
                    FROM books b
                    JOIN authors a ON b.author_id = a.id
                    WHERE b.author_id = %s
                    ORDER BY b.title
                """
                cur.execute(query, (author_id,))
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