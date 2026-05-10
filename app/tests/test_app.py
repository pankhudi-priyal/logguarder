import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from unittest.mock import patch
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"LogGuard App Running" in response.data
    assert response.json['status'] == 'ok'


def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'up'


def test_order_success(client):
    with patch('random.random', return_value=0.5), \
         patch('random.uniform', return_value=0.1), \
         patch('random.randint', return_value=1234), \
         patch('time.sleep'):
        response = client.get('/order')
    assert response.status_code == 200
    assert response.json['order_id'] == 1234
    assert response.json['status'] == 'success'


def test_order_failure(client):
    with patch('random.random', return_value=0.1), \
         patch('random.uniform', return_value=0.1), \
         patch('time.sleep'):
        response = client.get('/order')
    assert response.status_code == 500
    assert response.json['error'] == 'Order failed'


def test_login_success(client):
    with patch('random.random', return_value=0.5):
        response = client.get('/login')
    assert response.status_code == 200
    assert response.json['status'] == 'logged_in'


def test_login_failure(client):
    with patch('random.random', return_value=0.1):
        response = client.get('/login')
    assert response.status_code == 401
    assert response.json['error'] == 'Invalid credentials'
