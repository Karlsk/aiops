from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from apps.utils.logger import TerraLogUtil
from apps.utils.config import settings
from apps.utils.db import close_graph_db
from apps.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 在这里可以添加启动时的初始化逻辑
    TerraLogUtil.info("Terra AiOps Platform应用启动中...")
    TerraLogUtil.info("Neo4j 全局连接已初始化")
    yield
    # 应用关闭时清理资源
    TerraLogUtil.info("Terra AiOps Platform应用关闭中...")
    TerraLogUtil.info("正在关闭 Neo4j 连接...")
    close_graph_db()
    TerraLogUtil.info("Neo4j 连接已关闭")
    

def custom_generate_unique_id(route: APIRoute) -> str:
    tag = route.tags[0] if route.tags and len(route.tags) > 0 else ""
    return f"{tag}-{route.name}"
    
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
app.include_router(api_router, prefix=settings.API_V1_STR)



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.HTTP_HOST, port=settings.HTTP_PORT, reload=True)
