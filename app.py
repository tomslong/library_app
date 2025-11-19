from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, Book
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'SQLALCHEMY_DATABASE_URL',
    'sqlite:///library.db'  #本地开发默认 
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    if Book.query.count() == 0:
        books = [
            Book(title='The Great Gatsby', author='F. Scott Fitzgerald'),
            Book(title='1984', author='George Orwell'),
            Book(title='To Kill a Mockingbird', author='Harper Lee')
        ]
        db.session.add_all(books)
        db.session.commit()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = request.form['user_id']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
    
        if User.query.filter_by(user_id = user_id).first() or User.query.filter_by( email=email).first():
            flash('User ID or email already existd!')
            return redirect(url_for('register'))
    
        new_user = User(user_id=user_id, name=name, email=email, password = password)
        db.session.add(new_user)
        db.session.commit()
    
        flash('Registration Successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html') 

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            flash('Login successful!')
            return redirect(url_for('books'))
        
        else:
            flash('Invalid email or password!')
    
    return render_template('login.html')
    
@app.route('/books', methods=['GET', 'POST'])
def books():
    if 'user_id' not in session:# WHAT IS A SESSION ? 
       flash('Please log in to access books.') 
       return redirect(url_for('login'))
       
    user = User.query.get(session['user_id'])

    # Handle POST actions: borrow or return
    if request.method == 'POST':
        book_id = int(request.form['book_id'])
        action = request.form.get('action', 'borrow')
        book = Book.query.get(book_id)
        if not book:
            flash('Book is not available!')  # keep message consistent
        elif action == 'return':
            # Only allow return if user has borrowed this book
            borrowed_ids = [int(bid) for bid in user.borrowed_books.split(',') if bid]
            if book_id in borrowed_ids:
                # mark available and remove from user's list
                book.available = True
                borrowed_ids.remove(book_id)
                user.borrowed_books = ','.join(str(b) for b in borrowed_ids)
                db.session.commit()
                flash(f'Returned {book.title}')
            else:
                flash('Book is not available!')
        else:
            if book and book.available:
                book.available = False
                if user.borrowed_books:
                    user.borrowed_books += f",{book_id}"
                else:
                    user.borrowed_books = str(book_id)
                db.session.commit()
                flash(f'You borrowed {book.title}')
            else:
                flash('Book is not available!')

    # Search/filter on GET (and after POST redirectless render)
    q = request.args.get('q', '').strip()
    query = Book.query
    if q:
        like = f"%{q}%"
        query = query.filter((Book.title.ilike(like)) | (Book.author.ilike(like)))
    all_books = query.all()

    borrowed_ids = [int(bid) for bid in user.borrowed_books.split(',') if bid]
    return render_template('books.html', books=all_books, borrowed_ids=borrowed_ids)
    
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!')
    return redirect(url_for('login'))
        
        
if __name__ == '__main__':
    app.run(debug=True)
    
        
        
        

