import pytest
from unittest.mock import patch
from pathlib import Path
from service_layer.wireguard import (
    generate_keys,
    create_interface,
    add_peer,
    remove_peer,
    get_interface_info,
    sync_config,
)


@pytest.fixture
def mock_run_command():
    with patch("wireguard.cli.run_command") as mock:
        yield mock


def test_generate_keys(mock_run_command):
    mock_run_command.side_effect = [("private_key_123\n", ""), ("public_key_456\n", "")]

    result = generate_keys()

    assert result == {"private_key": "private_key_123", "public_key": "public_key_456"}
    assert mock_run_command.call_count == 2


def test_create_interface(mock_run_command):
    with patch("pathlib.Path.write_text") as mock_write:
        create_interface(
            name="wg0",
            private_key="private_key_123",
            listen_port=51820,
            address="10.0.0.1/24",
            dns="1.1.1.1",
        )

        expected_config = "\n".join(
            [
                "[Interface]",
                "PrivateKey = private_key_123",
                "ListenPort = 51820",
                "Address = 10.0.0.1/24",
                "DNS = 1.1.1.1",
            ]
        )

        mock_write.assert_called_once_with(expected_config)
        mock_run_command.assert_called_once_with(["wg-quick", "up", "wg0"])


def test_add_peer(mock_run_command):
    add_peer(
        interface="wg0",
        public_key="public_key_456",
        allowed_ips="10.0.0.2/32",
        endpoint="example.com:51820",
        persistent_keepalive=25,
    )

    mock_run_command.assert_called_once_with(
        [
            "wg",
            "set",
            "wg0",
            "peer",
            "public_key_456",
            "allowed-ips",
            "10.0.0.2/32",
            "endpoint",
            "example.com:51820",
            "persistent-keepalive",
            "25",
        ]
    )


def test_remove_peer(mock_run_command):
    remove_peer(interface="wg0", public_key="public_key_456")

    mock_run_command.assert_called_once_with(
        ["wg", "set", "wg0", "peer", "public_key_456", "remove"]
    )


def test_get_interface_info(mock_run_command):
    mock_run_command.return_value = (
        "public_key_1\t\t1.2.3.4:51820\t10.0.0.2/32\t1620000000\t1000\t2000\t25\n",
        "",
    )

    result = get_interface_info("wg0")

    assert result == {
        "name": "wg0",
        "peers": [
            {
                "public_key": "public_key_1",
                "preshared_key": "",
                "endpoint": "1.2.3.4:51820",
                "allowed_ips": "10.0.0.2/32",
                "latest_handshake": "1620000000",
                "transfer_rx": "1000",
                "transfer_tx": "2000",
                "persistent_keepalive": "25",
            }
        ],
    }


def test_sync_config(mock_run_command):
    config = {
        "interfaces": [
            {
                "name": "wg0",
                "private_key": "private_key_123",
                "listen_port": 51820,
                "address": "10.0.0.1/24",
                "dns": "1.1.1.1",
                "peers": [
                    {
                        "public_key": "public_key_456",
                        "allowed_ips": "10.0.0.2/32",
                        "endpoint": "example.com:51820",
                        "persistent_keepalive": 25,
                    }
                ],
            }
        ]
    }

    config_file = Path("/tmp/wg-config.json")
    with patch("pathlib.Path.exists") as mock_exists, patch(
        "pathlib.Path.read_text"
    ) as mock_read, patch("json.loads") as mock_loads:

        mock_exists.return_value = True
        mock_read.return_value = "{}"
        mock_loads.return_value = config

        sync_config(config_file)
