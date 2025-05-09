import pytest
from etcd_client import EtcdClient
import etcd
from fastapi import HTTPException

@pytest.fixture
def etcd_client():
    client = EtcdClient()
    try:
        client.client.delete('/vpn/configs/', recursive=True)
    except etcd.EtcdKeyNotFound:
        pass
    return client

def test_create_config(etcd_client):
    config_id = 1
    config_data = {
        "server": "test.vpn.com",
        "port": 1194,
        "protocol": "udp"
    }
    
    etcd_client.create_config(config_id, config_data)
    
    stored_config = etcd_client.get_config(config_id)
    assert stored_config == config_data

def test_create_duplicate_config(etcd_client):
    config_id = 2
    config_data = {"server": "test.vpn.com"}
    
    etcd_client.create_config(config_id, config_data)
    
    with pytest.raises(HTTPException) as exc_info:
        etcd_client.create_config(config_id, config_data)
    assert exc_info.value.status_code == 400
    assert "Configuration already exists" in exc_info.value.detail

def test_get_nonexistent_config(etcd_client):
    assert etcd_client.get_config(999) is None

def test_update_config(etcd_client):
    config_id = 3
    initial_config = {"server": "old.vpn.com"}
    updated_config = {"server": "new.vpn.com"}
    
    etcd_client.create_config(config_id, initial_config)
    
    success = etcd_client.update_config(config_id, updated_config)
    assert success is True
    
    stored_config = etcd_client.get_config(config_id)
    assert stored_config == updated_config

def test_update_nonexistent_config(etcd_client):
    success = etcd_client.update_config(999, {"server": "test.vpn.com"})
    assert success is False

def test_delete_config(etcd_client):
    config_id = 4
    config_data = {"server": "test.vpn.com"}
    
    etcd_client.create_config(config_id, config_data)
    
    success = etcd_client.delete_config(config_id)
    assert success is True
    
    assert etcd_client.get_config(config_id) is None

def test_delete_nonexistent_config(etcd_client):
    success = etcd_client.delete_config(999)
    assert success is False

def test_list_configs(etcd_client):
    configs = {
        1: {"server": "vpn1.com"},
        2: {"server": "vpn2.com"},
        3: {"server": "vpn3.com"}
    }
    
    for config_id, config_data in configs.items():
        etcd_client.create_config(config_id, config_data)
    
    stored_configs = etcd_client.list_configs()
    assert stored_configs == configs