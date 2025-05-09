import etcd
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException

class EtcdClient:
    def __init__(self, host='localhost', port=2379):
        self.client = etcd.Client(host=host, port=port)
        self.base_key = '/vpn/configs/'

    def _get_full_key(self, config_id: int) -> str:
        return f"{self.base_key}{config_id}"

    def create_config(self, config_id: int, config_data: Dict[str, Any]) -> None:
        try:
            full_key = self._get_full_key(config_id)
            try:
                self.client.read(full_key)
                raise HTTPException(status_code=400, detail="Configuration already exists")
            except etcd.EtcdKeyNotFound:
                self.client.write(full_key, json.dumps(config_data))
        except etcd.EtcdConnectionFailed:
            raise HTTPException(status_code=503, detail="Failed to connect to etcd")

    def get_config(self, config_id: int) -> Optional[Dict[str, Any]]:
        try:
            full_key = self._get_full_key(config_id)
            result = self.client.read(full_key)
            return json.loads(result.value)
        except etcd.EtcdKeyNotFound:
            return None
        except etcd.EtcdConnectionFailed:
            raise HTTPException(status_code=503, detail="Failed to connect to etcd")

    def update_config(self, config_id: int, config_data: Dict[str, Any]) -> bool:
        try:
            full_key = self._get_full_key(config_id)
            try:
                self.client.read(full_key)
                self.client.write(full_key, json.dumps(config_data))
                return True
            except etcd.EtcdKeyNotFound:
                return False
        except etcd.EtcdConnectionFailed:
            raise HTTPException(status_code=503, detail="Failed to connect to etcd")

    def delete_config(self, config_id: int) -> bool:
        try:
            full_key = self._get_full_key(config_id)
            try:
                self.client.delete(full_key)
                return True
            except etcd.EtcdKeyNotFound:
                return False
        except etcd.EtcdConnectionFailed:
            raise HTTPException(status_code=503, detail="Failed to connect to etcd")

    def list_configs(self) -> Dict[int, Dict[str, Any]]:
        try:
            configs = {}
            try:
                result = self.client.read(self.base_key, recursive=True)
                for child in result.children:
                    config_id = int(child.key.split('/')[-1])
                    configs[config_id] = json.loads(child.value)
            except etcd.EtcdKeyNotFound:
                pass
            return configs
        except etcd.EtcdConnectionFailed:
            raise HTTPException(status_code=503, detail="Failed to connect to etcd")