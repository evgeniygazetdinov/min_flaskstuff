from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_vpn_config():
    test_config = {
        "server": "test.vpn.com",
        "port": 1194,
        "protocol": "udp"
    }
    response = client.post("/vpn/", json={"config_id": "test1", "config_data": test_config})
    assert response.status_code == 200
    assert response.json()["message"] == "VPN configuration created"
    assert response.json()["config_id"] == "test1"

def test_read_vpn_config():
    test_config = {
        "server": "test.vpn.com",
        "port": 1194,
        "protocol": "udp"
    }
    client.post("/vpn/", json={"config_id": "test2", "config_data": test_config})
    
    response = client.get("/vpn/test2")
    assert response.status_code == 200
    assert response.json() == test_config

def test_read_nonexistent_config():
    response = client.get("/vpn/nonexistent")
    assert response.status_code == 200  # FastAPI по умолчанию возвращает 200
    assert response.json()["error"] == "VPN configuration not found"

def test_update_vpn_config():
    initial_config = {
        "server": "test.vpn.com",
        "port": 1194,
        "protocol": "udp"
    }
    client.post("/vpn/", json={"config_id": "test3", "config_data": initial_config})
    
    updated_config = {
        "server": "new.vpn.com",
        "port": 443,
        "protocol": "tcp"
    }
    response = client.put("/vpn/test3", json={"config_id": "test3", "config_data": updated_config})
    assert response.status_code == 200
    assert response.json()["message"] == "VPN configuration updated"
    

    get_response = client.get("/vpn/test3")
    assert get_response.json() == updated_config

def test_delete_vpn_config():

    test_config = {
        "server": "test.vpn.com",
        "port": 1194,
        "protocol": "udp"
    }
    client.post("/vpn/", json={"config_id": "test4", "config_data": test_config})
    
    response = client.delete("/vpn/test4")
    assert response.status_code == 200
    assert response.json()["message"] == "VPN configuration deleted"
    
    get_response = client.get("/vpn/test4")
    assert get_response.json()["error"] == "VPN configuration not found"