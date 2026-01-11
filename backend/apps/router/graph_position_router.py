"""
图谱节点位置API路由
"""
from typing import Dict
from fastapi import HTTPException, Depends, APIRouter
from pydantic import BaseModel


from apps.utils.deps import SessionDep
from apps.utils.logger import TerraLogUtil

from apps.service.graph_position_service import GraphPositionService
from apps.models.service.api_schema import ApiResponse

router = APIRouter(tags=["GraphPosition"], prefix="/graph/positions")


class NodePositionUpdate(BaseModel):
    """节点位置更新模型"""
    node_id: str
    x: float
    y: float


class PositionsBatchUpdate(BaseModel):
    """批量更新节点位置模型"""
    positions: Dict[str, Dict[str, float]]


def get_position_service():
    return GraphPositionService()


@router.get("", summary="获取所有节点位置", description="获取所有保存的节点位置信息")
async def get_all_positions(
        session: SessionDep,
        database: str = 'default',
        service: GraphPositionService = Depends(get_position_service)
):
    """获取所有节点位置"""
    try:
        positions = service.get_all_positions(session, database)
        return ApiResponse(
            status="success",
            message="获取节点位置成功",
            data=positions
        )
    except Exception as e:
        TerraLogUtil.error(f"Error fetching all positions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", summary="批量保存节点位置",
             description="批量保存所有节点的位置信息（使用 UPSERT 逻辑，不会删除其他节点）")
async def batch_update_positions(
        payload: PositionsBatchUpdate,
        session: SessionDep,
        database: str = 'default',
        service: GraphPositionService = Depends(get_position_service)
):
    """批量保存节点位置"""
    try:
        success = await service.save_positions(session, payload.positions, database=database)
        if success:
            return ApiResponse(
                status="success",
                message=f"成功保存 {len(payload.positions)} 个节点位置到画布 {database}"
            )
        else:
            raise HTTPException(status_code=500, detail="保存节点位置失败")
    except Exception as e:
        TerraLogUtil.error(f"Error batch updating positions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{node_id}", summary="更新单个节点位置", description="更新指定节点的位置信息")
async def update_position(
        node_id: str,
        payload: NodePositionUpdate,
        session: SessionDep,
        database: str = 'default',
        service: GraphPositionService = Depends(get_position_service)
):
    """更新单个节点位置"""
    try:
        success = await service.update_position(
            session,
            node_id=payload.node_id,
            x=payload.x,
            y=payload.y,
            database=database
        )
        if success:
            return ApiResponse(
                status="success",
                message=f"成功更新节点 {payload.node_id} 在画布 {database} 的位置"
            )
        else:
            raise HTTPException(status_code=500, detail="更新节点位置失败")
    except Exception as e:
        TerraLogUtil.error(f"Error updating position for node {node_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{node_id}", summary="删除节点位置", description="删除指定节点的位置信息")
async def delete_position(
        node_id: str,
        session: SessionDep,
        database: str = 'default',
        service: GraphPositionService = Depends(get_position_service)
):
    """删除节点位置"""
    try:
        success = await service.delete_position(
            session,
            node_id=node_id,
            database=database
        )
        if success:
            return ApiResponse(
                status="success",
                message=f"成功删除节点 {node_id} 在画布 {database} 的位置"
            )
        else:
            raise HTTPException(status_code=500, detail="删除节点位置失败")
    except Exception as e:
        TerraLogUtil.error(f"Error deleting position for node {node_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("", summary="清空所有节点位置", description="清空所有保存的节点位置信息")
async def clear_all_positions(
        session: SessionDep,
        database: str = 'default',
        service: GraphPositionService = Depends(get_position_service)
):
    """清空所有节点位置"""
    try:
        success = await service.clear_all_positions(session, database)
        if success:
            return ApiResponse(
                status="success",
                message=f"成功清空画布 {database} 的所有节点位置"
            )
        else:
            raise HTTPException(status_code=500, detail="清空节点位置失败")
    except Exception as e:
        TerraLogUtil.error(f"Error clearing all positions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
