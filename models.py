from pydantic import BaseModel
from typing import Dict, Any


class VPNConfigRequest(BaseModel):
    config_id: int
    config_data: Dict[str, Any]