"""
图谱节点位置数据模型
"""

from sqlalchemy import Column, String, Float, DateTime, BigInteger, Identity
from sqlalchemy.sql import func
from datetime import datetime

from sqlmodel import SQLModel, Field


class GraphNodePosition(SQLModel, table=True):
    """图谱节点位置表"""

    __tablename__ = 'graph_node_positions'

    id: int = Field(sa_column=Column(BigInteger, Identity(always=True), nullable=False, primary_key=True, autoincrement=True ,comment="节点画布位置ID"))
    node_id: str = Field(sa_column=Column(String(100), nullable=False, comment='节点ID (label-name)'))
    database_name: str = Field(sa_column=Column(String(255), nullable=False, default="default", comment='所属数据库名称'))
    x: float = Field(sa_column=Column(Float, nullable=False, comment='X坐标'))
    y: float = Field(sa_column=Column(Float, nullable=False, comment='Y坐标'))
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now(), comment='创建时间'))
    updated_at: datetime = Field(sa_column=Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间'))
