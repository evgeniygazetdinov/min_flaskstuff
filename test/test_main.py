from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest
from main import app

client = TestClient(app)

@pytest.fixture
def mock_etcd():
    with patch('routers.vpn_config.etcd_client') as mock_client:

        configs = {}
        counter = 0
        
        def mock_create_config(config_data):
            nonlocal counter
            counter += 1
            configs[counter] = config_data
            return counter
            
        def mock_get_config(config_id):
            return configs.get(config_id)
            
        def mock_update_config(config_id, config_data):
            if config_id in configs:
                configs[config_id] = config_data
                return True
            return False
            
        def mock_delete_config(config_id):
            if config_id in configs:
                del configs[config_id]
                return True
            return False
            
        def mock_list_configs():
            return configs

        mock_client.create_config = MagicMock(side_effect=mock_create_config)
        mock_client.get_config = MagicMock(side_effect=mock_get_config)
        mock_client.update_config = MagicMock(side_effect=mock_update_config)
        mock_client.delete_config = MagicMock(side_effect=mock_delete_config)
        mock_client.list_configs = MagicMock(side_effect=mock_list_configs)
        
        yield mock_client

def test_create_vpn_config(mock_etcd):
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
    assert response.status_code == 200
    assert response.json() == test_config
    mock_etcd.get_config.assert_called_with(config_id)

    updated_config = {
        "server": "new.vpn.com",
        "port": 443,
        "protocol": "tcp"
    }
    response = client.put(f"/api/v1/config/{config_id}", json={"config_data": updated_config})
    assert response.status_code == 200
    assert response.json()["message"] == "VPN configuration updated"
    mock_etcd.update_config.assert_called_with(config_id, updated_config)
    
    get_response = client.get(f"/api/v1/config/{config_id}")
    assert get_response.status_code == 200
    assert get_response.json() == updated_config
    response = client.delete(f"/api/v1/config/{config_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "VPN configuration deleted"
    mock_etcd.delete_config.assert_called_with(config_id)
    
    get_response = client.get(f"/api/v1/config/{config_id}")
    assert get_response.status_code == 404