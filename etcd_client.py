import etcd
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class EtcdClient:
    def __init__(self, host='localhost', port=2379):
        self.client = etcd.Client(host=host, port=port)
        self.base_key = '/vpn/configs/'
        self.users_key = '/vpn/users/'
        self.counter_key = '/vpn/counter'
        # Initialize counter if it doesn't exist
        try:
            self.client.read(self.counter_key)
        except etcd.EtcdKeyNotFound:
            self.client.write(self.counter_key, '0')

    def _get_full_key(self, config_id: int) -> str:
        return f"{self.base_key}{config_id}"

    def _get_user_key(self, username: str) -> str:
        return f"{self.users_key}{username}"

    def _get_next_id(self) -> int:
        try:
            counter = self.client.read(self.counter_key)
            next_id = int(counter.value) + 1
            self.client.write(self.counter_key, str(next_id))
            return next_id
        except etcd.EtcdConnectionFailed as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to etcd {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def create_config(self, config_data: Dict[str, Any]) -> int:
        try:
            config_id = self._get_next_id()
            full_key = self._get_full_key(config_id)
            self.client.write(full_key, json.dumps(config_data))
            return config_id
        except etcd.EtcdConnectionFailed as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to etcd {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

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

    def create_user(self, username: str, password: str, vpn_config: Optional[Dict[str, Any]] = None) -> None:
        try:
            user_key = self._get_user_key(username)
            try:
                self.client.read(user_key)
                raise HTTPException(status_code=400, detail="User already exists")
            except etcd.EtcdKeyNotFound:
                hashed_password = pwd_context.hash(password)
                user_data = {
                    "username": username,
                    "password": hashed_password,
                    "vpn_config": vpn_config
                }
                self.client.write(user_key, json.dumps(user_data))
        except etcd.EtcdConnectionFailed as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to etcd {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        try:
            user_key = self._get_user_key(username)
            result = self.client.read(user_key)
            return json.loads(result.value)
        except etcd.EtcdKeyNotFound:
            return None
        except etcd.EtcdConnectionFailed as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to etcd {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def verify_password(self, username: str, password: str) -> bool:
        user = self.get_user(username)
        if not user:
            return False
        return pwd_context.verify(password, user["password"])