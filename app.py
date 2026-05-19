# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime

# --- Configuration ---
app = Flask(__name__)
app.config['ENV'] = 'development'
# Set a secret key for session management (IMPORTANT)
app.secret_key = os.urandom(24) 
# Note: DATABASE path assumes the 'instance' folder is created in the same directory as app.py
DATABASE = os.path.join(app.instance_path, 'budget_book.db')

# --- Database Helper Functions ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Connect to the database file
        db = g._database = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # Use Row objects to access columns by name
        db.row_factory = sqlite3.Row 
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    # Ensure the 'instance' folder exists before trying to create the DB file inside it
    os.makedirs(app.instance_path, exist_ok=True) 
    with app.app_context():
        db = get_db()
        # Schema for Users and Transactions
        try:
            with open('schema.sql', 'r') as f: 
                db.executescript(f.read())
            db.commit()
            print("Database initialized successfully.")
        except FileNotFoundError:
            print("ERROR: schema.sql file not found. Database not created.")

# --- Authentication and User Management ---

@app.route('/register', methods=('GET', 'POST'))
def register():
    # ... (Registration logic remains the same) ...
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
        
        flash(error, 'danger')
    return render_template('register.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    # ... (Login logic remains the same) ...
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))

        flash(error, 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- Transaction Management and Context Loader ---

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        # Use try/except in case the database is not yet initialized or the user was deleted
        try:
            g.user = get_db().execute(
                'SELECT * FROM users WHERE id = ?', (user_id,)
            ).fetchone()
        except sqlite3.OperationalError:
            g.user = None


def login_required(view):
    from functools import wraps
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            flash('Please log in to view this page.', 'warning')
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped_view

@app.route('/')
@login_required
def dashboard():
    user_id = g.user['id']
    db = get_db()
    
    # 1. Fetch recent transactions
    # Note: Use a default value of [] if the query fails (e.g., if DB is brand new)
    try:
        transactions = db.execute(
            'SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT 10',
            (user_id,)
        ).fetchall()
    except sqlite3.OperationalError:
        transactions = [] # Handle case where table doesn't exist yet
    
    # 2. Calculate summary (TOTAL INCOME / TOTAL EXPENSE)
    # The SQL for summary is fine, but wrap in try/except for safety
    try:
        total_income = db.execute(
            "SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'Income'",
            (user_id,)
        ).fetchone()[0] or 0

        total_expense = db.execute(
            "SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'Expense'",
            (user_id,)
        ).fetchone()[0] or 0
    except sqlite3.OperationalError:
        total_income = 0
        total_expense = 0
    
    balance = total_income - total_expense
    
    return render_template('index.html', 
                           transactions=transactions, 
                           total_income=total_income,
                           total_expense=total_expense,
                           balance=balance)

@app.route('/add', methods=('GET', 'POST'))
@login_required
def add_transaction():
    if request.method == 'POST':
        date = request.form['date']
        amount = request.form['amount']
        type = request.form['type']
        category = request.form['category']
        description = request.form.get('description', '') # Use .get for optional fields
        user_id = g.user['id']
        error = None

        if not all([date, amount, type, category]):
            error = 'All required fields must be filled.'
        
        try:
            amount = float(amount)
            if amount <= 0:
                 error = 'Amount must be greater than zero.'
        except ValueError:
            error = 'Invalid amount entered.'
        
        if error is None:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO transactions (user_id, date, amount, type, category, description) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, date, amount, type, category, description)
                )
                db.commit()
                flash('Transaction added successfully!', 'success')
                return redirect(url_for('dashboard'))
            except sqlite3.OperationalError as e:
                # Handle cases where the table might be missing (shouldn't happen if init_db runs)
                error = f"Database error: {e}. Please ensure schema.sql was run."
        
        flash(error, 'danger')
        
    # Standard Categories for easy selection
    categories = ['Food & Dining', 'Groceries', 'Utilities', 'Rent/Mortgage', 'Transport', 'Healthcare', 'Savings', 'Gifts', 'Salary', 'Investment', 'Other']
    
    return render_template('add_transaction.html', categories=categories, today=datetime.now().strftime('%Y-%m-%d'))


# --- Advanced Feature: Reporting and Analysis ---

@app.route('/report')
@login_required
def report():
    user_id = g.user['id']
    db = get_db()
    
    try:
        # 1. Monthly Summary (Yearly breakdown is better)
        monthly_data = db.execute("""
            SELECT 
                strftime('%Y-%m', date) AS month_year,
                SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END) AS total_income,
                SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) AS total_expense
            FROM transactions
            WHERE user_id = ?
            GROUP BY month_year
            ORDER BY month_year DESC
        """, (user_id,)).fetchall()

        # 2. Category-wise Spending (Top 5 categories this month - Advanced Feature)
        current_month = datetime.now().strftime('%Y-%m')
        category_spending = db.execute("""
            SELECT 
                category,
                SUM(amount) AS total_spent
            FROM transactions
            WHERE user_id = ? AND type = 'Expense' AND strftime('%Y-%m', date) = ?
            GROUP BY category
            ORDER BY total_spent DESC
            LIMIT 5
        """, (user_id, current_month)).fetchall()
        
    except sqlite3.OperationalError:
        # Return empty data if the table doesn't exist
        monthly_data = []
        category_spending = []

    
    return render_template('report.html', monthly_data=monthly_data, category_spending=category_spending)

# --- Application Startup ---

# Call init_db() on the first run of the application to create the database.
# This should be called outside the 'if __name__ == "__main__":' block 
# if you intend to run it using the 'flask run' command, but calling it here is fine too.
# The key is to ensure it is called only once to set up the database structure.
with app.app_context():
    init_db()

if __name__ == '__main__':
    # NOTE: Set debug=True for development. Change to False for production!
    app.run(debug=True)