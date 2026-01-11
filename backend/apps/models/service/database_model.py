"""
数据库管理数据模型
"""
from datetime import datetime
from sqlalchemy import Column, Text, BigInteger, DateTime, Identity
from sqlalchemy import Column,  String, DateTime, func
from sqlmodel import SQLModel, Field


class Database(SQLModel, table=True):
    """逻辑数据库表"""

    __tablename__ = 'databases'

    id: int = Field(
        sa_column=Column(BigInteger, Identity(always=True), nullable=False, primary_key=True, comment='数据库ID'))
    name: str = Field(
        sa_column=Column(String(255), nullable=False, unique=True, comment='数据库名称'))
    description: str = Field(
        sa_column=Column(Text, nullable=True, comment='数据库描述'))
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now(), comment='创建时间'))
    updated_at: datetime = Field(sa_column=Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间'))
