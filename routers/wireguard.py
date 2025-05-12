from fastapi import APIRouter, HTTPException
from models.wireguard import WireGuardInterface, WireGuardPeer
from service_layer.wireguard.cli import (
    generate_keys,
    create_interface,
    add_peer,
    remove_peer,
    get_interface_info,
)
from typing import Dict

router = APIRouter(prefix="/api/v1/wireguard", tags=["WireGuard"])

@router.post("/interface", response_model=Dict[str, str])
async def create_wg_interface(interface: WireGuardInterface):
    try:
        if not interface.private_key:
            keys = generate_keys()
            interface.private_key = keys["private_key"]
        
        create_interface(
            name=interface.name,
            private_key=interface.private_key,
            listen_port=interface.listen_port,
            address=interface.address,
            dns=interface.dns
        )
        return {
            "message": "Interface configuration created successfully",
            "note": "To activate the interface, you need to run 'sudo wg-quick up <config_path>' with the generated configuration file"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interface/{name}/peer")
async def add_wg_peer(name: str, peer: WireGuardPeer):
    try:
        add_peer(
            interface=name,
            public_key=peer.public_key,
            allowed_ips=peer.allowed_ips,
            endpoint=peer.endpoint,
            persistent_keepalive=peer.persistent_keepalive
        )
        return {"message": "Peer configuration added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/interface/{name}/peer/{public_key}")
async def remove_wg_peer(name: str, public_key: str):
    try:
        remove_peer(interface=name, public_key=public_key)
        return {"message": "Peer removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/interface/{name}")
async def get_wg_interface(name: str):
    try:
        return get_interface_info(name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))