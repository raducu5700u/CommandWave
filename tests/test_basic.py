"""
Basic tests for CommandWave application that don't rely on complex mocking
"""
import pytest
import json

def test_index_route(client):
    """Test the main index route returns correct HTML."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'CommandWave' in response.data
    assert b'Terminal Management Interface' in response.data
    
def test_healthcheck(client):
    """Test the healthcheck endpoint."""
    response = client.get('/healthcheck')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}

def test_static_files(client):
    """Test that static files are served correctly."""
    response = client.get('/static/css/style.css')
    assert response.status_code == 200
    assert b'CommandWave' in response.data  # Check for a string that's actually in the CSS
    
    response = client.get('/static/js/script.js') 
    assert response.status_code == 200
    assert b'CommandWave' in response.data
