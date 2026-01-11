from fastapi import HTTPException
from sqlmodel import Session
from sqlmodel import select, delete

from apps.utils.logger import TerraLogUtil
from apps.models.service.graph_position_model import GraphNodePosition


class GraphPositionService:
    async def get_all_positions(self, session: Session, database: str = 'default'):
        """
        获取所有节点位置

        Args:
            database: 数据库/画布名称

        Returns:
            节点位置字典，格式: {"node_id": {"x": 100, "y": 200}}
        """
        try:
            stmt = select(GraphNodePosition).where(GraphNodePosition.database == database)
            result = session.exec(stmt)
            db_positions = result.scalars().all()
            positions = {
                db_position.node_id: {"x": db_position.x, "y": db_position.y}
                for db_position in db_positions
            }
            return {
                pos.node_id: {"x": pos.x, "y": pos.y}
                for pos in positions
            }
        except Exception as e:
            TerraLogUtil.error(f"获取节点位置失败: {e}")
            return {}

    async def save_positions(self, session: Session, positions, database):
        """
        批量保存节点位置（使用 UPSERT 逻辑）

        Args:
            session: 数据库会话
            positions: 节点位置字典
            database: 数据库/画布名称

        Returns:
            是否保存成功
        """
        try:
            for node_id, pos in positions.items():
                # 查找现有记录
                stmt = select(GraphNodePosition).where(
                    GraphNodePosition.node_id == node_id,
                    GraphNodePosition.database_name == database
                )
                result = session.execute(stmt)
                position = result.scalar_one_or_none()
                if position:
                    # 更新现有记录
                    position.x = pos['x']
                    position.y = pos['y']
                else:
                    # 创建新记录
                    position = GraphNodePosition(
                        node_id=node_id,
                        database_name=database,
                        x=pos['x'],
                        y=pos['y']
                    )
                    session.add(position)
            session.commit()
            TerraLogUtil.info(f"成功保存 {len(positions)} 个节点位置到画布 {database}")
            return True
        except Exception as e:
            TerraLogUtil.error(f"保存节点位置失败: {e}")
            return False

    async def update_position(self, session: Session, node_id, x, y, database):
        """
        更新单个节点位置

        Args:
            session: 数据库会话
            node_id: 节点 ID
            x: X 坐标
            y: Y 坐标
            database: 数据库/画布名称

        Returns:
            是否更新成功
        """
        try:
            stmt = select(GraphNodePosition).where(
                GraphNodePosition.node_id == node_id,
                GraphNodePosition.database_name == database
            )
            result = session.execute(stmt)
            position = result.scalar_one_or_none()
            if position:
                position.x = x
                position.y = y
            else:
                # 创建新记录
                position = GraphNodePosition(
                    node_id=node_id,
                    database_name=database,
                    x=x,
                    y=y
                )
                session.add(position)
            session.commit()
            TerraLogUtil.info(f"成功更新节点 {node_id} 在画布 {database} 的位置")
            return True
        except Exception as e:
            TerraLogUtil.error(f"更新节点位置失败: {e}")
            return False

    async def delete_position(self, session, node_id, database):
        """
        删除节点位置

        Args:
            session: 数据库会话
            node_id: 节点 ID
            database: 数据库/画布名称

        Returns:
            是否删除成功
        """
        try:
            stmt = select(GraphNodePosition).where(
                GraphNodePosition.node_id == node_id,
                GraphNodePosition.database_name == database
            )
            result = session.execute(stmt)
            position = result.scalar_one_or_none()
            if position:
                session.delete(position)
                session.commit()
                TerraLogUtil.info(f"成功删除节点 {node_id} 在画布 {database} 的位置")
            else:
                TerraLogUtil.warning(f"节点 {node_id} 在画布 {database} 的位置不存在，无法删除")
                raise HTTPException(status_code=404, detail=f"节点 {node_id} 在画布 {database} 的位置不存在")

            return True
        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"删除节点位置失败: {e}")
            return False

    async def clear_all_positions(self, session, database):
        """
        清空所有节点位置

        Args:
            session: 数据库会话
            database: 数据库/画布名称

        Returns:
            是否清空成功
        """
        try:
            stmt = delete(GraphNodePosition).where(
                GraphNodePosition.database_name == database
            )
            session.execute(stmt)
            session.commit()
            TerraLogUtil.info(f"成功清空画布 {database} 的所有节点位置")
            return True
        except Exception as e:
            TerraLogUtil.error(f"清空节点位置失败: {e}")
            return False
