from sqlmodel import Session, create_engine, SQLModel

from .config import settings
from ..graph_db import Neo4jHelper

# PostgreSQL engine - 全局单例
engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI),
                       pool_size=settings.PG_POOL_SIZE,
                       max_overflow=settings.PG_MAX_OVERFLOW,
                       pool_recycle=settings.PG_POOL_RECYCLE,
                       pool_pre_ping=settings.PG_POOL_PRE_PING,
                       connect_args={"options": "-c timezone=Asia/Shanghai"})

# Neo4j helper - 全局单例
# Neo4j Driver 内置连接池，全局复用可以提升性能
neo4j_helper = Neo4jHelper(neo4j_config=settings.get_graph_db_config())


def get_session():
    """获取 PostgreSQL 会话"""
    with Session(engine) as session:
        yield session


def get_graph_db_session():
    """获取 Neo4j 会话（返回全局单例）"""
    return neo4j_helper


def init_db():
    """初始化关系型数据库"""
    SQLModel.metadata.create_all(engine)


def close_graph_db():
    """关闭 Neo4j 连接（应用关闭时调用）"""
    if neo4j_helper:
        neo4j_helper.close()