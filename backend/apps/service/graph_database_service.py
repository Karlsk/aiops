"""
图数据库业务服务
"""

from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from sqlmodel import select, delete, Session

from apps.graph_db.neo4j_helper import Neo4jHelper
from apps.graph_db.neo4j_mermaid_converter import Neo4jMermaidConverter
from apps.utils.logger import TerraLogUtil
from apps.models.service.database_model import Database


class GraphDatabaseService:
    """图数据库业务服务
    
    使用全局 Neo4jHelper 实例，提升性能并复用连接池
    """

    def __init__(self):
        """初始化服务，使用全局 Neo4j 实例"""
        pass

    async def get_database_info(self, graph_helper: Neo4jHelper, database: str = None) -> Dict[str, Any]:
        """获取数据库信息"""
        try:
            return graph_helper.get_database_info(database=database)
        except Exception as e:
            TerraLogUtil.error(f"Failed to get database info: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get database info: {str(e)}")

    async def get_all_labels(self, graph_helper: Neo4jHelper) -> List[str]:
        """获取所有节点标签"""
        try:
            db_info = await self.get_database_info(graph_helper)
            return db_info.get('labels', [])
        except Exception as e:
            TerraLogUtil.error(f"Failed to get node labels: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get node labels: {str(e)}")

    async def get_all_relationship_types(self, graph_helper: Neo4jHelper) -> List[str]:
        """获取所有关系类型"""
        try:
            db_info = await self.get_database_info(graph_helper)
            return db_info.get('relationship_types', [])
        except Exception as e:
            TerraLogUtil.error(f"Failed to get relationship types: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get relationship types: {str(e)}")

    async def create_node(self, graph_helper: Neo4jHelper, name: str, label: str,
                          properties: Optional[Dict[str, Any]] = None,
                          database: str = None) -> Dict[str, Any]:
        """
        创建节点，保证label和name的组合唯一
        
        Args:
            graph_helper:
            name: 节点名称
            label: 节点标签
            properties: 节点属性
            database: 数据库/画布名称
            
        Returns:
            创建的节点信息
        """
        try:
            # 输入校验
            if not name or not name.strip():
                raise HTTPException(status_code=400, detail="Node name cannot be empty")
            if not label or not label.strip():
                raise HTTPException(status_code=400, detail="Node label cannot be empty")

            name = name.strip()
            label = label.strip()
            database = database.strip() if database else None

            # 检查节点是否已存在
            if database:
                existing_nodes = graph_helper.get_node_properties(label, {"name": name},
                                                                  database=database)
            else:
                existing_nodes = graph_helper.get_node_properties(label, {"name": name})
            if existing_nodes:
                raise HTTPException(
                    status_code=409,
                    detail=f"Node with label '{label}' and name '{name}' already exists"
                )

            # 准备节点属性
            node_properties = {"name": name}
            if properties:
                node_properties.update(properties)

            # 创建节点
            result = graph_helper.merge_node(label, node_properties, database=database)

            if not result:
                raise HTTPException(status_code=500, detail="Failed to create node")

            return {
                "status": "success",
                "message": f"Node '{name}' with label '{label}' created successfully",
                "data": result
            }

        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"Failed to create node: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create node: {str(e)}")

    async def delete_node(self, graph_helper: Neo4jHelper, name: str, label: str, database: str = None) -> Dict[
        str, Any]:
        """
        删除节点

        Args:
            graph_helper:
            name: 节点名称
            label: 节点标签
            database: 逻辑数据库名称/画布名称
        Returns:
            删除结果
        """
        try:
            # 输入校验
            if not name or not name.strip():
                raise HTTPException(status_code=400, detail="Node name cannot be empty")
            if not label or not label.strip():
                raise HTTPException(status_code=400, detail="Node label cannot be empty")

            name = name.strip()
            label = label.strip()
            database = database.strip() if database else None

            # 检查节点是否已存在
            if database:
                existing_nodes = graph_helper.get_node_properties(label, {"name": name},
                                                                  database=database)
            else:
                existing_nodes = graph_helper.get_node_properties(label, {"name": name})

            if not existing_nodes:
                raise HTTPException(
                    status_code=404,
                    detail=f"Node with label '{label}' and name '{name}' not found"
                )

            # 删除节点
            deleted_count = graph_helper.delete_node(label, {"name": name}, database=database)

            if deleted_count == 0:
                raise HTTPException(status_code=500, detail="Failed to delete node")

            return {
                "status": "success",
                "message": f"Node '{name}' with label '{label}' deleted successfully",
                "data": {"deleted_count": deleted_count}
            }

        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"Failed to delete node: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete node: {str(e)}")

    async def update_node(self, graph_helper: Neo4jHelper, name: str, label: str,
                          properties: Optional[Dict[str, Any]] = None,
                          database: str = None) -> Dict[str, Any]:
        """
        更新节点属性

        Args:
            name: 节点名称
            label: 节点标签
            properties: 要更新的属性
            database: 逻辑数据库名称

        Returns:
            更新后的节点信息
        """
        try:
            # 输入校验
            if not name or not name.strip():
                raise HTTPException(status_code=400, detail="Node name cannot be empty")
            if not label or not label.strip():
                raise HTTPException(status_code=400, detail="Node label cannot be empty")
            if not properties:
                raise HTTPException(status_code=400, detail="Properties cannot be empty")

            name = name.strip()
            label = label.strip()
            database = database.strip() if database else None

            # 检查节点是否已存在
            if database:
                existing_nodes = graph_helper.get_node_properties(label, {"name": name},
                                                                  database=database)
            else:
                existing_nodes = graph_helper.get_node_properties(label, {"name": name})

            if not existing_nodes:
                raise HTTPException(
                    status_code=404,
                    detail=f"Node with label '{label}' and name '{name}' not found"
                )

            # 更新节点属性
            result = graph_helper.update_node_properties(
                label, {"name": name}, properties, database=database
            )

            if not result:
                raise HTTPException(status_code=500, detail="Failed to update node")

            return {
                "status": "success",
                "message": f"Node '{name}' with label '{label}' updated successfully",
                "data": result[0] if result else {}
            }

        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"Failed to update node: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update node: {str(e)}")

    async def create_relationship(
            self,
            graph_helper: Neo4jHelper,
            from_node_name: str,
            from_node_label: str,
            to_node_name: str,
            to_node_label: str,
            relationship_type: str,
            relationship_properties: Optional[Dict[str, Any]] = None,
            database: str = None
    ) -> Dict[str, Any]:
        """
        创建关系

        Args:
            from_node_name: 起始节点名称
            from_node_label: 起始节点标签
            to_node_name: 目标节点名称
            to_node_label: 目标节点标签
            relationship_type: 关系类型
            relationship_properties: 关系属性

        Returns:
            创建的关系信息
        """
        try:
            # 输入校验
            if not from_node_name or not from_node_name.strip():
                raise HTTPException(status_code=400, detail="From node name cannot be empty")
            if not from_node_label or not from_node_label.strip():
                raise HTTPException(status_code=400, detail="From node label cannot be empty")
            if not to_node_name or not to_node_name.strip():
                raise HTTPException(status_code=400, detail="To node name cannot be empty")
            if not to_node_label or not to_node_label.strip():
                raise HTTPException(status_code=400, detail="To node label cannot be empty")
            if not relationship_type or not relationship_type.strip():
                raise HTTPException(status_code=400, detail="Relationship type cannot be empty")

            from_node_name = from_node_name.strip()
            from_node_label = from_node_label.strip()
            to_node_name = to_node_name.strip()
            to_node_label = to_node_label.strip()
            relationship_type = relationship_type.strip()

            # 检查起始节点是否存在
            from_nodes = graph_helper.get_node_properties(from_node_label, {"name": from_node_name})
            if not from_nodes:
                raise HTTPException(
                    status_code=404,
                    detail=f"From node with label '{from_node_label}' and name '{from_node_name}' not found"
                )

            # 检查目标节点是否存在
            to_nodes = graph_helper.get_node_properties(to_node_label, {"name": to_node_name})
            if not to_nodes:
                raise HTTPException(
                    status_code=404,
                    detail=f"To node with label '{to_node_label}' and name '{to_node_name}' not found"
                )

            # # 验证关系属性
            # if relationship_properties:
            #     for key, value in relationship_properties.items():
            #         if not isinstance(value, str):
            #             raise HTTPException(
            #                 status_code=400,
            #                 detail=f"Relationship property '{key}' value must be a string"
            #             )

            # 创建关系
            result = graph_helper.create_relationship(
                from_node_label, {"name": from_node_name},
                to_node_label, {"name": to_node_name},
                relationship_type, relationship_properties or {}, database=database
            )

            # result为None才表示失败，空字典{}表示成功但没有返回数据
            if result is None:
                raise HTTPException(status_code=500, detail="Failed to create relationship")

            return {
                "status": "success",
                "message": f"Relationship '{relationship_type}' created successfully between nodes",
                "data": result
            }

        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"Failed to create relationship: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create relationship: {str(e)}")

    async def delete_relationship(self,
                                  graph_helper: Neo4jHelper,
                                  from_node_name: str,
                                  from_node_label: str,
                                  to_node_name: str,
                                  to_node_label: str,
                                  relationship_type: str,
                                  database: str = None
                                  ) -> Dict[str, Any]:
        """
        删除关系

        Args:
            from_node_name: 起始节点名称
            from_node_label: 起始节点标签
            to_node_name: 目标节点名称
            to_node_label: 目标节点标签
            relationship_type: 关系类型

        Returns:
            删除结果
        """
        try:
            # 输入校验
            if not from_node_name or not from_node_name.strip():
                raise HTTPException(status_code=400, detail="From node name cannot be empty")
            if not from_node_label or not from_node_label.strip():
                raise HTTPException(status_code=400, detail="From node label cannot be empty")
            if not to_node_name or not to_node_name.strip():
                raise HTTPException(status_code=400, detail="To node name cannot be empty")
            if not to_node_label or not to_node_label.strip():
                raise HTTPException(status_code=400, detail="To node label cannot be empty")
            if not relationship_type or not relationship_type.strip():
                raise HTTPException(status_code=400, detail="Relationship type cannot be empty")

            from_node_name = from_node_name.strip()
            from_node_label = from_node_label.strip()
            to_node_name = to_node_name.strip()
            to_node_label = to_node_label.strip()
            relationship_type = relationship_type.strip()

            # 检查关系是否存在
            existing_relationships = graph_helper.get_relationship_properties(
                relationship_type,
                from_node_label, {"name": from_node_name},
                to_node_label, {"name": to_node_name}
            )

            if not existing_relationships:
                raise HTTPException(
                    status_code=404,
                    detail=f"Relationship '{relationship_type}' between specified nodes not found"
                )

            # 删除关系
            deleted_count = graph_helper.delete_relationship(
                from_node_label, {"name": from_node_name},
                to_node_label, {"name": to_node_name},
                relationship_type, database=database
            )

            if deleted_count == 0:
                raise HTTPException(status_code=500, detail="Failed to delete relationship")

            return {
                "status": "success",
                "message": f"Relationship '{relationship_type}' deleted successfully",
                "data": {"deleted_count": deleted_count}
            }

        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"Failed to delete relationship: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete relationship: {str(e)}")

    async def update_relationship(self,
                                  graph_helper: Neo4jHelper,
                                  from_node_name: str,
                                  from_node_label: str,
                                  to_node_name: str,
                                  to_node_label: str,
                                  relationship_type: str,
                                  relationship_properties: Optional[Dict[str, Any]] = None,
                                  database: str = None
                                  ) -> Dict[str, Any]:
        """
        更新关系属性

        Args:
            from_node_name: 起始节点名称
            from_node_label: 起始节点标签
            to_node_name: 目标节点名称
            to_node_label: 目标节点标签
            relationship_type: 关系类型
            relationship_properties: 要更新的关系属性
            database: 逻辑数据库名称

        Returns:
            更新后的关系信息
        """
        try:
            # 输入校验
            if not from_node_name or not from_node_name.strip():
                raise HTTPException(status_code=400, detail="From node name cannot be empty")
            if not from_node_label or not from_node_label.strip():
                raise HTTPException(status_code=400, detail="From node label cannot be empty")
            if not to_node_name or not to_node_name.strip():
                raise HTTPException(status_code=400, detail="To node name cannot be empty")
            if not to_node_label or not to_node_label.strip():
                raise HTTPException(status_code=400, detail="To node label cannot be empty")
            if not relationship_type or not relationship_type.strip():
                raise HTTPException(status_code=400, detail="Relationship type cannot be empty")
            if not relationship_properties:
                raise HTTPException(status_code=400, detail="Properties cannot be empty")

            from_node_name = from_node_name.strip()
            from_node_label = from_node_label.strip()
            to_node_name = to_node_name.strip()
            to_node_label = to_node_label.strip()
            relationship_type = relationship_type.strip()
            database = database.strip() if database else None

            # 检查关系是否存在
            existing_relationships = graph_helper.get_relationship_properties(
                relationship_type,
                from_node_label, {"name": from_node_name},
                to_node_label, {"name": to_node_name},
                database=database
            )

            if not existing_relationships:
                raise HTTPException(
                    status_code=404,
                    detail=f"Relationship '{relationship_type}' between specified nodes not found"
                )

            # 更新关系属性
            result = graph_helper.update_relationship_properties(
                from_node_label, {"name": from_node_name},
                to_node_label, {"name": to_node_name},
                relationship_type, relationship_properties, database=database
            )

            if not result:
                raise HTTPException(status_code=500, detail="Failed to update relationship")

            return {
                "status": "success",
                "message": f"Relationship '{relationship_type}' updated successfully",
                "data": result[0] if result else {}
            }

        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"Failed to update relationship: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update relationship: {str(e)}")

    async def delete_relationship_by_id(
            self,
            graph_helper: Neo4jHelper,
            relationship_id: str
    ) -> Dict[str, Any]:
        """
        通过关系ID删除关系（精确删除单条关系）

        Args:
            relationship_id: Neo4j 关系的内部 ID（格式："5:xxxxx:10"）

        Returns:
            删除结果
        """
        try:
            # 输入校验
            if not relationship_id or not relationship_id.strip():
                raise HTTPException(status_code=400, detail="Relationship ID cannot be empty")

            relationship_id = relationship_id.strip()

            # 删除关系
            deleted_count = graph_helper.delete_relationship_by_id(relationship_id)

            if deleted_count == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Relationship with ID '{relationship_id}' not found"
                )

            return {
                "status": "success",
                "message": f"Relationship with ID '{relationship_id}' deleted successfully",
                "data": {"deleted_count": deleted_count}
            }

        except HTTPException:
            raise
        except ValueError as e:
            # 处理ID格式错误
            TerraLogUtil.error(f"Invalid relationship ID format: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            TerraLogUtil.error(f"Failed to delete relationship by ID: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete relationship by ID: {str(e)}")

    async def get_all_nodes(self, graph_helper: Neo4jHelper, label: Optional[str] = None, limit: int = 100,
                            database: str = None) -> Dict[
        str, Any]:
        """
        获取所有节点

        Args:
            label: 节点标签过滤（可选）
            limit: 限制返回数量

        Returns:
            节点列表，格式为List[NodeCreate]
        """
        try:
            # 获取节点列表
            nodes_raw = graph_helper.get_all_nodes(label=label, limit=limit, database=database)

            # 转换为NodeCreate格式
            nodes = []
            for node_data in nodes_raw:
                # node_data是一个字典，包含'n'（节点属性）和'node_labels'（节点标签列表）
                if 'n' in node_data and 'node_labels' in node_data:
                    node_props = node_data['n']
                    node_labels = node_data['node_labels']

                    # 提取name
                    name = node_props.get('name', '')

                    # 获取第一个label作为主label（如果有多个label）
                    node_label = node_labels[0] if node_labels else 'Unknown'

                    # 过滤掉name字段，剩余的作为properties
                    properties = {k: v for k, v in node_props.items() if k != 'name'}

                    nodes.append({
                        'name': name,
                        'label': node_label,
                        'properties': properties if properties else None
                    })

            return {
                "status": "success",
                "message": "Nodes retrieved successfully",
                "data": nodes
            }

        except Exception as e:
            TerraLogUtil.error(f"Failed to get all nodes: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get all nodes: {str(e)}")

    async def get_all_relationships(
            self,
            graph_helper: Neo4jHelper,
            relationship_type: Optional[str] = None,
            from_label: Optional[str] = None,
            to_label: Optional[str] = None,
            limit: int = 100,
            database: str = None
    ) -> Dict[str, Any]:
        """
        获取所有关系

        Args:
            relationship_type: 关系类型过滤（可选）
            from_label: 起始节点标签过滤（可选）
            to_label: 目标节点标签过滤（可选）
            limit: 限制返回数量

        Returns:
            关系列表，格式为List[RelationshipInfo]
        """
        try:
            # 获取关系列表
            relationships_raw = graph_helper.get_relationship_properties(
                relationship_type=relationship_type,
                from_label=from_label,
                to_label=to_label,
                limit=limit,
                database=database
            )

            # 转换为RelationshipInfo格式
            relationships = []
            for rel_data in relationships_raw:
                # rel_data包含: 'a', 'from_labels', 'r', 'rel_type', 'b', 'to_labels'
                if 'from_node' in rel_data and 'relationship' in rel_data and 'to_node' in rel_data:
                    TerraLogUtil.info(f"Relationship data: {rel_data}")
                    # 提取节点属性和关系属性
                    from_node_props = rel_data['from_node']
                    to_node_props = rel_data['to_node']
                    rel_props = rel_data['relationship']
                    from_labels = from_node_props.get('labels', [])
                    to_labels = to_node_props.get('labels', [])
                    rel_type = rel_props.get('_type', '')

                    # 提取节点名称和标签
                    from_name = from_node_props.get('name', '')
                    to_name = to_node_props.get('name', '')
                    from_label_str = from_labels[0] if from_labels else 'Unknown'
                    to_label_str = to_labels[0] if to_labels else 'Unknown'

                    # 构建关系信息
                    relationships.append({
                        'from_node': {
                            'name': from_name,
                            'label': from_label_str
                        },
                        'to_node': {
                            'name': to_name,
                            'label': to_label_str
                        },
                        'relationship_type': rel_type,
                        'relationship_properties': rel_props if rel_props else None
                    })

            return {
                "status": "success",
                "message": "Relationships retrieved successfully",
                "data": relationships
            }

        except Exception as e:
            TerraLogUtil.error(f"Failed to get all relationships: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get all relationships: {str(e)}")

    async def get_node_by_label_and_name(self, graph_helper: Neo4jHelper, label: str, name: str,
                                         database: str = None) -> Dict[str, Any]:
        """
        通过label和name获取单个节点

        Args:
            label: 节点标签
            name: 节点名称

        Returns:
            节点信息，格式为NodeCreate
        """
        try:
            # 输入校验
            if not name or not name.strip():
                raise HTTPException(status_code=400, detail="Node name cannot be empty")
            if not label or not label.strip():
                raise HTTPException(status_code=400, detail="Node label cannot be empty")

            name = name.strip()
            label = label.strip()

            # 查询节点
            nodes = graph_helper.get_node_properties(label, {"name": name}, database=database)

            if not nodes:
                raise HTTPException(
                    status_code=404,
                    detail=f"Node with label '{label}' and name '{name}' not found"
                )

            # 转换为NodeCreate格式
            node_data = nodes[0]['n']
            node_name = node_data.get('name', '')
            properties = {k: v for k, v in node_data.items() if k != 'name'}

            node_info = {
                'name': node_name,
                'label': label,
                'properties': properties if properties else None
            }

            return {
                "status": "success",
                "message": f"Node '{name}' with label '{label}' retrieved successfully",
                "data": node_info
            }

        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"Failed to get node by label and name: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get node by label and name: {str(e)}")

    async def get_relationships_by_query(
            self,
            graph_helper: Neo4jHelper,
            relationship_type: str,
            from_node_label: Optional[str] = None,
            from_node_name: Optional[str] = None,
            to_node_label: Optional[str] = None,
            to_node_name: Optional[str] = None,
            limit: int = 100,
            database: str = None
    ) -> Dict[str, Any]:
        """
        通过from_node、to_node和type获取相关的relationship

        Args:
            relationship_type: 关系类型（必填）
            from_node_label: 起始节点标签（选填）
            from_node_name: 起始节点名称（选填）
            to_node_label: 目标节点标签（选填）
            to_node_name: 目标节点名称（选填）
            limit: 限制返回数量

        Returns:
            关系列表，格式为List[RelationshipInfo]
        """
        try:
            # 输入校验
            if not relationship_type or not relationship_type.strip():
                raise HTTPException(status_code=400, detail="Relationship type cannot be empty")

            relationship_type = relationship_type.strip()

            # 构建查询参数
            from_properties = None
            to_properties = None

            if from_node_name and from_node_name.strip():
                from_properties = {"name": from_node_name.strip()}

            if to_node_name and to_node_name.strip():
                to_properties = {"name": to_node_name.strip()}

            # 使用get_relationship_properties方法查询
            relationships_raw = graph_helper.get_relationship_properties(
                relationship_type=relationship_type,
                from_label=from_node_label,
                from_properties=from_properties,
                to_label=to_node_label,
                to_properties=to_properties,
                limit=limit,
                database=database
            )

            # 转换为RelationshipInfo格式
            relationships = []
            for rel_data in relationships_raw:
                # rel_data格式: {'from_node': {...}, 'relationship': {...}, 'to_node': {...}}
                if 'from_node' in rel_data and 'to_node' in rel_data and 'relationship' in rel_data:
                    from_node_props = rel_data['from_node']
                    to_node_props = rel_data['to_node']
                    rel_props = rel_data['relationship']

                    # 提取节点名称，需要从标签中推断（这里简化处理）
                    from_name = from_node_props.get('name', '')
                    to_name = to_node_props.get('name', '')

                    # 清理关系属性，移除内部字段
                    clean_rel_props = {k: v for k, v in rel_props.items() if not k.startswith('_')}

                    relationships.append({
                        'from_node': {
                            'name': from_name,
                            'label': from_node_label if from_node_label else 'Unknown'
                        },
                        'to_node': {
                            'name': to_name,
                            'label': to_node_label if to_node_label else 'Unknown'
                        },
                        'relationship_type': relationship_type,
                        'relationship_properties': clean_rel_props if clean_rel_props else None
                    })

            return {
                "status": "success",
                "message": "Relationships retrieved successfully",
                "data": relationships
            }

        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"Failed to get relationships by query: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get relationships by query: {str(e)}")

    async def convert_neo4j_to_mermaid(self, graph_helper: Neo4jHelper, name: str, database: str = None) -> Dict[
        str, Any]:
        """
        将Neo4j图数据转换为Mermaid流程图格式

        Args:
            name: 事件名称，用于查询路径的起始节点

        Returns:
            Mermaid流程图字符串
        """
        try:
            # 输入校验
            if not name or not name.strip():
                raise HTTPException(status_code=400, detail="Name cannot be empty")

            name = name.strip()

            # 检查名称对应的节点是否存在且包含Event标签
            if not database or not database.strip():
                event_nodes = graph_helper.get_node_properties("Event", {"name": name})
            else:
                database = database.strip()
                event_nodes = graph_helper.get_node_properties("Event", {"name": name}, database)
            if not event_nodes:
                raise HTTPException(
                    status_code=400,
                    detail=f"No node with label 'Event' and name '{name}' found"
                )

            # 创建转换器
            converter = Neo4jMermaidConverter(graph_helper)

            # 查询路径（传递database参数进行过滤）
            paths = converter.query_paths(name, database)

            if not paths:
                raise HTTPException(
                    status_code=404,
                    detail=f"No paths found for event name '{name}'"
                )

            # 构建图
            graph = converter.build_graph(paths)

            # 转换为Mermaid格式
            mermaid_output = converter.to_mermaid()

            return {
                "status": "success",
                "message": f"Successfully converted Neo4j graph to Mermaid format for event '{name}'",
                "data": {
                    "mermaid": mermaid_output,
                    "stats": {
                        "paths_count": len(paths),
                        "nodes_count": graph.number_of_nodes(),
                        "edges_count": graph.number_of_edges()
                    }
                }
            }

        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"Failed to convert Neo4j to Mermaid: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to convert Neo4j to Mermaid: {str(e)}")

    async def convert_neo4j_to_json(self, graph_helper: Neo4jHelper, name: str, database: str = None) -> Dict[str, Any]:
        """
        将Neo4j图数据转换为JSON格式（结构化Plan Schema）

        Args:
            name: 事件名称，用于查询路径的起始节点

        Returns:
            JSON格式的结构化Plan Schema
        """
        try:
            # 输入校验
            if not name or not name.strip():
                raise HTTPException(status_code=400, detail="Name cannot be empty")

            name = name.strip()

            # 检查名称对应的节点是否存在且包含Event标签
            if not database or not database.strip():
                event_nodes = graph_helper.get_node_properties("Event", {"name": name})
            else:
                database = database.strip()
                event_nodes = graph_helper.get_node_properties("Event", {"name": name}, database)
            if not event_nodes:
                raise HTTPException(
                    status_code=400,
                    detail=f"No node with label 'Event' and name '{name}' found"
                )

            # 创建转换器
            converter = Neo4jMermaidConverter(graph_helper)

            # 查询路径（传递database参数进行过滤）
            paths = converter.query_paths(name, database)

            if not paths:
                raise HTTPException(
                    status_code=404,
                    detail=f"No paths found for event name '{name}'"
                )

            # 构建图
            graph = converter.build_graph(paths)

            # 转换为JSON格式
            json_output = self._convert_graph_to_json(name, graph, converter.edge_info)

            return {
                "status": "success",
                "message": f"Successfully converted Neo4j graph to JSON format for event '{name}'",
                "data": json_output
            }

        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"Failed to convert Neo4j to JSON: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to convert Neo4j to JSON: {str(e)}")

    def _convert_graph_to_json(self, plan_id: str, graph, edge_info: Dict) -> Dict[str, Any]:
        """
        将networkx图转换为JSON格式的结构化Plan Schema

        Args:
            plan_id: 计划ID
            graph: networkx DiGraph对象
            edge_info: 边的额外信息（关系类型和条件）

        Returns:
            JSON格式的结构化Plan Schema
        """
        nodes = {}
        edges = []
        start_node = None

        # 处理图中的节点
        for node, data in graph.nodes(data=True):
            node_id = node

            # 确定节点类型
            if "Action" in data:
                node_type = "function_call"
                action = data.get('Action', '')
                description = data.get('name', '')
                outputs = data.get('Observation', '')
                if outputs:
                    outputs = [outputs] if isinstance(outputs, str) else [outputs]
                else:
                    outputs = []

                nodes[node_id] = {
                    "type": node_type,
                    "action": action,
                    "description": description,
                    "outputs": outputs
                }

                # 第一个节点作为start节点
                if start_node is None:
                    start_node = node_id

            elif "FinalAnswer" in data:
                node_type = "final_answer"
                reason = data.get('FinalAnswer', '')

                nodes[node_id] = {
                    "type": node_type,
                    "reason": reason if reason else None
                }
                # 清理只有type和None reason的节点
                if not reason:
                    nodes[node_id] = {
                        "type": node_type
                    }

        # 处理图中的边
        for src, dst in graph.edges():
            edge_key = (src, dst)
            edge_data = edge_info.get(edge_key, {})
            condition = edge_data.get('condition')

            edge_obj = {
                "from": src,
                "to": dst
            }

            # 只有当condition存在时才添加
            if condition:
                edge_obj["condition"] = condition

            edges.append(edge_obj)

        # 如果还没有设置start节点，使用第一个节点
        if start_node is None and nodes:
            # 查找入度为0的节点（没有入边的节点）
            for node in graph.nodes():
                if graph.in_degree(node) == 0:
                    start_node = node
                    break
            # 如果没有找到，使用第一个节点
            if start_node is None:
                start_node = list(nodes.keys())[0]

        return {
            "id": f"plan_{plan_id}",
            "nodes": nodes,
            "edges": edges,
            "start": start_node,
            "stats": {
                "nodes_count": len(nodes),
                "edges_count": len(edges)
            }
        }

    # ==================== Database 管理方法 ====================

    async def create_database(self, session: Session, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        创建逻辑数据库

        Args:
            name: 数据库名称
            description: 数据库描述

        Returns:
            创建结果
        """
        try:
            # 输入校验
            if not name or not name.strip():
                raise HTTPException(status_code=400, detail="Database name cannot be empty")

            name = name.strip()

            # 检查数据库名称是否已存在
            stmt = select(Database).where(Database.name == name)
            result = session.execute(stmt)
            existing_db = result.scalar_one_or_none()

            if existing_db:
                raise HTTPException(
                    status_code=409,
                    detail=f"Database '{name}' already exists"
                )
            TerraLogUtil.info(f"Creating new database record: {name}")
            # 创建数据库记录
            new_db = Database(
                name=name,
                description=description
            )
            session.add(new_db)
            session.commit()
            session.refresh(new_db)

            return {
                "status": "success",
                "message": f"Database '{name}' created successfully",
                "data": new_db.model_dump()
            }

        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"Failed to create database: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create database: {str(e)}")

    async def delete_database(self, session: Session, graph_helper: Neo4jHelper, name: str) -> Dict[str, Any]:
        """
        删除逻辑数据库

        Args:
            name: 数据库名称

        Returns:
            删除结果
        """
        try:
            # 输入校验
            if not name or not name.strip():
                raise HTTPException(status_code=400, detail="Database name cannot be empty")

            name = name.strip()

            # 检查数据库是否存在
            stmt = select(Database).where(Database.name == name)
            result = session.execute(stmt)
            db_record = result.scalar_one_or_none()

            if not db_record:
                raise HTTPException(
                    status_code=404,
                    detail=f"Database '{name}' not found"
                )

            # 检查 Neo4j 中是否还有该 database 的节点
            nodes_with_db = graph_helper.get_all_nodes(limit=1, database=name)
            if nodes_with_db:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot delete database '{name}': nodes still exist in Neo4j"
                )

            # 删除数据库记录
            session.delete(db_record)
            session.commit()

            return {
                "status": "success",
                "message": f"Database '{name}' deleted successfully",
                "data": {"deleted_name": name}
            }

        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"Failed to delete database: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete database: {str(e)}")

    async def get_databases(self, session: Session) -> Dict[str, Any]:
        """
        获取所有逻辑数据库

        Returns:
            数据库列表
        """
        try:
            stmt = select(Database).order_by(Database.created_at.desc())
            result = session.execute(stmt)
            databases = result.scalars().all()

            db_list = [db.model_dump() for db in databases]

            return {
                "status": "success",
                "message": "Databases retrieved successfully",
                "data": db_list
            }

        except Exception as e:
            TerraLogUtil.error(f"Failed to get databases: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get databases: {str(e)}")

    async def delete_topology_to_database(self, graph_helper: Neo4jHelper, ndatabase_name):
        try:
            graph_helper.delete_all_nodes(database=ndatabase_name)
            graph_helper.delete_all_relationships(database=ndatabase_name)
            return {
                "status": "success",
                "message": f"Topology deleted from database '{ndatabase_name}' successfully"
            }
        except Exception as e:
            TerraLogUtil.error(f"Failed to delete topology from database: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete topology from database: {str(e)}")

    async def get_workflow_next_node(self, graph_helper: Neo4jHelper, current_name: str, database: str = None,
                                     include_details: bool = True) -> \
            Dict[str, Any]:
        """
        获取当前节点的下一步信息

        Args:
            current_name: 当前节点的name
            database: 逻辑数据库名称

        Returns:
            包含nodes和edges的响应
        """
        try:
            # 输入校验
            if not current_name or not current_name.strip():
                raise HTTPException(status_code=400, detail="Current node name cannot be empty")

            current_name = current_name.strip()
            database = database.strip() if database else None

            # 步骤1: 查找当前节点及其标签
            current_node_query = "MATCH (n) WHERE n.name = $name"
            params = {"name": current_name}

            if database:
                current_node_query += " AND n.database = $database"
                params["database"] = database

            current_node_query += " RETURN n, labels(n) as node_labels"

            current_nodes = graph_helper.execute_query(current_node_query, params)

            if not current_nodes:
                raise HTTPException(
                    status_code=404,
                    detail=f"Node with name '{current_name}' not found"
                )

            current_node_data = current_nodes[0]['n']
            current_labels = current_nodes[0]['node_labels']
            current_label = current_labels[0] if current_labels else 'Unknown'

            # 判断是否为首节点（Event标签）
            is_first_node = current_label == "Event"

            nodes = []
            edges = []

            if is_first_node:
                # 情况1: 当前是Event节点，返回下一个节点，无edges，标记为首节点
                next_query = "MATCH (current {name: $name})-[r]->(next)"
                params = {"name": current_name}

                if database:
                    next_query += " WHERE current.database = $database AND next.database = $database AND r.database = $database"
                    params["database"] = database

                next_query += " RETURN next, labels(next) as next_labels, r, type(r) as rel_type"

                next_nodes = graph_helper.execute_query(next_query, params)

                if next_nodes:
                    for next_item in next_nodes:
                        next_node_data = next_item['next']
                        next_labels = next_item['next_labels']
                        next_label = next_labels[0] if next_labels else 'Unknown'

                        node_type = self._determine_node_type(next_label)
                        node_obj = self._build_node_object(next_node_data, next_label, node_type, include_details)
                        nodes.append(node_obj)

                return {
                    "status": "success",
                    "message": f"Next node information retrieved for Event node '{current_name}'",
                    "data": self._build_response_data(nodes, [], current_label, True, include_details)
                }

            # 情况2和3: 非Event节点，需要查询关系类型
            edges_query = "MATCH (current {name: $name})-[r]->(next)"
            params = {"name": current_name}

            if database:
                edges_query += " WHERE current.database = $database AND next.database = $database AND r.database = $database"
                params["database"] = database

            edges_query += " RETURN current, r, type(r) as rel_type, next, labels(next) as next_labels, properties(r) as rel_props"

            edges_data = graph_helper.execute_query(edges_query, params)

            # 添加当前节点到返回列表
            current_node_type = self._determine_node_type(current_label)
            current_node_obj = self._build_node_object(current_node_data, current_label, current_node_type,
                                                       include_details)
            nodes.append(current_node_obj)

            if not edges_data:
                # 当前节点无出边，返回只有当前节点，无edges
                return {
                    "status": "success",
                    "message": f"Node '{current_name}' has no outgoing edges",
                    "data": self._build_response_data(nodes, [], current_label, False, include_details)
                }

            # 根据关系类型判断是Sequence还是Branch
            rel_type = edges_data[0].get('rel_type', '')

            if rel_type == "Sequence":
                # 情况2: Sequence类型，返回当前节点和下一个节点，edges返回from/to[/relationship_type]
                for edge_item in edges_data:
                    next_node_data = edge_item['next']
                    next_labels = edge_item['next_labels']
                    next_label = next_labels[0] if next_labels else 'Unknown'

                    next_node_type = self._determine_node_type(next_label)
                    next_node_obj = self._build_node_object(next_node_data, next_label, next_node_type, include_details)
                    nodes.append(next_node_obj)

                    # 添加edge
                    edge_obj = {
                        "from_node": current_name,
                        "to_node": next_node_data.get('name'),
                        "condition": None
                    }
                    if include_details:
                        edge_obj["relationship_type"] = rel_type
                    edges.append(edge_obj)

            elif rel_type == "Branch":
                # 情况3: Branch类型，返回当前节点和多个节点，edges返回from/to[/relationship_type]/condition
                for edge_item in edges_data:
                    next_node_data = edge_item['next']
                    next_labels = edge_item['next_labels']
                    next_label = next_labels[0] if next_labels else 'Unknown'

                    next_node_type = self._determine_node_type(next_label)
                    next_node_obj = self._build_node_object(next_node_data, next_label, next_node_type, include_details)
                    nodes.append(next_node_obj)

                    # 获取条件（从关系属性中）
                    rel_props = edge_item.get('rel_props', {})
                    condition = rel_props.get('Condition') if isinstance(rel_props, dict) else None

                    # 添加edge
                    edge_obj = {
                        "from_node": current_name,
                        "to_node": next_node_data.get('name'),
                        "condition": condition
                    }
                    if include_details:
                        edge_obj["relationship_type"] = rel_type
                    edges.append(edge_obj)

            return {
                "status": "success",
                "message": f"Next node information retrieved for node '{current_name}' with relationship type '{rel_type}'",
                "data": self._build_response_data(nodes, edges, current_label, False, include_details)
            }

        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"Failed to get workflow next node: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get workflow next node: {str(e)}")

    def _determine_node_type(self, label: str) -> str:
        """
        根据节点标签确定节点类型

        Args:
            label: 节点标签

        Returns:
            'function_call' 或 'final_answer'
        """
        if label == "Step":
            return "function_call"
        elif label == "Output":
            return "final_answer"
        else:
            return "function_call"  # 默认

    def _build_node_object(self, node_data: Dict[str, Any], label: str, node_type: str, include_details: bool = True) -> \
            Dict[str, Any]:
        """
        构建节点对象

        Args:
            node_data: 节点数据
            label: 节点标签
            node_type: 节点类型
            include_details: 是否包含details

        Returns:
            节点对象
        """
        node_obj = {
            "name": node_data.get('name', ''),
            "type": node_type
        }

        # 仅当include_details=True时添加label和properties
        if include_details:
            node_obj["label"] = label

        if node_type == "function_call":
            node_obj["action"] = node_data.get('Action')
            node_obj["observation"] = node_data.get('Observation')
        elif node_type == "final_answer":
            node_obj["reason"] = node_data.get('FinalAnswer')

        # 仅当include_details=True时添加其他属性
        if include_details:
            exclude_keys = {'name', 'Action', 'Observation', 'FinalAnswer', 'database'}
            properties = {k: v for k, v in node_data.items() if k not in exclude_keys}
            if properties:
                node_obj["properties"] = properties

        return node_obj

    def _build_response_data(self, nodes: List, edges: List, current_label: str, is_first_node: bool,
                             include_details: bool) -> Dict[str, Any]:
        """
        构建响应数据

        Args:
            nodes: 节点列表
            edges: 边列表
            current_label: 当前节点标签
            is_first_node: 是否是首节点
            include_details: 是否包含details

        Returns:
            响应数据字典
        """
        response_data = {
            "nodes": nodes,
            "edges": edges,
            "is_first_node": is_first_node
        }

        # 仅当include_details=True时添加current_label
        if include_details:
            response_data["current_label"] = current_label

        return response_data

    async def save_topology_to_database(self, session: Session, graph_helper: Neo4jHelper, database_name, nodes, links):
        try:
            # 保存节点
            for node in nodes:
                label = "Router"
                name = node.get("device_name")
                properties = {
                    "device_name_alias": node.get("device_name_alias", ""),
                    "management_ip": node.get("management_ip", ""),
                    "node_type": node.get("node_type", ""),
                    "vendor": node.get("vendor", ""),
                    "series": node.get("series", "")
                }
                await self.create_node(graph_helper, name, label, properties, database=database_name)

            # 保存关系
            for link in links:
                source_ip = link.get("source_ip", "")
                dest_ip = link.get("dest_ip", "")
                source_port = link.get("source_tp", "")
                dest_port = link.get("dest_tp", "")
                link_id = link.get("link_id", "")
                status = link.get("status", "")

                relationship_type = "CONNECTS_TO"
                relationship_properties = {
                    "link_id": link_id,
                    "status": status,
                    "source_ip": source_ip,
                    "dest_ip": dest_ip,
                    "source_port": source_port,
                    "dest_port": dest_port
                }

                from_name = link.get("source_node", "")
                from_label = "Router"
                to_name = link.get("dest_node", "")
                to_label = "Router"

                await self.create_relationship(
                    graph_helper,
                    from_name, from_label,
                    to_name, to_label,
                    relationship_type,
                    relationship_properties,
                    database=database_name
                )

            return {
                "status": "success",
                "message": f"Topology saved to database '{database_name}' successfully"
            }
        except Exception as e:
            try:
                TerraLogUtil.error(f"Failed to save topology to database: {e}")
                graph_helper.delete_all_relationships(database=database_name)
            except Exception as cleanup_error:
                TerraLogUtil.error(
                    f"Failed to clean up all_relationships in neo4j after topology save failure: {cleanup_error}")
            try:
                graph_helper.delete_all_nodes(database=database_name)
            except Exception as cleanup_error:
                TerraLogUtil.error(
                    f"Failed to clean up all_nodes in neo4j after topology save failure: {cleanup_error}")
            # 注意：delete_database需要session参数，这里没有session，所以跳过PostgreSQL记录的清理
            # 如果需要清理，需要在调用层手动删除
            try:
                await self.delete_database(session, graph_helper, database_name)
            except Exception as cleanup_error:
                TerraLogUtil.error(
                    f"Failed to clean up database record after topology save failure: {cleanup_error}")

            raise HTTPException(status_code=400, detail=f"Failed to save topology to database: {str(e)}")
