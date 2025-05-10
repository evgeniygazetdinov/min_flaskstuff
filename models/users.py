from pydantic import BaseModel
from typing import Dict, Any, Optional

class User(BaseModel):
    username: str
    password: str
    vpn_config: Optional[Dict[str, Any]] = None

class UserAuth(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str