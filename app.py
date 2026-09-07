import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key' # In production, use environment variable
app.config['SESSION_TYPE'] = 'filesystem'
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__name__)), 'database', 'atm.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = get_db()
    c = conn.cursor()
    # Create tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT UNIQUE NOT NULL,
            pin_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Check if seed user exists
    c.execute("SELECT * FROM users WHERE card_number = '1234567890123456'")
    if not c.fetchone():
        pin_hash = generate_password_hash('1234')
        c.execute("INSERT INTO users (card_number, pin_hash, name, balance, is_admin) VALUES (?, ?, ?, ?, ?)",
                  ('1234567890123456', pin_hash, 'Demo User', 1000.0, 0))
    
    # Check if admin user exists
    c.execute("SELECT * FROM users WHERE card_number = 'admin'")
    if not c.fetchone():
        pin_hash = generate_password_hash('admin123')
        c.execute("INSERT INTO users (card_number, pin_hash, name, balance, is_admin) VALUES (?, ?, ?, ?, ?)",
                  ('admin', pin_hash, 'Admin', 0.0, 1))

    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        card_number = request.form['card_number']
        pin = request.form['pin']
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE card_number = ?", (card_number,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user['pin_hash'], pin):
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['is_admin'] = bool(user['is_admin'])
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid card number or PIN', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    return render_template('dashboard.html')

@app.route('/balance')
@login_required
def balance():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],))
    balance = c.fetchone()['balance']
    conn.close()
    return render_template('balance.html', balance=balance)

@app.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        if amount <= 0:
            flash('Amount must be greater than zero.', 'error')
            return redirect(url_for('withdraw'))
            
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],))
        current_balance = c.fetchone()['balance']
        
        if current_balance >= amount:
            new_balance = current_balance - amount
            c.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, session['user_id']))
            c.execute("INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)",
                      (session['user_id'], 'Withdrawal', amount))
            conn.commit()
            conn.close()
            flash(f'Successfully withdrew ${amount:.2f}', 'success')
            return redirect(url_for('dashboard'))
        else:
            conn.close()
            flash('Insufficient funds', 'error')
            
    return render_template('withdraw.html')

@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        if amount <= 0:
            flash('Amount must be greater than zero.', 'error')
            return redirect(url_for('deposit'))
            
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],))
        current_balance = c.fetchone()['balance']
        
        new_balance = current_balance + amount
        c.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, session['user_id']))
        c.execute("INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)",
                  (session['user_id'], 'Deposit', amount))
        conn.commit()
        conn.close()
        flash(f'Successfully deposited ${amount:.2f}', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('deposit.html')

@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    if request.method == 'POST':
        target_card = request.form['target_card']
        amount = float(request.form['amount'])
        
        if amount <= 0:
            flash('Amount must be greater than zero.', 'error')
            return redirect(url_for('transfer'))
            
        conn = get_db()
        c = conn.cursor()
        
        # Check source balance
        c.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],))
        source_balance = c.fetchone()['balance']
        
        if source_balance < amount:
            conn.close()
            flash('Insufficient funds', 'error')
            return redirect(url_for('transfer'))
            
        # Check target user
        c.execute("SELECT id, balance FROM users WHERE card_number = ?", (target_card,))
        target_user = c.fetchone()
        
        if not target_user:
            conn.close()
            flash('Target account not found', 'error')
            return redirect(url_for('transfer'))
            
        if target_user['id'] == session['user_id']:
            conn.close()
            flash('Cannot transfer to yourself', 'error')
            return redirect(url_for('transfer'))
            
        # Perform transfer
        c.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, session['user_id']))
        c.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, target_user['id']))
        
        c.execute("INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)",
                  (session['user_id'], f'Transfer to {target_card}', amount))
        c.execute("INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)",
                  (target_user['id'], 'Transfer Received', amount))
                  
        conn.commit()
        conn.close()
        flash(f'Successfully transferred ${amount:.2f}', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('transfer.html')

@app.route('/statement')
@login_required
def statement():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10", (session['user_id'],))
    transactions = c.fetchall()
    conn.close()
    return render_template('statement.html', transactions=transactions)

@app.route('/change_pin', methods=['GET', 'POST'])
@login_required
def change_pin():
    if request.method == 'POST':
        old_pin = request.form['old_pin']
        new_pin = request.form['new_pin']
        confirm_pin = request.form['confirm_pin']
        
        if new_pin != confirm_pin:
            flash('New PINs do not match', 'error')
            return redirect(url_for('change_pin'))
            
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT pin_hash FROM users WHERE id = ?", (session['user_id'],))
        user = c.fetchone()
        
        if check_password_hash(user['pin_hash'], old_pin):
            new_hash = generate_password_hash(new_pin)
            c.execute("UPDATE users SET pin_hash = ? WHERE id = ?", (new_hash, session['user_id']))
            conn.commit()
            conn.close()
            flash('PIN successfully changed', 'success')
            return redirect(url_for('dashboard'))
        else:
            conn.close()
            flash('Incorrect current PIN', 'error')
            
    return render_template('change_pin.html')

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE is_admin = 0")
    users = c.fetchall()
    conn.close()
    return render_template('admin.html', users=users)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
