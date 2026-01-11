from fastapi import APIRouter

from apps.router import mcp_router, graph_position_router, sdn_router, graph_database_router, common

api_router = APIRouter()
api_router.include_router(mcp_router.router)
api_router.include_router(graph_position_router.router)
api_router.include_router(sdn_router.router)
api_router.include_router(graph_database_router.router)
api_router.include_router(common.router)