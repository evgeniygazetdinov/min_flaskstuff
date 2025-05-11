from fastapi import APIRouter, HTTPException

from models.vpn_config import VPNConfigRequest
from query_sets.vpn_config import VpnConfigQuerySets

router = APIRouter(prefix="/api/v1/config", tags=["Config"])


query_set = VpnConfigQuerySets()


@router.post("/")
def create_vpn_config(config_request: VPNConfigRequest):
    try:
        config_id = query_set.create_config(config_request.config_data)
        return {"message": "VPN configuration created", "config_id": config_id}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{config_id}")
def read_vpn_config(config_id: int):
    config = query_set.get_config(config_id)
    if config is None:
        raise HTTPException(status_code=404, detail="VPN configuration not found")
    return config


@router.get("/")
def list_vpn_configs():
    return query_set.list_configs()


@router.put("/{config_id}")
def update_vpn_config(config_id: int, config_request: VPNConfigRequest):
    if query_set.update_config(config_id, config_request.config_data):
        return {"message": "VPN configuration updated", "config_id": config_id}
    raise HTTPException(status_code=404, detail="VPN configuration not found")


@router.delete("/{config_id}")
def delete_vpn_config(config_id: int):
    if query_set.delete_config(config_id):
        return {"message": "VPN configuration deleted", "config_id": config_id}
    raise HTTPException(status_code=404, detail="VPN configuration not found")
