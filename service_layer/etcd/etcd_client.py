import etcd3
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class EtcdClient:
    def __init__(self, host="localhost", port=2379):
        self.client = etcd3.client(host=host, port=port)
        self.counter_key = "/vpn/counter"
        # Initialize counter if it doesn't exist
        if not self.client.get(self.counter_key)[0]:
            self.client.put(self.counter_key, b"0")

    def _get_full_key(self, config_id: int) -> str:
        return f"{self.base_key}{config_id}"

    def _get_next_id(self) -> int:
        try:
            counter_value = self.client.get(self.counter_key)[0]
            next_id = int(counter_value.decode("utf-8")) + 1
            self.client.put(self.counter_key, str(next_id).encode("utf-8"))
            return next_id
        except Exception as e:
            raise HTTPException(
                status_code=503, detail=f"Failed to get next ID: {str(e)}"
            )


