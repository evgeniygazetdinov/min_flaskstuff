import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from service_layer.etcd.etcd_client import EtcdClient, pwd_context


class UsersQuerySets(EtcdClient):
    def __init__(self):
        super().__init__()
        self.users_key = "/vpn/users/"

    def _get_user_key(self, username: str) -> str:
        return f"{self.users_key}{username}"

    def create_user(
        self, username: str, password: str, vpn_config: Optional[Dict[str, Any]] = None
    ) -> None:
        try:
            user_key = self._get_user_key(username)
            if self.client.get(user_key)[0] is not None:
                raise HTTPException(status_code=400, detail="User already exists")

            user_data = {
                "username": username,
                "password": pwd_context.hash(password),
                "vpn_config": vpn_config,
            }
            self.client.put(user_key, json.dumps(user_data).encode("utf-8"))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=503, detail=f"Failed to create user: {str(e)}"
            )

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        try:
            user_key = self._get_user_key(username)
            result = self.client.get(user_key)[0]
            if result is None:
                return None
            return json.loads(result.decode("utf-8"))
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Failed to get user: {str(e)}")

    def verify_password(self, username: str, password: str) -> bool:
        user = self.get_user(username)
        if not user:
            return False
        return pwd_context.verify(password, user["password"])
