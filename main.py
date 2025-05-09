from fastapi import FastAPI, HTTPException
from models import VPNConfigRequest
from etcd_client import EtcdClient

app = FastAPI()
etcd_client = EtcdClient()

@app.post("/vpn/")
def create_vpn_config(config_request: VPNConfigRequest):
    try:
        config_id = etcd_client.create_config(config_request.config_data)
        return {"message": "VPN configuration created", "config_id": config_id}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vpn/{config_id}")
def read_vpn_config(config_id: int):
    config = etcd_client.get_config(config_id)
    if config is None:
        raise HTTPException(status_code=404, detail="VPN configuration not found")
    return config

@app.get("/vpn/")
def list_vpn_configs():
    return etcd_client.list_configs()

@app.put("/vpn/{config_id}")
def update_vpn_config(config_id: int, config_request: VPNConfigRequest):
    if etcd_client.update_config(config_id, config_request.config_data):
        return {"message": "VPN configuration updated", "config_id": config_id}
    raise HTTPException(status_code=404, detail="VPN configuration not found")

@app.delete("/vpn/{config_id}")
def delete_vpn_config(config_id: int):
    if etcd_client.delete_config(config_id):
        return {"message": "VPN configuration deleted", "config_id": config_id}
    raise HTTPException(status_code=404, detail="VPN configuration not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)