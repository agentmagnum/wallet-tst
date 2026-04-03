from fastapi import FastAPI

from app.api.routes import router as wallets_router
from app.core.config import get_settings


settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(wallets_router)
