import etcd3
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class EtcdClient:
    def __init__(self, host='localhost', port=2379):
        self.client = etcd3.client(host=host, port=port)
        self.base_key = '/vpn/configs/'
        self.users_key = '/vpn/users/'
        self.counter_key = '/vpn/counter'
        # Initialize counter if it doesn't exist
        if not self.client.get(self.counter_key)[0]:
            self.client.put(self.counter_key, b'0')

    def _get_full_key(self, config_id: int) -> str:
        return f"{self.base_key}{config_id}"

    def _get_user_key(self, username: str) -> str:
        return f"{self.users_key}{username}"

    def _get_next_id(self) -> int:
        try:
            counter_value = self.client.get(self.counter_key)[0]
            next_id = int(counter_value.decode('utf-8')) + 1
            self.client.put(self.counter_key, str(next_id).encode('utf-8'))
            return next_id
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Failed to get next ID: {str(e)}")

    def create_config(self, config_data: Dict[str, Any]) -> int:
        try:
            config_id = self._get_next_id()
            full_key = self._get_full_key(config_id)
            self.client.put(full_key, json.dumps(config_data).encode('utf-8'))
            return config_id
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Failed to create config: {str(e)}")

    def get_config(self, config_id: int) -> Optional[Dict[str, Any]]:
        try:
            full_key = self._get_full_key(config_id)
            result = self.client.get(full_key)[0]
            if result is None:
                return None
            return json.loads(result.decode('utf-8'))
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Failed to get config: {str(e)}")

    def update_config(self, config_id: int, config_data: Dict[str, Any]) -> bool:
        try:
            full_key = self._get_full_key(config_id)
            if self.client.get(full_key)[0] is None:
                return False
            self.client.put(full_key, json.dumps(config_data).encode('utf-8'))
            return True
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Failed to update config: {str(e)}")

    def delete_config(self, config_id: int) -> bool:
        try:
            full_key = self._get_full_key(config_id)
            if self.client.get(full_key)[0] is None:
                return False
            self.client.delete(full_key)
            return True
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Failed to delete config: {str(e)}")

    def list_configs(self) -> Dict[int, Dict[str, Any]]:
        try:
            configs = {}
            for item in self.client.get_prefix(self.base_key):
                key = item[1].key.decode('utf-8')
                config_id = int(key.split('/')[-1])
                configs[config_id] = json.loads(item[0].decode('utf-8'))
            return configs
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Failed to list configs: {str(e)}")

    def create_user(self, username: str, password: str, vpn_config: Optional[Dict[str, Any]] = None) -> None:
        try:
            user_key = self._get_user_key(username)
            if self.client.get(user_key)[0] is not None:
                raise HTTPException(status_code=400, detail="User already exists")
            
            user_data = {
                "username": username,
                "password": pwd_context.hash(password),
                "vpn_config": vpn_config
            }
            self.client.put(user_key, json.dumps(user_data).encode('utf-8'))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Failed to create user: {str(e)}")

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        try:
            user_key = self._get_user_key(username)
            result = self.client.get(user_key)[0]
            if result is None:
                return None
            return json.loads(result.decode('utf-8'))
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Failed to get user: {str(e)}")

    def verify_password(self, username: str, password: str) -> bool:
        user = self.get_user(username)
        if not user:
            return False
        return pwd_context.verify(password, user["password"])