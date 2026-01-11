"""
SDN控制器相关数据模型
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class SDNControllerType(str, Enum):
    """SDN控制器类型"""
    OPENDAYLIGHT = "opendaylight"
    ONOS = "onos"
    FLOODLIGHT = "floodlight"
    RYU = "ryu"
    CUSTOM = "custom"
    TERRA = "terra"


class SDNControllerStatus(str, Enum):
    """SDN控制器状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UNKNOWN = "unknown"


class SDNController(BaseModel):
    """SDN控制器配置模型"""
    id: Optional[int] = None
    name: str = Field(..., description="控制器名称")
    type: SDNControllerType = Field(..., description="控制器类型")
    host: str = Field(..., description="控制器主机地址")
    port: int = Field(..., description="控制器端口")
    username: Optional[str] = Field(None, description="认证用户名")
    password: Optional[str] = Field(None, description="认证密码")
    api_token: Optional[str] = Field(None, description="API令牌")
    status: SDNControllerStatus = Field(default=SDNControllerStatus.UNKNOWN, description="控制器状态")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外配置")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TopologyNode(BaseModel):
    """拓扑节点模型"""
    id: str = Field(..., description="节点ID")
    name: Optional[str] = Field(None, description="节点名称")
    type: str = Field(..., description="节点类型")
    controller_id: int = Field(..., description="所属控制器ID")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="节点属性")
    status: str = Field(default="unknown", description="节点状态")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TopologyLink(BaseModel):
    """拓扑链路模型"""
    id: str = Field(..., description="链路ID")
    source_node_id: str = Field(..., description="源节点ID")
    target_node_id: str = Field(..., description="目标节点ID")
    controller_id: int = Field(..., description="所属控制器ID")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="链路属性")
    status: str = Field(default="unknown", description="链路状态")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MonitoringData(BaseModel):
    """监控数据模型"""
    id: Optional[int] = None
    controller_id: int = Field(..., description="控制器ID")
    alert_id: Optional[int] = Field(None, description="关联的告警ID")
    node_id: Optional[str] = Field(None, description="节点ID")
    metric_name: str = Field(..., description="指标名称")
    metric_value: float = Field(..., description="指标值")
    unit: Optional[str] = Field(None, description="单位")
    timestamp: datetime = Field(..., description="时间戳")
    tags: Optional[Dict[str, str]] = Field(default_factory=dict, description="标签")

    class Config:
        from_attributes = True


class LogEntry(BaseModel):
    """日志条目模型"""
    id: Optional[int] = None
    controller_id: int = Field(..., description="控制器ID")
    alert_id: Optional[int] = Field(None, description="关联的告警ID")
    level: str = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息")
    source: Optional[str] = Field(None, description="日志来源")
    timestamp: datetime = Field(..., description="时间戳")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")

    class Config:
        from_attributes = True


class TopologySnapshot(BaseModel):
    """拓扑快照模型"""
    id: Optional[int] = None
    controller_id: int = Field(..., description="SDN控制器ID")
    database_name: str = Field(..., description="Neo4j数据库名称")
    snapshot_time: datetime = Field(..., description="快照时间")
    node_count: int = Field(default=0, description="节点数量")
    link_count: int = Field(default=0, description="链路数量")
    description: Optional[str] = Field(None, description="快照描述")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外元数据")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True