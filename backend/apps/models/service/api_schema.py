"""
API请求和响应模型定义
用于FastAPI路由的Pydantic模型
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from pydantic import field_validator

from .sdn_models import SDNControllerType, SDNControllerStatus
# from .alert_models import AlertSeverity, AlertStatus


# ==================== SDN控制器相关API模型 ====================

class SDNControllerCreate(BaseModel):
    """创建SDN控制器请求模型"""
    name: str
    type: SDNControllerType
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    api_token: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

    # @field_validator("type",mode="after")
    # @classmethod
    # def convert_type_to_lowercase(cls, v):
    #     """将请求值转为小写后再验证"""
    #     if isinstance(v, str):
    #         return v.lower()
    #     return v


class SDNControllerUpdate(BaseModel):
    """更新SDN控制器请求模型"""
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_token: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[SDNControllerStatus] = None
    
    class Config:
        # 让Pydantic允许None值
        use_enum_values = True


# ==================== 告警相关API模型 ====================

# class AlertCreate(BaseModel):
#     """创建告警请求模型"""
#     controller_id: int
#     alert_name: str
#     severity: AlertSeverity
#     message: str
#     description: Optional[str] = None
#     source: Optional[str] = None
#     labels: Optional[Dict[str, str]] = None
#     annotations: Optional[Dict[str, str]] = None
#
#
# class AlertRuleCreate(BaseModel):
#     """创建告警规则请求模型"""
#     controller_id: int
#     rule_name: str
#     expression: str
#     severity: AlertSeverity
#     duration: Optional[str] = None
#     labels: Optional[Dict[str, str]] = None
#     annotations: Optional[Dict[str, str]] = None
#     enabled: bool = True
#
#
# class AlertRuleUpdate(BaseModel):
#     """更新告警规则请求模型"""
#     rule_name: Optional[str] = None
#     expression: Optional[str] = None
#     severity: Optional[AlertSeverity] = None
#     duration: Optional[str] = None
#     labels: Optional[Dict[str, str]] = None
#     annotations: Optional[Dict[str, str]] = None
#     enabled: Optional[bool] = None
#
#
# class AlertWebhookCreate(BaseModel):
#     """创建Webhook请求模型"""
#     controller_id: int
#     webhook_name: str
#     url: str
#     method: str = "POST"
#     headers: Optional[Dict[str, str]] = None
#     enabled: bool = True
#
#
# class AlertWebhookUpdate(BaseModel):
#     """更新Webhook请求模型"""
#     webhook_name: Optional[str] = None
#     url: Optional[str] = None
#     method: Optional[str] = None
#     headers: Optional[Dict[str, str]] = None
#     enabled: Optional[bool] = None
#
#
# class AlertStatusUpdate(BaseModel):
#     """更新告警状态请求模型"""
#     status: AlertStatus
#     comment: Optional[str] = None


# ==================== 通用响应模型 ====================

class ApiResponse(BaseModel):
    """通用API响应模型"""
    status: str
    message: Optional[str] = None
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    items: list
    total: int
    page: int
    size: int
    pages: int


# ==================== 查询参数模型 ====================

# class AlertQueryParams(BaseModel):
#     """告警查询参数"""
#     controller_id: Optional[int] = None
#     status: Optional[AlertStatus] = None
#     severity: Optional[AlertSeverity] = None
#     start_time: Optional[str] = None
#     end_time: Optional[str] = None
#     page: int = 1
#     size: int = 20


class SDNControllerQueryParams(BaseModel):
    """SDN控制器查询参数"""
    type: Optional[SDNControllerType] = None
    status: Optional[SDNControllerStatus] = None
    page: int = 1
    size: int = 20


# ==================== Neo4j图数据库相关API模型 ====================

class NodeInfo(BaseModel):
    """节点信息模型"""
    name: str
    label: str


class NodeCreate(BaseModel):
    """创建节点请求模型"""
    name: str
    label: str
    properties: Optional[Dict[str, Any]] = None


class NodeDelete(BaseModel):
    """删除节点请求模型"""
    name: str
    label: str


class NodeUpdate(BaseModel):
    """更新节点请求模型"""
    name: str
    label: str
    properties: Optional[Dict[str, Any]] = None


class RelationshipCreate(BaseModel):
    """创建关系请求模型"""
    from_node: NodeInfo
    to_node: NodeInfo
    relationship_type: str
    relationship_properties: Optional[Dict[str, Any]] = None


class RelationshipDelete(BaseModel):
    """删除关系请求模型"""
    from_node: NodeInfo
    to_node: NodeInfo
    relationship_type: str


class RelationshipDeleteById(BaseModel):
    """通过ID删除关系请求模型"""
    relationship_id: str  # Neo4j 关系的内部 ID，格式如 "5:xxxxx:10"


class RelationshipInfo(BaseModel):
    """关系信息响应模型"""
    from_node: NodeInfo
    to_node: NodeInfo
    relationship_type: str
    relationship_properties: Optional[Dict[str, Any]] = None


class RelationshipQuery(BaseModel):
    """查询关系请求模型"""
    from_node: Optional[NodeInfo] = None
    to_node: Optional[NodeInfo] = None
    relationship_type: str


class RelationshipUpdate(BaseModel):
    """更新关系请求模型"""
    from_node: NodeInfo
    to_node: NodeInfo
    relationship_type: str
    relationship_properties: Optional[Dict[str, Any]] = None


class Neo4jLabelsResponse(BaseModel):
    """Neo4j标签响应模型"""
    labels: List[str]


class Neo4jRelationshipTypesResponse(BaseModel):
    """Neo4j关系类型响应模型"""
    relationship_types: List[str]


class Neo4jNodesResponse(BaseModel):
    """Neo4j所有节点响应模型"""
    nodes: List[Dict[str, Any]]
    total: int


class Neo4jRelationshipsResponse(BaseModel):
    """Neo4j所有关系响应模型"""
    relationships: List[Dict[str, Any]]
    total: int


# ==================== Database管理相关API模型 ====================

class DatabaseCreate(BaseModel):
    """创建逻辑数据库请求模型"""
    name: str
    description: Optional[str] = None


class DatabaseInfo(BaseModel):
    """数据库信息响应模型"""
    id: int
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str


class DatabasesResponse(BaseModel):
    """数据库列表响应模型"""
    databases: List[DatabaseInfo]


# ==================== 拓扑快照相关API模型 ====================

from datetime import datetime
from pydantic import field_serializer


class TopologySnapshotCreate(BaseModel):
    """创建拓扑快照请求模型"""
    controller_id: int
    database_name: str
    snapshot_time: str  # ISO格式时间字符串
    node_count: int = 0
    link_count: int = 0
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TopologySnapshotResponse(BaseModel):
    """拓扑快照响应模型"""
    id: int
    controller_id: int
    database_name: str
    snapshot_time: datetime
    node_count: int
    link_count: int
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('snapshot_time', 'created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> Optional[str]:
        """将datetime对象序列化为ISO格式字符串"""
        return value.isoformat() if value else None
    
    class Config:
        from_attributes = True


class TopologySnapshotsResponse(BaseModel):
    """拓扑快照列表响应模型"""
    snapshots: List[TopologySnapshotResponse]
    total: int


# ==================== MCP 服务器相关 API 模型 ====================

class MCPServerCreate(BaseModel):
    """创建 MCP 服务器请求模型"""
    name: str
    url: str
    transport: str = "streamable_http"
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class MCPServerUpdate(BaseModel):
    """更新 MCP 服务器请求模型"""
    name: Optional[str] = None
    url: Optional[str] = None
    transport: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class MCPServerResponse(BaseModel):
    """MCP 服务器响应模型"""
    id: int
    name: str
    url: str
    transport: str
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> Optional[str]:
        """将datetime对象序列化为ISO格式字符串"""
        return value.isoformat() if value else None
    
    class Config:
        from_attributes = True


# ==================== 工作流节点相关 API 模型 ====================

class WorkflowNode(BaseModel):
    """工作流节点详细模型（用于next_node_detail）"""
    name: str
    label: str
    type: str  # 'function_call' 或 'final_answer'
    action: Optional[str] = None  # type=function_call 时包含
    observation: Optional[str] = None  # type=function_call 时包含
    reason: Optional[str] = None  # type=final_answer 时包含
    properties: Optional[Dict[str, Any]] = None


class WorkflowNodeSimple(BaseModel):
    """工作流节点简化模型（用于next_node）"""
    name: str
    type: str  # 'function_call' 或 'final_answer'
    action: Optional[str] = None  # type=function_call 时包含
    observation: Optional[str] = None  # type=function_call 时包含
    reason: Optional[str] = None  # type=final_answer 时包含


class WorkflowEdge(BaseModel):
    """工作流边详细模型（用于next_node_detail）"""
    from_node: str
    to_node: str
    relationship_type: str
    condition: Optional[str] = None  # Branch 类型的边可能有条件


class WorkflowEdgeSimple(BaseModel):
    """工作流边简化模型（用于next_node）"""
    from_node: str
    to_node: str
    condition: Optional[str] = None  # Branch 类型的边可能有条件


class WorkflowNextNodeResponse(BaseModel):
    """获取下一步节点详细响应模型（next_node_detail）"""
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    current_label: str  # 当前节点的label
    is_first_node: bool = False  # 是否为首节点（Event）


class WorkflowNextNodeSimpleResponse(BaseModel):
    """获取下一步节点简化响应模型（next_node）"""
    nodes: List[WorkflowNodeSimple]
    edges: List[WorkflowEdgeSimple]
    is_first_node: bool = False  # 是否为首节点（Event）