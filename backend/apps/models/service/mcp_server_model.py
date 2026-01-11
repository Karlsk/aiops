"""
MCP 服务器数据库模型
"""
from datetime import datetime

from sqlalchemy import Column, String, DateTime, BigInteger, Text, JSON
from sqlalchemy import Identity
from sqlalchemy.sql import func
from sqlmodel import SQLModel, Field




class MCPServerDBModel(SQLModel, table=True):
    """MCP 服务器数据库表模型"""
    
    __tablename__ = 'mcp_servers'
    
    id: int = Field(sa_column=Column(BigInteger, Identity(always=True), nullable=False, primary_key=True, autoincrement=True ,comment="MCP 服务器ID"))
    name: str = Field(sa_column=Column(String(255), nullable=False, comment='MCP服务器名称'))
    url: str = Field(sa_column=Column(Text, nullable=False, comment='MCP服务器URL'))
    transport: str = Field(sa_column=Column(String(100), default='streamable_http', nullable=False, comment='传输方式'))
    description: str = Field(sa_column=Column(Text, nullable=True, comment='服务器描述'))
    config: str = Field(sa_column=Column(JSON, nullable=True, comment='额外配置信息'))
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now(), comment='创建时间'))
    updated_at:datetime = Field(sa_column=Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间'))
    
    # def to_dict(self):
    #     """转换为字典"""
    #     return {
    #         'id': self.id,
    #         'name': self.name,
    #         'url': self.url,
    #         'transport': self.transport,
    #         'description': self.description,
    #         'config': self.config,
    #         'created_at': self.created_at.isoformat() if self.created_at is not None else None,
    #         'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None
    #     }
