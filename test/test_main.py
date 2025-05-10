from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_vpn_config():
    test_config = {
        "server": "test.vpn.com",
        "port": 1194,
        "protocol": "udp"
    }
    response = client.post("/api/v1/config", json={"config_data": test_config})
    assert response.status_code == 200
    assert response.json()["message"] == "VPN configuration created"
    config_id = response.json()["config_id"]
    assert response.json()["config_id"] is not None
    response = client.get(f"/api/v1/config/{config_id}")
    assert response.json() == test_config
    updated_config = {
        "server": "new.vpn.com",
        "port": 443,
        "protocol": "tcp"
    }
    response = client.put(f"/api/v1/config/{config_id}", json={ "config_data": updated_config})
    assert response.status_code == 200
    assert response.json()["message"] == "VPN configuration updated"
    get_response = client.get(f"/api/v1/config/{config_id}")
    assert get_response.json() == updated_config
    response = client.delete(f"/api/v1/config/{config_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "VPN configuration deleted"
    
    get_response = client.get(f"/api/v1/config/{config_id}")
    assert get_response.status_code == 404