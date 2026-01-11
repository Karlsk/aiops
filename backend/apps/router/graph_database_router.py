"""
SDN控制器相关API路由
"""

from typing import Dict, List, Optional
from fastapi import HTTPException, Depends, APIRouter, Query
from pydantic import BaseModel

from apps.models.service.api_schema import Neo4jLabelsResponse, Neo4jRelationshipTypesResponse, ApiResponse, NodeCreate, \
    NodeDelete, NodeUpdate, RelationshipCreate, RelationshipDelete, RelationshipUpdate, RelationshipDeleteById, \
    RelationshipQuery, DatabaseCreate
from apps.utils.deps import SessionDep, GraphDatabaseSessionDep
from apps.utils.logger import TerraLogUtil

from apps.service.graph_database_service import GraphDatabaseService

router = APIRouter(tags=["GraphDatabase"], prefix="/graph/database")


def get_graph_db_service():
    return GraphDatabaseService()


@router.get(
    "/labels",
    response_model=Neo4jLabelsResponse,
    summary="获取所有节点标签",
    description="获取Neo4j数据库中所有节点标签列表"
)
async def get_all_labels(
        graph_session: GraphDatabaseSessionDep,
        service: GraphDatabaseService = Depends(get_graph_db_service)
):
    """获取所有节点标签"""
    try:
        labels = await service.get_all_labels(graph_session)
        return Neo4jLabelsResponse(labels=labels)
    except HTTPException:
        raise
    except Exception as e:
        TerraLogUtil.error(f"Error fetching all labels: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/relationship-types",
    response_model=Neo4jRelationshipTypesResponse,
    summary="获取所有关系类型",
    description="获取Neo4j数据库中所有关系类型列表"
)
async def get_all_relationship_types(
        graph_session: GraphDatabaseSessionDep,
        service: GraphDatabaseService = Depends(get_graph_db_service)
):
    """获取所有关系类型"""
    try:
        relationship_types = await service.get_all_relationship_types(graph_session)
        return Neo4jRelationshipTypesResponse(relationship_types=relationship_types)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/nodes",
    response_model=ApiResponse,
    summary="创建节点",
    description="在Neo4j数据库中创建新节点，保证label和name的组合唯一"
)
async def create_node(
        node: NodeCreate,
        graph_session: GraphDatabaseSessionDep,
        database: str = None,
        service: GraphDatabaseService = Depends(get_graph_db_service)
):
    """创建节点"""
    try:
        result = await service.create_node(
            graph_helper=graph_session,
            name=node.name,
            label=node.label,
            properties=node.properties,
            database=database
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/nodes",
    response_model=ApiResponse,
    summary="删除节点",
    description="根据name和label删除Neo4j数据库中的节点"
)
async def delete_node(
        node: NodeDelete,
        graph_session: GraphDatabaseSessionDep,
        database: str = None,
        service: GraphDatabaseService = Depends(get_graph_db_service)
):
    """删除节点"""
    try:
        result = await service.delete_node(
            graph_helper=graph_session,
            name=node.name,
            label=node.label,
            database=database
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/nodes",
    response_model=ApiResponse,
    summary="更新节点",
    description="根据name和label更新Neo4j数据库中的节点属性"
)
async def update_node(
        node: NodeUpdate,
        graph_session: GraphDatabaseSessionDep,
        database: str = None,
        service: GraphDatabaseService = Depends(get_graph_db_service)
):
    """更新节点"""
    try:
        result = await service.update_node(
            graph_helper=graph_session,
            name=node.name,
            label=node.label,
            properties=node.properties,
            database=database
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/relationships",
    response_model=ApiResponse,
    summary="创建关系",
    description="在Neo4j数据库中创建节点间的关系"
)
async def create_relationship(
        relationship: RelationshipCreate,
        graph_session: GraphDatabaseSessionDep,
        database: str = None,
        service: GraphDatabaseService = Depends(get_graph_db_service)
):
    """创建关系"""
    try:
        result = await service.create_relationship(
            graph_helper=graph_session,
            from_node_name=relationship.from_node.name,
            from_node_label=relationship.from_node.label,
            to_node_name=relationship.to_node.name,
            to_node_label=relationship.to_node.label,
            relationship_type=relationship.relationship_type,
            relationship_properties=relationship.relationship_properties,
            database=database
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/relationships",
    response_model=ApiResponse,
    summary="删除关系",
    description="删除Neo4j数据库中指定的节点关系"
)
async def delete_relationship(
        relationship: RelationshipDelete,
        graph_session: GraphDatabaseSessionDep,
        service: GraphDatabaseService = Depends(get_graph_db_service),
        database: str = None
):
    """删除关系"""
    try:
        result = await service.delete_relationship(
            graph_helper=graph_session,
            from_node_name=relationship.from_node.name,
            from_node_label=relationship.from_node.label,
            to_node_name=relationship.to_node.name,
            to_node_label=relationship.to_node.label,
            relationship_type=relationship.relationship_type,
            database=database
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/relationships",
    response_model=ApiResponse,
    summary="更新关系",
    description="更新Neo4j数据库中指定的节点关系属性"
)
async def update_relationship(
        relationship: RelationshipUpdate,
        graph_session: GraphDatabaseSessionDep,
        service: GraphDatabaseService = Depends(get_graph_db_service),
        database: str = None
):
    """更新关系"""
    try:
        result = await service.update_relationship(
            graph_helper=graph_session,
            from_node_name=relationship.from_node.name,
            from_node_label=relationship.from_node.label,
            to_node_name=relationship.to_node.name,
            to_node_label=relationship.to_node.label,
            relationship_type=relationship.relationship_type,
            relationship_properties=relationship.relationship_properties,
            database=database
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/relationships/by-id",
    response_model=ApiResponse,
    summary="通过ID删除关系",
    description="通过Neo4j关系的内部ID精确删除单条关系"
)
async def delete_relationship_by_id(
        relationship: RelationshipDeleteById,
        graph_session: GraphDatabaseSessionDep,
        service: GraphDatabaseService = Depends(get_graph_db_service)
):
    """通过ID删除关系"""
    try:
        result = await service.delete_relationship_by_id(
            graph_helper=graph_session,
            relationship_id=relationship.relationship_id
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/nodes",
    response_model=ApiResponse,
    summary="获取所有节点",
    description="获取Neo4j数据库中的所有节点，支持按标签过滤和限制数量。返回格式为List[NodeCreate]"
)
async def get_all_nodes(
        graph_session: GraphDatabaseSessionDep,
        service: GraphDatabaseService = Depends(get_graph_db_service),
        label: str = None,
        limit: int = 100,
        database: str = None
):
    """获取所有节点，返回格式为List[NodeCreate]"""
    try:
        result = await service.get_all_nodes(
            graph_helper=graph_session,
            label=label,
            limit=limit,
            database=database
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]  # 这里的data已经是List[NodeCreate]格式
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/relationships",
    response_model=ApiResponse,
    summary="获取所有关系",
    description="获取Neo4j数据库中的所有关系，支持按关系类型、起始节点标签、目标节点标签过滤和限制数量。返回格式为List[RelationshipInfo]"
)
async def get_all_relationships(
        graph_session: GraphDatabaseSessionDep,
        service: GraphDatabaseService = Depends(get_graph_db_service),
        relationship_type: str = None,
        from_label: str = None,
        to_label: str = None,
        limit: int = 100,
        database: str = None
):
    """获取所有关系，返回格式为List[RelationshipInfo]"""
    try:
        result = await service.get_all_relationships(
            graph_helper=graph_session,
            relationship_type=relationship_type,
            from_label=from_label,
            to_label=to_label,
            limit=limit,
            database=database
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]  # 这里的data已经是List[RelationshipInfo]格式
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/nodes/{label}/{name}",
    response_model=ApiResponse,
    summary="通过label和name获取单个节点",
    description="通过指定的label和name获取单个节点信息。返回格式为NodeCreate"
)
async def get_node_by_label_and_name(
        label: str,
        name: str,
        graph_session: GraphDatabaseSessionDep,
        service: GraphDatabaseService = Depends(get_graph_db_service),
        database: str = None
):
    """通过label和name获取单个节点信息"""
    try:
        result = await service.get_node_by_label_and_name(
            graph_helper=graph_session,
            label=label,
            name=name,
            database=database
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/relationships/query",
    response_model=ApiResponse,
    summary="查询特定关系",
    description="通过from_node、to_node和relationship_type查询关系。from_node和to_node为选填，relationship_type为必填。返回格式为List[RelationshipInfo]"
)
async def get_relationships_by_query(
        relationship_query: RelationshipQuery,
        graph_session: GraphDatabaseSessionDep,
        service: GraphDatabaseService = Depends(get_graph_db_service),
        database: str = None
):
    """通过查询条件获取关系信息"""
    try:
        result = await service.get_relationships_by_query(
            graph_helper=graph_session,
            relationship_type=relationship_query.relationship_type,
            from_node_label=relationship_query.from_node.label if relationship_query.from_node else None,
            from_node_name=relationship_query.from_node.name if relationship_query.from_node else None,
            to_node_label=relationship_query.to_node.label if relationship_query.to_node else None,
            to_node_name=relationship_query.to_node.name if relationship_query.to_node else None,
            database=database
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/mermaid",
    response_model=ApiResponse,
    summary="将Neo4j图转换为Mermaid流程图",
    description="根据事件名称查询Neo4j数据库中的路径，并将其转换为Mermaid流程图格式。返回Mermaid语法字符串及统计信息"
)
async def convert_to_mermaid(
        name: str,
        graph_session: GraphDatabaseSessionDep,
        service: GraphDatabaseService = Depends(get_graph_db_service),
        database: str = None
):
    """将Neo4j图数据转换为Mermaid流程图格式"""
    try:
        TerraLogUtil.info(f"convert_to_mermaid name={name} database={database}")
        result = await service.convert_neo4j_to_mermaid(
            graph_helper=graph_session,
            name=name,
            database=database
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/json",
    response_model=ApiResponse,
    summary="将Neo4j图转换为JSON格式",
    description="根据事件名称查询Neo4j数据库中的路径，并将其转换为结构化JSON格式（Plan Schema）。返回包含nodes、edges、start等信息的JSON结构"
)
async def convert_to_json(
        name: str,
        graph_session: GraphDatabaseSessionDep,
        service: GraphDatabaseService = Depends(get_graph_db_service),
        database: str = None
):
    """将Neo4j图数据转换为JSON格式"""
    try:
        result = await service.convert_neo4j_to_json(
            graph_helper=graph_session,
            name=name,
            database=database
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Database 管理 API ====================

@router.post(
    "/databases",
    response_model=ApiResponse,
    summary="创建逻辑数据库",
    description="在MySQL中创建逻辑数据库记录，用于Neo4j社区版的多数据库支持"
)
async def create_database(
        database: DatabaseCreate,
        session: SessionDep,
        service: GraphDatabaseService = Depends(get_graph_db_service),
):
    """创建逻辑数据库"""
    try:
        result = await service.create_database(
            session=session,
            name=database.name,
            description=database.description
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/databases/{name}",
    response_model=ApiResponse,
    summary="删除逻辑数据库",
    description="删除MySQL中的逻辑数据库记录。删除前会校验Neo4j中是否还有该database的节点"
)
async def delete_database(
        name: str,
        graph_session: GraphDatabaseSessionDep,
        session: SessionDep,
        service: GraphDatabaseService = Depends(get_graph_db_service),
):
    """删除逻辑数据库"""
    try:
        result = await service.delete_database(
            session=session,
            graph_helper=graph_session,
            name=name
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/databases",
    response_model=ApiResponse,
    summary="获取所有逻辑数据库",
    description="获取MySQL中存储的所有逻辑数据库信息"
)
async def get_databases(session: SessionDep, service: GraphDatabaseService = Depends(get_graph_db_service)):
    """获取所有逻辑数据库"""
    try:
        result = await service.get_databases(session)
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 工作流节点 API ====================

@router.get(
    "/workflow/next-node",
    response_model=ApiResponse,
    summary="获取工作流下一步节点信息（简化）",
    description="根据当前节点的name和database获取下一步节点信息，返回nodes和edges。\n" +
                "不包含node的label、properties和edge的relationship_type。"
)
async def get_workflow_next_node(
        name: str,
        graph_session: GraphDatabaseSessionDep,
        service: GraphDatabaseService = Depends(get_graph_db_service),
        database: str = None
):
    """获取工作流下一步节点信息（简化）"""
    try:
        result = await service.get_workflow_next_node(
            graph_helper=graph_session,
            current_name=name,
            database=database,
            include_details=False
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/workflow/next-node-detail",
    response_model=ApiResponse,
    summary="获取工作流下一步节点信息（详细）",
    description="根据当前节点的name和database获取下一步节点详细信息，返回nodes和edges。\n" +
                "- Event标签节点返回下一个节点，无edges，标记为首节点\n" +
                "- Sequence关系返回当前节点和下一个节点，edges返回from/to/relationship_type\n" +
                "- Branch关系返回当前节点和多个节点，edges返回from/to/relationship_type/condition\n" +
                "- function_call类型节点包含action和observation属性\n" +
                "- final_answer类型节点包含reason属性"
)
async def get_workflow_next_node_detail(
        name: str,
        graph_session: GraphDatabaseSessionDep,
        service: GraphDatabaseService = Depends(get_graph_db_service),
        database: str = None
):
    """获取工作流下一步节点详细信息"""
    try:
        result = await service.get_workflow_next_node(
            graph_helper=graph_session,
            current_name=name,
            database=database,
            include_details=True
        )
        return ApiResponse(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
