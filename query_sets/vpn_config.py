import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from service_layer.etcd.etcd_client import EtcdClient


class VpnConfigQuerySets(EtcdClient):
    def __init__(self):
        super().__init__()
        self.config = "/vpn/users/"

    def create_config(self, config_data: Dict[str, Any]) -> int:
        try:
            config_id = self._get_next_id()
            full_key = self._get_full_key(config_id)
            self.client.put(full_key, json.dumps(config_data).encode("utf-8"))
            return config_id
        except Exception as e:
            raise HTTPException(
                status_code=503, detail=f"Failed to create config: {str(e)}"
            )

    def get_config(self, config_id: int) -> Optional[Dict[str, Any]]:
        try:
            full_key = self._get_full_key(config_id)
            result = self.client.get(full_key)[0]
            if result is None:
                return None
            return json.loads(result.decode("utf-8"))
        except Exception as e:
            raise HTTPException(
                status_code=503, detail=f"Failed to get config: {str(e)}"
            )

    def update_config(self, config_id: int, config_data: Dict[str, Any]) -> bool:
        try:
            full_key = self._get_full_key(config_id)
            if self.client.get(full_key)[0] is None:
                return False
            self.client.put(full_key, json.dumps(config_data).encode("utf-8"))
            return True
        except Exception as e:
            raise HTTPException(
                status_code=503, detail=f"Failed to update config: {str(e)}"
            )

    def delete_config(self, config_id: int) -> bool:
        try:
            full_key = self._get_full_key(config_id)
            if self.client.get(full_key)[0] is None:
                return False
            self.client.delete(full_key)
            return True
        except Exception as e:
            raise HTTPException(
                status_code=503, detail=f"Failed to delete config: {str(e)}"
            )

    def list_configs(self) -> Dict[int, Dict[str, Any]]:
        try:
            configs = {}
            for item in self.client.get_prefix(self.base_key):
                key = item[1].key.decode("utf-8")
                config_id = int(key.split("/")[-1])
                configs[config_id] = json.loads(item[0].decode("utf-8"))
            return configs
        except Exception as e:
            raise HTTPException(
                status_code=503, detail=f"Failed to list configs: {str(e)}"
            )