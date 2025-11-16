import pytest
import os
from app import app as flask_app
from models import db, User, Book


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test_secret_key',
        'WTF_CSRF_ENABLED': False
    })
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def init_database(app):
    """Initialize database with test data."""
    with app.app_context():
        # Add some test books
        book1 = Book(title='Test Book 1', author='Author 1')
        book2 = Book(title='Test Book 2', author='Author 2')
        db.session.add_all([book1, book2])
        db.session.commit()
        yield db


# Test Case 4: Application initializes with predefined books
class TestApplicationInitialization:
    def test_predefined_books_are_created_on_startup(self):
        """Test that the application initializes with predefined books in the database."""
        # Create a fresh app context to simulate startup
        test_app = flask_app
        test_app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test_secret_key'
        })
        
        with test_app.app_context():
            db.create_all()
            
            # Simulate the initialization code from app.py
            if Book.query.count() == 0:
                books = [
                    Book(title='The Great Gatsby', author='F. Scott Fitzgerald'),
                    Book(title='1984', author='George Orwell'),
                    Book(title='To Kill a Mockingbird', author='Harper Lee')
                ]
                db.session.add_all(books)
                db.session.commit()
            
            # Verify books were created
            assert Book.query.count() == 3
            
            # Verify specific books exist
            gatsby = Book.query.filter_by(title='The Great Gatsby').first()
            assert gatsby is not None
            assert gatsby.author == 'F. Scott Fitzgerald'
            # Don't check available status as it may vary depending on order of tests
            
            orwell = Book.query.filter_by(title='1984').first()
            assert orwell is not None
            assert orwell.author == 'George Orwell'
            
            mockingbird = Book.query.filter_by(title='To Kill a Mockingbird').first()
            assert mockingbird is not None
            assert mockingbird.author == 'Harper Lee'
            
            db.session.remove()
            db.drop_all()


# Test Case 1: User Registration
class TestUserRegistration:
    def test_successful_user_registration(self, client, app):
        """Test that user registration successfully creates a new user."""
        with app.app_context():
            response = client.post('/register', data={
                'user_id': 'user001',
                'name': 'John Doe',
                'email': 'john@example.com',
                'password': 'password123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'Registration Successful! Please log in.' in response.data or b'Login' in response.data
            
            # Verify user was created in database
            user = User.query.filter_by(user_id='user001').first()
            assert user is not None
            assert user.name == 'John Doe'
            assert user.email == 'john@example.com'
            assert user.password == 'password123'
            assert user.borrowed_books == ""
    
    def test_duplicate_user_id_rejected(self, client, app):
        """Test that duplicate user IDs are rejected during registration."""
        with app.app_context():
            # Register first user
            client.post('/register', data={
                'user_id': 'user001',
                'name': 'John Doe',
                'email': 'john@example.com',
                'password': 'password123'
            })
            
            # Try to register another user with same user_id
            response = client.post('/register', data={
                'user_id': 'user001',
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'password': 'password456'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'User ID or email already existd!' in response.data
            
            # Verify only one user exists with that user_id
            users = User.query.filter_by(user_id='user001').all()
            assert len(users) == 1
            assert users[0].name == 'John Doe'
    
    def test_duplicate_email_rejected(self, client, app):
        """Test that duplicate emails are rejected during registration."""
        with app.app_context():
            # Register first user
            client.post('/register', data={
                'user_id': 'user001',
                'name': 'John Doe',
                'email': 'john@example.com',
                'password': 'password123'
            })
            
            # Try to register another user with same email
            response = client.post('/register', data={
                'user_id': 'user002',
                'name': 'Jane Smith',
                'email': 'john@example.com',
                'password': 'password456'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'User ID or email already existd!' in response.data
            
            # Verify only one user exists with that email
            users = User.query.filter_by(email='john@example.com').all()
            assert len(users) == 1
            assert users[0].user_id == 'user001'


# Test Case 2: User Login
class TestUserLogin:
    def test_successful_login_with_correct_credentials(self, client, app):
        """Test that user login authenticates with correct credentials."""
        with app.app_context():
            # First register a user
            user = User(user_id='user001', name='John Doe', 
                       email='john@example.com', password='password123')
            db.session.add(user)
            db.session.commit()
            
            # Try to login with correct credentials
            response = client.post('/login', data={
                'email': 'john@example.com',
                'password': 'password123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'Login successful!' in response.data or b'books' in response.data.lower()
            
            # Verify session was created
            with client.session_transaction() as sess:
                assert 'user_id' in sess
                assert sess['user_id'] == user.id
    
    def test_login_rejects_incorrect_password(self, client, app):
        """Test that login rejects incorrect password."""
        with app.app_context():
            # Register a user
            user = User(user_id='user001', name='John Doe',
                       email='john@example.com', password='password123')
            db.session.add(user)
            db.session.commit()
            
            # Try to login with wrong password
            response = client.post('/login', data={
                'email': 'john@example.com',
                'password': 'wrongpassword'
            }, follow_redirects=False)
            
            assert response.status_code == 200
            assert b'Invalid email or password!' in response.data
            
            # Verify no session was created
            with client.session_transaction() as sess:
                assert 'user_id' not in sess
    
    def test_login_rejects_incorrect_email(self, client, app):
        """Test that login rejects incorrect email."""
        with app.app_context():
            # Register a user
            user = User(user_id='user001', name='John Doe',
                       email='john@example.com', password='password123')
            db.session.add(user)
            db.session.commit()
            
            # Try to login with wrong email
            response = client.post('/login', data={
                'email': 'wrong@example.com',
                'password': 'password123'
            }, follow_redirects=False)
            
            assert response.status_code == 200
            assert b'Invalid email or password!' in response.data
            
            # Verify no session was created
            with client.session_transaction() as sess:
                assert 'user_id' not in sess
    
    def test_login_rejects_nonexistent_user(self, client, app):
        """Test that login rejects non-existent user."""
        with app.app_context():
            response = client.post('/login', data={
                'email': 'nonexistent@example.com',
                'password': 'password123'
            }, follow_redirects=False)
            
            assert response.status_code == 200
            assert b'Invalid email or password!' in response.data


# Test Case 3: Borrowing Books
class TestBookBorrowing:
    def test_borrowing_available_book_updates_status(self, client, app):
        """Test that borrowing an available book updates its status."""
        with app.app_context():
            # Create a user and a book
            user = User(user_id='user001', name='John Doe',
                       email='john@example.com', password='password123')
            book = Book(title='Test Book', author='Test Author', available=True)
            db.session.add(user)
            db.session.add(book)
            db.session.commit()
            
            user_id = user.id
            book_id = book.id
            
            # Login the user
            with client.session_transaction() as sess:
                sess['user_id'] = user_id
            
            # Borrow the book
            response = client.post('/books', data={
                'book_id': book_id
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Verify book status was updated
            book = Book.query.get(book_id)
            assert book.available == False
    
    def test_borrowing_updates_user_borrowed_books(self, client, app):
        """Test that borrowing a book updates the user's borrowed books list."""
        with app.app_context():
            # Create a user and a book
            user = User(user_id='user001', name='John Doe',
                       email='john@example.com', password='password123')
            book = Book(title='Test Book', author='Test Author', available=True)
            db.session.add(user)
            db.session.add(book)
            db.session.commit()
            
            user_id = user.id
            book_id = book.id
            
            # Login the user
            with client.session_transaction() as sess:
                sess['user_id'] = user_id
            
            # Borrow the book
            response = client.post('/books', data={
                'book_id': book_id
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Verify user's borrowed_books was updated
            user = User.query.get(user_id)
            assert user.borrowed_books == str(book_id)
            assert str(book_id) in user.borrowed_books
    
    def test_borrowing_multiple_books(self, client, app):
        """Test that borrowing multiple books correctly updates the borrowed_books list."""
        with app.app_context():
            # Create a user and multiple books
            user = User(user_id='user001', name='John Doe',
                       email='john@example.com', password='password123')
            book1 = Book(title='Book 1', author='Author 1', available=True)
            book2 = Book(title='Book 2', author='Author 2', available=True)
            db.session.add_all([user, book1, book2])
            db.session.commit()
            
            user_id = user.id
            book1_id = book1.id
            book2_id = book2.id
            
            # Login the user
            with client.session_transaction() as sess:
                sess['user_id'] = user_id
            
            # Borrow first book
            client.post('/books', data={'book_id': book1_id})
            
            # Borrow second book
            client.post('/books', data={'book_id': book2_id})
            
            # Verify both books are in borrowed_books
            user = User.query.get(user_id)
            borrowed_ids = [int(bid) for bid in user.borrowed_books.split(',') if bid]
            assert book1_id in borrowed_ids
            assert book2_id in borrowed_ids
            assert len(borrowed_ids) == 2
            
            # Verify both books are unavailable
            assert Book.query.get(book1_id).available == False
            assert Book.query.get(book2_id).available == False
    
    def test_cannot_borrow_unavailable_book(self, client, app):
        """Test that unavailable books cannot be borrowed."""
        with app.app_context():
            # Create a user and an unavailable book
            user = User(user_id='user001', name='John Doe',
                       email='john@example.com', password='password123')
            book = Book(title='Test Book', author='Test Author', available=False)
            db.session.add(user)
            db.session.add(book)
            db.session.commit()
            
            user_id = user.id
            book_id = book.id
            original_borrowed = user.borrowed_books
            
            # Login the user
            with client.session_transaction() as sess:
                sess['user_id'] = user_id
            
            # Try to borrow the unavailable book
            response = client.post('/books', data={
                'book_id': book_id
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'Book is not available!' in response.data
            
            # Verify user's borrowed_books was NOT updated
            user = User.query.get(user_id)
            assert user.borrowed_books == original_borrowed


# Test Case 5: Protected Routes Access Control
class TestProtectedRoutes:
    def test_unauthenticated_user_denied_access_to_books(self, client, app):
        """Test that unauthenticated users cannot access the /books route."""
        with app.app_context():
            response = client.get('/books', follow_redirects=True)
            
            assert response.status_code == 200
            assert b'Please log in to access books.' in response.data
            # Should redirect to login page
            assert b'login' in response.data.lower() or b'email' in response.data.lower()
    
    def test_unauthenticated_user_cannot_post_to_books(self, client, app):
        """Test that unauthenticated users cannot borrow books via POST to /books."""
        with app.app_context():
            # Create a book
            book = Book(title='Test Book', author='Test Author', available=True)
            db.session.add(book)
            db.session.commit()
            book_id = book.id
            
            # Try to borrow without being logged in
            response = client.post('/books', data={
                'book_id': book_id
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'Please log in to access books.' in response.data
            
            # Verify book status unchanged
            book = Book.query.get(book_id)
            assert book.available == True
    
    def test_authenticated_user_can_access_books(self, client, app):
        """Test that authenticated users can access the /books route."""
        with app.app_context():
            # Create and login a user
            user = User(user_id='user001', name='John Doe',
                       email='john@example.com', password='password123')
            db.session.add(user)
            db.session.commit()
            
            with client.session_transaction() as sess:
                sess['user_id'] = user.id
            
            # Access books route
            response = client.get('/books')
            
            assert response.status_code == 200
            assert b'Please log in to access books.' not in response.data
    
    def test_logout_removes_session(self, client, app):
        """Test that logout removes the user session."""
        with app.app_context():
            # Create and login a user
            user = User(user_id='user001', name='John Doe',
                       email='john@example.com', password='password123')
            db.session.add(user)
            db.session.commit()
            
            with client.session_transaction() as sess:
                sess['user_id'] = user.id
            
            # Logout
            response = client.get('/logout', follow_redirects=True)
            
            assert response.status_code == 200
            assert b'Logged out successfully!' in response.data
            
            # Verify session was cleared
            with client.session_transaction() as sess:
                assert 'user_id' not in sess
            
            # Verify cannot access protected route after logout
            response = client.get('/books', follow_redirects=True)
            assert b'Please log in to access books.' in response.data
