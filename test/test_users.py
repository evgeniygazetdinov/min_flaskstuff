import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from main import app
from models.users import User, UserAuth
from etcd_client import EtcdClient, pwd_context

client = TestClient(app)

# Test data
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
def mock_etcd_client():
    with patch('etcd_client.EtcdClient') as mock_client:
        yield mock_client

@pytest.fixture
def mock_user_in_db(test_user_data):
    return {
        "username": test_user_data["username"],
        "password": pwd_context.hash(test_user_data["password"]),
        "vpn_config": test_user_data["vpn_config"]
    }

def test_create_user_success(mock_etcd_client, test_user_data):
    instance = mock_etcd_client.return_value
    instance.create_user.return_value = None
    
    response = client.post("/api/v1/users", json=test_user_data)
    
    assert response.status_code == 200
    assert response.json() == {"message": "User created successfully"}
    
    instance.create_user.assert_called_once_with(
        test_user_data["username"],
        test_user_data["password"],
        test_user_data["vpn_config"]
    )

def test_create_duplicate_user(mock_etcd_client, test_user_data):
    instance = mock_etcd_client.return_value
    instance.create_user.side_effect = Exception("User already exists")
    
    response = client.post("/api/v1/users", json=test_user_data)
    
    assert response.status_code == 500
    assert response.json()["detail"] == "User already exists"

def test_authenticate_valid_user(mock_etcd_client, test_user_data, mock_user_in_db):
    instance = mock_etcd_client.return_value
    instance.verify_password.return_value = True
    instance.get_user.return_value = mock_user_in_db
    
    auth_data = {"username": test_user_data["username"], "password": test_user_data["password"]}
    response = client.post("/api/v1/users/auth", json=auth_data)
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_authenticate_invalid_password(mock_etcd_client, test_user_data):
    instance = mock_etcd_client.return_value
    instance.verify_password.return_value = False
    
    auth_data = {"username": test_user_data["username"], "password": "wrongpass"}
    response = client.post("/api/v1/users/auth", json=auth_data)
    
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_authenticate_nonexistent_user(mock_etcd_client):
    instance = mock_etcd_client.return_value
    instance.verify_password.return_value = False
    instance.get_user.return_value = None
    
    auth_data = {"username": "nonexistent", "password": "anypass"}
    response = client.post("/api/v1/users/auth", json=auth_data)
    
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_get_current_user_success(mock_etcd_client, test_user_data, mock_user_in_db):
    instance = mock_etcd_client.return_value
    instance.verify_password.return_value = True
    instance.get_user.return_value = mock_user_in_db
    
    auth_response = client.post(
        "/api/v1/users/auth",
        json={"username": test_user_data["username"], "password": test_user_data["password"]}
    )
    token = auth_response.json()["access_token"]
    
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["username"] == test_user_data["username"]
    assert "password" not in response.json()  # Ensure password is not returned

def test_get_current_user_invalid_token(mock_etcd_client):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]

def test_database_connection_error(mock_etcd_client, test_user_data):
    instance = mock_etcd_client.return_value
    instance.create_user.side_effect = Exception("Failed to connect to etcd")
    
    response = client.post("/api/v1/users", json=test_user_data)
    
    assert response.status_code == 503
    assert "Failed to connect to etcd" in response.json()["detail"]