"""
SDN控制器数据库模型
"""
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Integer, Text, Enum as SQLEnum, JSON, BigInteger, Identity
from sqlalchemy.sql import func
from sqlmodel import SQLModel, Field

from .sdn_models import SDNControllerType, SDNControllerStatus


class SDNControllerDBModel(SQLModel, table=True):
    """SDN控制器数据库表模型"""
    
    __tablename__ = 'sdn_controllers'
    
    id: int = Field(sa_column=Column(BigInteger, Identity(always=True), nullable=False, primary_key=True, autoincrement=True ,comment="SDN控制器ID"))
    name: str = Field(sa_column=Column(String(100), unique=True, nullable=False, index=True, comment='控制器名称'))
    type: str = Field(sa_column=Column(String(100), nullable=False, comment='控制器类型'))
    host: str = Field(sa_column=Column(String(255), nullable=False, comment='控制器主机地址'))
    port: int = Field(sa_column=Column(Integer, nullable=False, comment='控制器端口'))
    username: str = Field(sa_column=Column(String(100), nullable=True, comment='认证用户名'))
    password: str = Field(sa_column=Column(String(255), nullable=True, comment='认证密码'))
    api_token: str = Field(sa_column=Column(Text, nullable=True, comment='API令牌'))
    status: str = Field(sa_column=Column(String(100), default=SDNControllerStatus.UNKNOWN.value, nullable=False, comment='控制器状态'))
    config: str = Field(sa_column=Column(JSON, nullable=True, comment='额外配置信息'))
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now(), comment='创建时间'))
    updated_at: datetime = Field(sa_column=Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间'))
    
    def to_dict(self, include_sensitive: bool = False):
        """
        转换为字典
        
        Args:
            include_sensitive: 是否包含敏感信息(密码、令牌)
        """
        result = {
            'id': self.id,
            'name': self.name,
            'type': self.type.value if isinstance(self.type, SDNControllerType) else self.type,
            'host': self.host,
            'port': self.port,
            'status': self.status.value if isinstance(self.status, SDNControllerStatus) else self.status,
            'config': self.config,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None
        }
        
        if include_sensitive:
            result['username'] = self.username
            result['password'] = self.password
            result['api_token'] = self.api_token
        else:
            # 不包含敏感信息时，只返回用户名（如果有）
            result['username'] = self.username
        
        return result
