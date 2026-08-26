from fastapi import APIRouter

from common_gateway_service.controllers.auth_controller import router as auth_router


api_router = APIRouter()
api_router.include_router(auth_router, tags=["auth"])

