from fastapi import FastAPI

app = FastAPI()

from routers.vpn_config import router as config_router
# from routers.auth_router import router as config_router

# app.include_router(notification_router)
app.include_router(config_router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)