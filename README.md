## API Documentation

### Authors Endpoints

#### GET /api/authors
- Get all authors
- Query parameters:
  - name: Filter authors by name (partial match)

#### GET /api/authors/{author_id}
- Get a specific author by ID

#### POST /api/authors
- Create a new author
- Request body:
  ```json
  {
    "name": "Jane Austen",
    "biography": "English novelist known for her six major novels...",
    "birth_date": "1775-12-16"
  }
  ```

#### PUT /api/authors/{author_id}
- Update an existing author
- Request body (all fields optional):
  ```json
  {
    "name": "Jane Austen",
    "biography": "Updated biography...",
    "birth_date": "1775-12-16"
  }
  ```

#### DELETE /api/authors/{author_id}
- Delete an author and all associated books

#### GET /api/authors/{author_id}/books
- Get all books by a specific author

### Books Endpoints

#### GET /api/books
- Get all books
- Query parameters:
  - title: Filter books by title (partial match)
  - author_id: Filter books by author ID

#### GET /api/books/{book_id}
- Get a specific book by ID

#### POST /api/books
- Create a new book
- Request body:
  ```json
  {
    "title": "Pride and Prejudice",
    "description": "A romantic novel of manners...",
    "isbn": "9780141439518",
    "publication_date": "1813-01-28",
    "price": 9.99,
    "author_id": 1
  }
  ```

#### PUT /api/books/{book_id}
- Update an existing book
- Request body (all fields optional):
  ```json
  {
    "title": "Pride and Prejudice",
    "description": "Updated description...",
    "isbn": "9780141439518",
    "publication_date": "1813-01-28",
    "price": 12.99,
    "author_id": 1
  }
  ```

#### DELETE /api/books/{book_id}
- Delete a book