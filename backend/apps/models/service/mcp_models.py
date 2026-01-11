"""
MCP 服务器 Pydantic 模型
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, field_serializer


class MCPServer(BaseModel):
    """MCP 服务器模型"""
    id: Optional[int] = None
    name: str
    url: str
    transport: str = "streamable_http"
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
