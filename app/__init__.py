from fastapi import FastAPI
from app.api.notification_router import router as notification_router

def create_app():
    app = FastAPI()

    app.include_router(notification_router)

    @app.get("/")
    async def root():
        return {"message": "Notification Service is running"}

    return app
