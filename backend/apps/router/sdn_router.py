"""
SDN控制器相关API路由
"""

from typing import Dict, List, Optional
from fastapi import HTTPException, Depends, APIRouter, Query
from pydantic import BaseModel

from apps.utils.deps import SessionDep, GraphDatabaseSessionDep
from apps.utils.logger import TerraLogUtil

from apps.service.sdn_controller_service import SDNControllerService
from apps.models.service.sdn_models import SDNController, SDNControllerStatus
from apps.models.service.api_schema import SDNControllerCreate, SDNControllerUpdate, ApiResponse, \
    TopologySnapshotsResponse, TopologySnapshotResponse

router = APIRouter(tags=["SDNController"], prefix="/sdn")


def get_sdn_service():
    return SDNControllerService()


@router.post("/controllers", summary="创建SDN控制器配置", response_model=SDNController)
async def create_controller(
        controller_data: SDNControllerCreate,
        session: SessionDep,
        service: SDNControllerService = Depends(get_sdn_service)
):
    """创建SDN控制器配置"""
    try:
        controller = await service.create_controller(session, controller_data)
        return controller
    except HTTPException:
        raise
    except Exception as e:
        TerraLogUtil.error(f"Error creating SDN controller: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/controllers", response_model=List[SDNController])
async def list_controllers(
        session: SessionDep,
        service: SDNControllerService = Depends(get_sdn_service)
):
    """列出所有SDN控制器配置"""
    try:
        controllers = await service.list_controllers(session)
        return controllers or []
    except Exception as e:
        TerraLogUtil.error(f"Error listing SDN controllers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/controllers/{controller_id}", response_model=SDNController)
async def get_controller(
        controller_id: int,
        session: SessionDep,
        service: SDNControllerService = Depends(get_sdn_service)
):
    """获取指定ID的SDN控制器配置"""
    try:
        controller = await service.get_controller(session, controller_id)
        if not controller:
            raise HTTPException(status_code=404, detail="SDN Controller not found")
        return controller
    except HTTPException:
        raise
    except Exception as e:
        TerraLogUtil.error(f"Error fetching SDN controller {controller_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/controllers/{controller_id}", response_model=SDNController)
async def update_controller(
        controller_id: int,
        controller_data: SDNControllerUpdate,
        session: SessionDep,
        service: SDNControllerService = Depends(get_sdn_service)
):
    """更新指定ID的SDN控制器配置"""
    try:
        controller = await service.update_controller(session, controller_id, controller_data)
        if not controller:
            raise HTTPException(status_code=404, detail="SDN Controller not found")
        return controller
    except HTTPException:
        raise
    except Exception as e:
        TerraLogUtil.error(f"Error updating SDN controller {controller_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/controllers/{controller_id}", response_model=ApiResponse)
async def delete_controller(
        controller_id: int,
        session: SessionDep,
        service: SDNControllerService = Depends(get_sdn_service)
):
    """删除指定ID的SDN控制器配置"""
    try:
        success = await service.delete_controller(session, controller_id)
        if not success:
            raise HTTPException(status_code=404, detail="SDN Controller not found")
        return ApiResponse(status="success", message="SDN Controller deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        TerraLogUtil.error(f"Error deleting SDN controller {controller_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/controllers/{controller_id}/test")
async def test_controller_connection(
        controller_id: int,
        session: SessionDep,
        service: SDNControllerService = Depends(get_sdn_service)
):
    """测试与指定SDN控制器的连接，并根据结果自动更新状态"""
    try:
        # 测试连接
        result = await service.test_controller_connection(session, controller_id)
        
        # 根据测试结果更新状态
        if result.get("status") == "success":
            # 测试成功，更新为ACTIVE
            await service.update_controller_status(session, controller_id, SDNControllerStatus.ACTIVE)
        else:
            # 测试失败，更新为ERROR
            await service.update_controller_status(session, controller_id, SDNControllerStatus.ERROR)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        TerraLogUtil.error(f"Error testing connection for SDN controller {controller_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/controllers/{controller_id}/topology")
async def get_topology(
        controller_id: int,
        session: SessionDep,
        service: SDNControllerService = Depends(get_sdn_service)
):
    """获取指定SDN控制器的网络拓扑"""
    try:
        topology = await service.get_topology(session, controller_id)
        return topology
    except HTTPException:
        raise
    except Exception as e:
        TerraLogUtil.error(f"Error fetching topology for SDN controller {controller_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/controllers/{controller_id}/sync_topology")
async def sync_topology(
        controller_id: int,
        session: SessionDep,
        graph_session: GraphDatabaseSessionDep,
        service: SDNControllerService = Depends(get_sdn_service)
):
    """同步指定SDN控制器的网络拓扑"""
    try:
        topology = await service.sync_topology(session, graph_session, controller_id)
        return topology
    except HTTPException:
        raise
    except Exception as e:
        TerraLogUtil.error(f"Error syncing topology for SDN controller {controller_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/controllers/{controller_id}/monitoring")
async def get_monitoring_data(
        controller_id: int,
        session: SessionDep,
        metric_name: Optional[str] = Query(None, description="指定监控指标名称"),
        service: SDNControllerService = Depends(get_sdn_service)
):
    """获取指定SDN控制器的监控数据"""
    """获取监控数据"""
    try:
        result = await service.get_monitoring_data(session, controller_id, metric_name)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/controllers/{controller_id}/logs")
async def get_logs(
        controller_id: int,
        session: SessionDep,
        level: Optional[str] = Query(None, description="日志级别过滤"),
        limit: int = Query(100, description="返回日志条数限制"),
        service: SDNControllerService = Depends(get_sdn_service)
):
    """获取指定SDN控制器的日志信息"""
    try:
        result = await service.get_logs(session, controller_id, level, limit)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/snapshots", response_model=TopologySnapshotsResponse)
async def list_snapshots(
        session: SessionDep,
        controller_id: Optional[int] = Query(None, description="控制器ID过滤"),
        service: SDNControllerService = Depends(get_sdn_service)
):
    """列出网络拓扑快照"""
    try:
        snapshots = await service.list_snapshots(session, controller_id)
        # 直接使用 model_validate 或 from_orm，让 Pydantic 处理类型转换
        snapshots_data = [TopologySnapshotResponse.model_validate(snap) for snap in snapshots]
        return TopologySnapshotsResponse(
            snapshots=snapshots_data,
            total=len(snapshots_data)
        )
    except Exception as e:
        TerraLogUtil.error(f"Error listing topology snapshots: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/snapshots/{snapshot_id}", response_model=TopologySnapshotResponse)
async def get_snapshot(
        snapshot_id: int,
        session: SessionDep,
        service: SDNControllerService = Depends(get_sdn_service)
):
    """获取指定拓扑快照"""
    try:
        snapshot = await service.get_snapshot(session, snapshot_id)
        if not snapshot:
            raise HTTPException(status_code=404, detail="Snapshot not found")
        return TopologySnapshotResponse.model_validate(snapshot)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/snapshots/{snapshot_id}")
async def delete_snapshot(
        snapshot_id: int,
        session: SessionDep,
        service: SDNControllerService = Depends(get_sdn_service)
):
    """删除指定拓扑快照"""
    try:
        result = await service.delete_snapshot(session, snapshot_id)
        if result["status"] == "error":
            if "not found" in result["message"].lower():
                raise HTTPException(status_code=404, detail=result["message"])
            else:
                raise HTTPException(status_code=500, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/controllers/{controller_id}/snapshots")
async def delete_snapshots_by_controller(
        controller_id: int,
        session: SessionDep,
        service: SDNControllerService = Depends(get_sdn_service)
):
    """删除指定控制器的所有快照"""
    try:
        result = await service.delete_snapshots_by_controller(session, controller_id)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
