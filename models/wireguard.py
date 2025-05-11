from typing import Optional, List
from pydantic import BaseModel


class WireGuardInterface(BaseModel):
    name: str
    private_key: Optional[str] = None
    listen_port: int
    address: str
    dns: Optional[str] = None


class WireGuardPeer(BaseModel):
    public_key: str
    allowed_ips: str
    endpoint: Optional[str] = None
    persistent_keepalive: Optional[int] = None
