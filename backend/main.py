from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from apps.utils.logger import TerraLogUtil
from apps.utils.config import settings
from apps.utils.db import close_graph_db, get_session
from apps.api import api_router
from apps.service.sdn_controller_service import SDNControllerService
from apps.rca.collector.sdn_collector import sdn_collector_manager


async def register_sdn_collectors():
    """重新注册所有已存在的 SDN 控制器"""
    try:
        TerraLogUtil.info("正在重新注册 SDN 控制器...")
        sdn_service = SDNControllerService()
        db_gen = get_session()
        session = next(db_gen)
        try:
            controllers = await sdn_service.list_controllers(session)
            registered_count = 0
            for controller in controllers:
                try:
                    controller_dict = controller.model_dump()
                    # 使用 force=True 强制重新注册，避免重复注册错误
                    sdn_collector_manager.register_collector(controller.type, controller_dict, force=True)
                    registered_count += 1
                    TerraLogUtil.info(f"已注册 SDN 控制器: {controller.name} (类型: {controller.type})")
                except Exception as e:
                    TerraLogUtil.error(f"注册控制器 {controller.name} 失败: {e}")
            TerraLogUtil.info(f"成功重新注册 {registered_count} 个 SDN 控制器")
        finally:
            session.close()
    except Exception as e:
        TerraLogUtil.error(f"重新注册 SDN 控制器时发生错误: {e}")


async def cleanup_sdn_collectors():
    """清理所有已注册的 SDN 收集器"""
    try:
        TerraLogUtil.info("正在清理 SDN 收集器...")
        registered_types = sdn_collector_manager.list_supported_types()
        for controller_type in registered_types:
            sdn_collector_manager.unregister_collector(controller_type)
        TerraLogUtil.info("SDN 收集器已清理")
    except Exception as e:
        TerraLogUtil.error(f"清理 SDN 收集器时发生错误: {e}")


async def startup():
    """应用启动时的初始化逻辑"""
    TerraLogUtil.info("Terra AiOps Platform应用启动中...")
    TerraLogUtil.info("Neo4j 全局连接已初始化")
    
    # 重新注册所有已存在的 SDN 控制器
    await register_sdn_collectors()


async def shutdown():
    """应用关闭时的清理逻辑"""
    TerraLogUtil.info("Terra AiOps Platform应用关闭中...")
    
    # 清理所有注册的收集器
    await cleanup_sdn_collectors()
    
    TerraLogUtil.info("正在关闭 Neo4j 连接...")
    close_graph_db()
    TerraLogUtil.info("Neo4j 连接已关闭")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    await startup()
    
    yield
    
    # 关闭时清理资源
    await shutdown()
    

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
