import pytest
from etcd_client import EtcdClient
from fastapi import HTTPException


@pytest.fixture
def etcd_client():
    client = EtcdClient()
    # Clean up any existing configs
    client.client.delete_prefix("/vpn/configs/")
    client.client.delete_prefix("/vpn/users/")
    # Reset counter each call
    client.client.put("/vpn/counter", b"0")
    return client


def test_create_config(etcd_client):
    config_data = {"server": "test.vpn.com", "port": 1194, "protocol": "udp"}

    config_id = etcd_client.create_config(config_data)

    stored_config = etcd_client.get_config(config_id)
    assert stored_config == config_data


def test_get_nonexistent_config(etcd_client):
    assert etcd_client.get_config(999) is None


def test_update_config(etcd_client):
    initial_config = {"server": "old.vpn.com"}
    updated_config = {"server": "new.vpn.com"}

    config_id = etcd_client.create_config(initial_config)

    success = etcd_client.update_config(config_id, updated_config)
    assert success is True

    stored_config = etcd_client.get_config(config_id)
    assert stored_config == updated_config


def test_update_nonexistent_config(etcd_client):
    success = etcd_client.update_config(999, {"server": "test.vpn.com"})
    assert success is False


def test_delete_config(etcd_client):
    config_data = {"server": "test.vpn.com"}

    config_id = etcd_client.create_config(config_data)

    success = etcd_client.delete_config(config_id)
    assert success is True

    assert etcd_client.get_config(config_id) is None


def test_delete_nonexistent_config(etcd_client):
    success = etcd_client.delete_config(999)
    assert success is False


def test_list_configs(etcd_client):
    configs = {}

    # Create multiple configs and store their IDs
    for server in ["vpn1.com", "vpn2.com", "vpn3.com"]:
        config_data = {"server": server}
        config_id = etcd_client.create_config(config_data)
        configs[config_id] = config_data

    stored_configs = etcd_client.list_configs()
    assert stored_configs == configs


def test_create_user(etcd_client):
    username = "testuser"
    password = "testpass"
    vpn_config = {"server": "user.vpn.com"}

    etcd_client.create_user(username, password, vpn_config)

    user = etcd_client.get_user(username)
    assert user["username"] == username
    assert user["vpn_config"] == vpn_config
    assert etcd_client.verify_password(username, password)


def test_create_duplicate_user(etcd_client):
    username = "testuser2"
    password = "testpass"

    etcd_client.create_user(username, password)

    with pytest.raises(HTTPException) as exc_info:
        etcd_client.create_user(username, password)
    assert exc_info.value.status_code == 400
    assert "User already exists" in str(exc_info.value.detail)


def test_get_nonexistent_user(etcd_client):
    assert etcd_client.get_user("nonexistent") is None


def test_verify_password(etcd_client):
    username = "testuser3"
    password = "testpass"

    etcd_client.create_user(username, password)

    assert etcd_client.verify_password(username, password) is True
    assert etcd_client.verify_password(username, "wrongpass") is False
    assert etcd_client.verify_password("nonexistent", password) is False
