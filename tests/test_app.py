import pytest
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
