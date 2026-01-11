"""
拓扑快照数据库模型
"""
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Integer, JSON, ForeignKey, BigInteger, Identity
from sqlalchemy.sql import func
from sqlmodel import SQLModel, Field


class TopologySnapshotDBModel(SQLModel, table=True):
    """拓扑快照数据库表模型
    
    注意：使用 extra_metadata 而不是 metadata，
    因为 metadata 是 SQLAlchemy Declarative API 的保留字段
    """
    
    __tablename__ = 'topology_snapshots'
    
    id: int = Field(sa_column=Column(BigInteger, Identity(always=True), nullable=False, primary_key=True, autoincrement=True ,comment="拓扑快照ID"))
    controller_id: int = Field(sa_column=Column(Integer, ForeignKey('sdn_controllers.id', ondelete='CASCADE'), nullable=False, comment='SDN控制器ID'))
    database_name: str = Field(sa_column=Column(String(255), unique=True, nullable=False, index=True, comment='Neo4j数据库名称'))
    snapshot_time: datetime = Field(sa_column=Column(DateTime, nullable=False, comment='快照时间'))
    node_count: int = Field(sa_column=Column(Integer, default=0, comment='节点数量'))
    link_count: int = Field(sa_column=Column(Integer, default=0, comment='链路数量'))
    description: str = Field(sa_column=Column(String(500), nullable=True, comment='快照描述'))
    extra_metadata: dict = Field(sa_column=Column(JSON, nullable=True, comment='额外元数据'))
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now(), comment='创建时间'))
    updated_at: datetime = Field(sa_column=Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间'))
    
    # def to_dict(self):
    #     """转换为字典"""
    #     return {
    #         'id': self.id,
    #         'controller_id': self.controller_id,
    #         'database_name': self.database_name,
    #         'snapshot_time': self.snapshot_time.isoformat() if self.snapshot_time is not None else None,
    #         'node_count': self.node_count,
    #         'link_count': self.link_count,
    #         'description': self.description,
    #         'metadata': self.extra_metadata,
    #         'created_at': self.created_at.isoformat() if self.created_at is not None else None,
    #         'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None
    #     }
