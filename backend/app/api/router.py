from fastapi import APIRouter

from app.api.routes import artifacts, auth, brain, chat, documents, vision, workspaces

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(brain.router, prefix="/brain", tags=["brain"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(artifacts.router, tags=["artifacts"])
api_router.include_router(vision.router, tags=["vision"])

