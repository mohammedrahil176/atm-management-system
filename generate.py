import os

base_dir = '/home/rahil/atm-system'

html_base = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATM System</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container">
        <header>
            <h1>ATM Management System</h1>
            {% if session.get('user_id') %}
            <nav>
                {% if not session.get('is_admin') %}
                <a href="{{ url_for('dashboard') }}">Dashboard</a>
                {% endif %}
                <a href="{{ url_for('logout') }}" class="btn-logout">Logout</a>
            </nav>
            {% endif %}
        </header>
        
        <main>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            {% block content %}{% endblock %}
        </main>
    </div>
    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
</body>
</html>
"""

templates = {
    'login.html': """{% extends "base.html" %}
{% block content %}
<div class="login-box">
    <h2>Welcome to ATM</h2>
    <form method="POST" action="{{ url_for('login') }}">
        <div class="form-group">
            <label>Card Number</label>
            <input type="text" name="card_number" required pattern="[0-9a-zA-Z]+" title="Alphanumeric card number">
        </div>
        <div class="form-group">
            <label>PIN</label>
            <input type="password" name="pin" required>
        </div>
        <button type="submit" class="btn">Login</button>
    </form>
</div>
{% endblock %}""",

    'dashboard.html': """{% extends "base.html" %}
{% block content %}
<div class="dashboard">
    <h2>Welcome, {{ session.name }}</h2>
    <div class="grid">
        <a href="{{ url_for('balance') }}" class="card">Balance Inquiry</a>
        <a href="{{ url_for('withdraw') }}" class="card">Cash Withdrawal</a>
        <a href="{{ url_for('deposit') }}" class="card">Cash Deposit</a>
        <a href="{{ url_for('transfer') }}" class="card">Money Transfer</a>
        <a href="{{ url_for('statement') }}" class="card">Mini Statement</a>
        <a href="{{ url_for('change_pin') }}" class="card">Change PIN</a>
    </div>
</div>
{% endblock %}""",

    'balance.html': """{% extends "base.html" %}
{% block content %}
<div class="center-content">
    <h2>Current Balance</h2>
    <div class="balance-amount">${{ "%.2f"|format(balance) }}</div>
    <a href="{{ url_for('dashboard') }}" class="btn">Back to Dashboard</a>
</div>
{% endblock %}""",

    'withdraw.html': """{% extends "base.html" %}
{% block content %}
<div class="form-box">
    <h2>Cash Withdrawal</h2>
    <form method="POST">
        <div class="form-group">
            <label>Amount ($)</label>
            <input type="number" step="0.01" name="amount" min="1" required>
        </div>
        <button type="submit" class="btn">Withdraw</button>
        <a href="{{ url_for('dashboard') }}" class="btn btn-secondary">Cancel</a>
    </form>
</div>
{% endblock %}""",

    'deposit.html': """{% extends "base.html" %}
{% block content %}
<div class="form-box">
    <h2>Cash Deposit</h2>
    <form method="POST">
        <div class="form-group">
            <label>Amount ($)</label>
            <input type="number" step="0.01" name="amount" min="1" required>
        </div>
        <button type="submit" class="btn">Deposit</button>
        <a href="{{ url_for('dashboard') }}" class="btn btn-secondary">Cancel</a>
    </form>
</div>
{% endblock %}""",

    'transfer.html': """{% extends "base.html" %}
{% block content %}
<div class="form-box">
    <h2>Money Transfer</h2>
    <form method="POST">
        <div class="form-group">
            <label>Target Card Number</label>
            <input type="text" name="target_card" required>
        </div>
        <div class="form-group">
            <label>Amount ($)</label>
            <input type="number" step="0.01" name="amount" min="1" required>
        </div>
        <button type="submit" class="btn">Transfer</button>
        <a href="{{ url_for('dashboard') }}" class="btn btn-secondary">Cancel</a>
    </form>
</div>
{% endblock %}""",

    'statement.html': """{% extends "base.html" %}
{% block content %}
<div class="statement-box">
    <h2>Mini Statement</h2>
    <table class="table">
        <thead>
            <tr>
                <th>Date & Time</th>
                <th>Transaction Type</th>
                <th>Amount</th>
            </tr>
        </thead>
        <tbody>
            {% for t in transactions %}
            <tr>
                <td>{{ t.timestamp }}</td>
                <td>{{ t.type }}</td>
                <td>${{ "%.2f"|format(t.amount) }}</td>
            </tr>
            {% else %}
            <tr>
                <td colspan="3">No transactions found.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    <br>
    <a href="{{ url_for('dashboard') }}" class="btn">Back to Dashboard</a>
</div>
{% endblock %}""",

    'change_pin.html': """{% extends "base.html" %}
{% block content %}
<div class="form-box">
    <h2>Change PIN</h2>
    <form method="POST">
        <div class="form-group">
            <label>Current PIN</label>
            <input type="password" name="old_pin" required>
        </div>
        <div class="form-group">
            <label>New PIN</label>
            <input type="password" name="new_pin" required>
        </div>
        <div class="form-group">
            <label>Confirm New PIN</label>
            <input type="password" name="confirm_pin" required>
        </div>
        <button type="submit" class="btn">Change PIN</button>
        <a href="{{ url_for('dashboard') }}" class="btn btn-secondary">Cancel</a>
    </form>
</div>
{% endblock %}""",

    'admin.html': """{% extends "base.html" %}
{% block content %}
<div class="admin-dashboard">
    <h2>Admin Panel</h2>
    <h3>All Users</h3>
    <table class="table">
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Card Number</th>
                <th>Balance</th>
            </tr>
        </thead>
        <tbody>
            {% for u in users %}
            <tr>
                <td>{{ u.id }}</td>
                <td>{{ u.name }}</td>
                <td>{{ u.card_number }}</td>
                <td>${{ "%.2f"|format(u.balance) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}"""
}

css = """
:root {
    --primary: #2c3e50;
    --secondary: #34495e;
    --accent: #3498db;
    --bg: #f4f7f6;
    --text: #333;
    --error: #e74c3c;
    --success: #2ecc71;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: var(--bg);
    color: var(--text);
    margin: 0;
    padding: 0;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: var(--primary);
    color: white;
    padding: 15px 30px;
    border-radius: 8px;
    margin-bottom: 20px;
}

header h1 {
    margin: 0;
    font-size: 24px;
}

nav a {
    color: white;
    text-decoration: none;
    margin-left: 15px;
}

.btn {
    display: inline-block;
    background: var(--accent);
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    text-decoration: none;
    text-align: center;
    font-size: 16px;
}

.btn-secondary {
    background: #95a5a6;
}

.btn:hover {
    opacity: 0.9;
}

.alert {
    padding: 10px;
    margin-bottom: 15px;
    border-radius: 4px;
}

.alert-error {
    background: #fadbd8;
    color: var(--error);
}

.alert-success {
    background: #d5f5e3;
    color: var(--success);
}

.login-box, .form-box, .center-content, .statement-box, .admin-dashboard {
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.form-group {
    margin-bottom: 15px;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

.form-group input {
    width: 100%;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    box-sizing: border-box;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-top: 20px;
}

.card {
    background: white;
    padding: 20px;
    text-align: center;
    border-radius: 8px;
    text-decoration: none;
    color: var(--primary);
    font-weight: bold;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.2s;
}

.card:hover {
    transform: translateY(-5px);
    background: var(--accent);
    color: white;
}

.balance-amount {
    font-size: 48px;
    font-weight: bold;
    color: var(--accent);
    margin: 20px 0;
}

.table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}

.table th, .table td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

.table th {
    background-color: var(--primary);
    color: white;
}
"""

js = """
// Client-side interactions
document.addEventListener('DOMContentLoaded', () => {
    // Timeout for alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.display = 'none';
        }, 5000);
    });
});
"""

test_py = """import pytest
import sqlite3
import os
from app import app, init_db, DATABASE

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # use in-memory db or test db
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

def test_login(client):
    response = client.post('/', data={
        'card_number': '1234567890123456',
        'pin': '1234'
    }, follow_redirects=True)
    assert b'Welcome, Demo User' in response.data

def test_invalid_login(client):
    response = client.post('/', data={
        'card_number': '1234567890123456',
        'pin': 'wrong'
    }, follow_redirects=True)
    assert b'Invalid card number or PIN' in response.data
"""

readme = """# ATM Management System

A Flask-based ATM Management System.

## Features
- Login/Auth
- Dashboard
- Cash Withdrawal, Deposit, Balance, Transfer
- Mini Statement, Change PIN
- Admin Panel

## Setup
1. `pip install -r requirements.txt`
2. `python app.py`

## Credentials
- User: `1234567890123456` / PIN: `1234`
- Admin: `admin` / PIN: `admin123`
"""

gitignore = """venv/
__pycache__/
*.pyc
.env
.pytest_cache/
database/atm.db
"""

env_example = """FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
"""

with open(os.path.join(base_dir, 'templates', 'base.html'), 'w') as f: f.write(html_base)
for name, content in templates.items():
    with open(os.path.join(base_dir, 'templates', name), 'w') as f: f.write(content)
with open(os.path.join(base_dir, 'static', 'css', 'style.css'), 'w') as f: f.write(css)
with open(os.path.join(base_dir, 'static', 'js', 'app.js'), 'w') as f: f.write(js)
with open(os.path.join(base_dir, 'tests', 'test_app.py'), 'w') as f: f.write(test_py)
with open(os.path.join(base_dir, 'README.md'), 'w') as f: f.write(readme)
with open(os.path.join(base_dir, '.gitignore'), 'w') as f: f.write(gitignore)
with open(os.path.join(base_dir, '.env.example'), 'w') as f: f.write(env_example)
