import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from etcd_client import pwd_context
from fastapi import HTTPException

client = TestClient(app)

@pytest.fixture
def test_user_data():
    return {
        "username": "testuser",
        "password": "testpass123",
        "vpn_config": {
            "server": "user.vpn.com",
            "port": 1194,
            "protocol": "udp"
        }
    }

@pytest.fixture
def mock_etcd():
    with patch('routers.users.etcd_client') as mock_client:
        # Setup mock storage
        users = {}
        
        def mock_create_user(username, password, vpn_config=None):
            if username in users:
                raise HTTPException(status_code=400, detail="User already exists")
            users[username] = {
                "username": username,
                "password": pwd_context.hash(password),
                "vpn_config": vpn_config
            }
            
        def mock_get_user(username):
            return users.get(username)
            
        def mock_verify_password(username, password):
            user = users.get(username)
            if not user:
                return False
            return pwd_context.verify(password, user["password"])
            
        # Setup mock methods
        mock_client.create_user = MagicMock(side_effect=mock_create_user)
        mock_client.get_user = MagicMock(side_effect=mock_get_user)
        mock_client.verify_password = MagicMock(side_effect=mock_verify_password)
        
        yield mock_client

def test_create_user_success(mock_etcd, test_user_data):
    response = client.post("/api/v1/users", json=test_user_data)
    
    assert response.status_code == 200
    assert response.json() == {"message": "User created successfully"}
    
    mock_etcd.create_user.assert_called_once_with(
        test_user_data["username"],
        test_user_data["password"],
        test_user_data["vpn_config"]
    )

def test_create_duplicate_user(mock_etcd, test_user_data):
    # First create the user
    client.post("/api/v1/users", json=test_user_data)
    
    # Try to create the same user again
    response = client.post("/api/v1/users", json=test_user_data)
    
    assert response.status_code == 400
    assert "User already exists" in response.json()["detail"]

def test_authenticate_valid_user(mock_etcd, test_user_data):
    # First create the user
    client.post("/api/v1/users", json=test_user_data)
    
    # Try to authenticate
    auth_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    }
    response = client.post("/api/v1/users/auth", json=auth_data)
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert response.json()["token_type"] == "bearer"
    
    # Verify the mock was called correctly
    mock_etcd.verify_password.assert_called_with(
        test_user_data["username"],
        test_user_data["password"]
    )

def test_authenticate_invalid_password(mock_etcd, test_user_data):
    # First create the user
    client.post("/api/v1/users", json=test_user_data)
    
    # Try to authenticate with wrong password
    auth_data = {
        "username": test_user_data["username"],
        "password": "wrongpass"
    }
    response = client.post("/api/v1/users/auth", json=auth_data)
    
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_authenticate_nonexistent_user(mock_etcd):
    auth_data = {
        "username": "nonexistent",
        "password": "anypass"
    }
    response = client.post("/api/v1/users/auth", json=auth_data)
    
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_get_current_user_success(mock_etcd, test_user_data):
    # First create and authenticate the user
    client.post("/api/v1/users", json=test_user_data)
    auth_response = client.post("/api/v1/users/auth", json={
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    })
    
    # Get the token
    token = auth_response.json()["access_token"]
    
    # Try to get current user info
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["username"] == test_user_data["username"]
    assert response.json()["vpn_config"] == test_user_data["vpn_config"]

def test_get_current_user_invalid_token(mock_etcd):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]