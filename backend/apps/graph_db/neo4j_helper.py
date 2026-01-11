"""
Neo4j数据库操作工具类
提供常用的图数据库操作方法，包括节点和关系的CRUD操作
"""

from apps.utils.logger import TerraLogUtil
from typing import Any, Dict, List, Optional, Union
from neo4j import GraphDatabase, Driver, Session, Result
from neo4j.exceptions import Neo4jError
from neo4j.graph import Node, Relationship, Path
import yaml


class Neo4jHelper:
    """Neo4j数据库操作助手类"""
    
    def __init__(self, neo4j_config:  Optional[Dict[str, Any]] = None):
        """
        初始化Neo4j连接
        
        Args:
            uri: Neo4j数据库URI
            username: 用户名
            password: 密码
            config_path: 配置文件路径，如果提供则从配置文件读取连接信息
        """
        self.driver: Optional[Driver] = None
        TerraLogUtil.info(f"Neo4j config: {neo4j_config}")
        self.uri = neo4j_config.get('uri', 'bolt://127.0.0.1:7687')
        self.username = neo4j_config.get('username', 'neo4j')
        self.password = neo4j_config.get('password', 'password')
        self._connect()
        TerraLogUtil.info("Neo4j connection established successfully")
    
    def _connect(self):
        """建立数据库连接"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            # 测试连接
            with self.driver.session() as session:
                session.run("RETURN 1")
            TerraLogUtil.info("Neo4j connection established successfully")
        except Exception as e:
            TerraLogUtil.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            TerraLogUtil.info("Neo4j connection closed")
    
    def __enter__(self):
        """上下文管理器进入"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
    
    def _convert_neo4j_types(self, value: Any) -> Any:
        """
        转换Neo4j类型为Python原生类型
        
        Args:
            value: Neo4j返回的值
            
        Returns:
            转换后的Python原生类型
        """
        if isinstance(value, Node):
            # 节点转换为字典，包含所有属性
            return dict(value)
        elif isinstance(value, Relationship):
            # 关系转换为字典，包含所有属性
            # 使用更详细的方式获取关系属性
            rel_dict = dict(value)  # 获取关系的属性
            # 添加关系的基本信息
            rel_dict.update({
                '_id': value.id,
                '_type': value.type,
                '_start_node_id': value.start_node.id,
                '_end_node_id': value.end_node.id
            })
            return rel_dict
        elif isinstance(value, Path):
            # 路径保持原样
            return value
        elif isinstance(value, list):
            return [self._convert_neo4j_types(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._convert_neo4j_types(v) for k, v in value.items()}
        else:
            # 对于其他类型，检查是否是Neo4j的特殊对象
            # 如果是元组且包含3个元素，可能是关系的简化表示
            if isinstance(value, tuple) and len(value) == 3:
                # 这可能是Neo4j驱动的内部表示，尝试解析
                try:
                    start_node, rel_type, end_node = value
                    return {
                        'start_node': start_node,
                        'type': rel_type,
                        'end_node': end_node
                    }
                except:
                    pass
            return value
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        执行Cypher查询语句
        
        Args:
            query: Cypher查询语句
            parameters: 查询参数
            
        Returns:
            查询结果列表
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                print(f"Query: {query}, result: {result}")
                result_copy = list(result)
                for record in result_copy:
                    print(f"Record data: {record.data()}")
                # 在事务内部将结果转换为列表，避免事务关闭后访问结果
                # 使用自定义转换函数处理Neo4j类型
                return [{k: self._convert_neo4j_types(v) for k, v in record.data().items()} for record in result_copy]
        except Neo4jError as e:
            TerraLogUtil.error(f"Query execution failed: {e}")
            raise
    
    def execute_write_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        执行写操作Cypher查询语句
        
        Args:
            query: Cypher查询语句
            parameters: 查询参数
            
        Returns:
            查询结果列表
        """
        def _execute_tx(tx):
            result = tx.run(query, parameters or {})
            # 在事务内部将结果转换为列表，避免事务关闭后访问结果
            # 使用自定义转换函数处理Neo4j类型
            return [{k: self._convert_neo4j_types(v) for k, v in record.data().items()} for record in result]
        
        try:
            with self.driver.session() as session:
                return session.execute_write(_execute_tx)
        except Neo4jError as e:
            TerraLogUtil.error(f"Write query execution failed: {e}")
            raise
    
    # 节点操作方法
    
    def create_node(self, label: str, properties: Dict[str, Any] = None, database: str = None) -> Dict[str, Any]:
        """
        创建节点
        
        Args:
            label: 节点标签
            properties: 节点属性
            database: 逻辑数据库名称,默认为None
            
        Returns:
            创建的节点信息
        """
        properties = properties or {}
        # 如果指定了database,添加到属性中
        if database is not None:
            properties['database'] = database
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        query = f"CREATE (n:{label} {{{props_str}}}) RETURN n"
        
        result = self.execute_write_query(query, properties)
        return result[0] if result else {}
    
    def merge_node(self, label: str, unique_properties: Dict[str, Any], 
                   additional_properties: Dict[str, Any] = None, database: str = None) -> Dict[str, Any]:
        """
        合并节点（存在则不重复创建）
        
        Args:
            label: 节点标签
            unique_properties: 用于匹配的唯一属性
            additional_properties: 额外的属性（在创建时设置）
            database: 逻辑数据库名称,默认为None
            
        Returns:
            节点信息
        """
        additional_properties = additional_properties or {}
        
        # 如果指定了database,添加到唯一属性中(用于匹配)
        if database is not None:
            unique_properties = {**unique_properties, 'database': database}
        
        # 构建MERGE语句
        unique_props_str = ", ".join([f"{k}: ${k}" for k in unique_properties.keys()])
        query = f"MERGE (n:{label} {{{unique_props_str}}})"
        
        # 如果有额外属性，在创建时设置
        if additional_properties:
            set_props_str = ", ".join([f"n.{k} = ${k}" for k in additional_properties.keys()])
            query += f" ON CREATE SET {set_props_str}"
        
        query += " RETURN n"
        
        all_props = {**unique_properties, **additional_properties}
        result = self.execute_write_query(query, all_props)
        return result[0] if result else {}
    
    def update_node_properties(self, label: str, match_properties: Dict[str, Any], 
                             update_properties: Dict[str, Any], database: str = None) -> List[Dict[str, Any]]:
        """
        更新节点属性
        
        Args:
            label: 节点标签
            match_properties: 用于匹配节点的属性
            update_properties: 要更新的属性
            database: 逻辑数据库名称,默认为None
            
        Returns:
            更新后的节点列表
        """
        # 如果指定了database,添加到匹配条件中
        if database is not None:
            match_properties = {**match_properties, 'database': database}
        
        # 构建MATCH条件
        match_props_str = " AND ".join([f"n.{k} = ${k}" for k in match_properties.keys()])
        
        # 构建SET语句
        set_props_str = ", ".join([f"n.{k} = $set_{k}" for k in update_properties.keys()])
        
        query = f"MATCH (n:{label}) WHERE {match_props_str} SET {set_props_str} RETURN n"
        
        # 组合参数
        params = {**match_properties}
        params.update({f"set_{k}": v for k, v in update_properties.items()})
        
        return self.execute_write_query(query, params)

    def delete_all_nodes(self, database: str = None) -> int:
        """
        删除所有节点（会先删除相关关系）

        Args:
            database: 逻辑数据库名称,默认为None

        Returns:
            删除的节点数量
        """
        # 如果指定了database,在节点上添加过滤条件
        node_filter = f"WHERE n.database = $node_database" if database is not None else ""

        query = f"""
        MATCH (n)
        {node_filter}
        DETACH DELETE n
        """

        params = {}
        if database is not None:
            params['node_database'] = database

        def _delete_tx(tx):
            result = tx.run(query, params)
            # 在事务内部获取计数器，避免事务关闭后访问结果
            summary = result.consume()
            return summary.counters.nodes_deleted

        with self.driver.session() as session:
            return session.execute_write(_delete_tx)
    
    def delete_node(self, label: str, properties: Dict[str, Any], database: str = None) -> int:
        """
        删除节点（会先删除相关关系）
        
        Args:
            label: 节点标签
            properties: 用于匹配节点的属性
            database: 逻辑数据库名称,默认为None
            
        Returns:
            删除的节点数量
        """
        # 如果指定了database,添加到匹配条件中
        if database is not None:
            properties = {**properties, 'database': database}
        
        # 构建匹配条件
        props_str = " AND ".join([f"n.{k} = ${k}" for k in properties.keys()])
        
        # 先删除关系，再删除节点
        query = f"MATCH (n:{label}) WHERE {props_str} DETACH DELETE n"
        
        def _delete_tx(tx):
            result = tx.run(query, properties)
            # 在事务内部获取计数器，避免事务关闭后访问结果
            summary = result.consume()
            return summary.counters.nodes_deleted
        
        with self.driver.session() as session:
            return session.execute_write(_delete_tx)
    
    # 关系操作方法
    
    def create_relationship(self, from_label: str, from_properties: Dict[str, Any],
                          to_label: str, to_properties: Dict[str, Any],
                          relationship_type: str, relationship_properties: Dict[str, Any] = None,
                          database: str = None) -> Dict[str, Any]:
        """
        创建关系
        
        Args:
            from_label: 起始节点标签
            from_properties: 起始节点属性
            to_label: 目标节点标签
            to_properties: 目标节点属性
            relationship_type: 关系类型
            relationship_properties: 关系属性
            database: 逻辑数据库名称,默认为None
            
        Returns:
            创建的关系信息
        """
        relationship_properties = relationship_properties or {}
        
        # 如果指定了database,添加到节点匹配条件和关系属性中
        if database is not None:
            from_properties = {**from_properties, 'database': database}
            to_properties = {**to_properties, 'database': database}
            relationship_properties['database'] = database
        
        # 构建匹配条件
        from_props_str = " AND ".join([f"a.{k} = $from_{k}" for k in from_properties.keys()])
        to_props_str = " AND ".join([f"b.{k} = $to_{k}" for k in to_properties.keys()])
        
        # 构建关系属性
        rel_props_str = ""
        if relationship_properties:
            rel_props_str = " {" + ", ".join([f"{k}: $rel_{k}" for k in relationship_properties.keys()]) + "}"
        
        query = f"""
        MATCH (a:{from_label}) WHERE {from_props_str}
        MATCH (b:{to_label}) WHERE {to_props_str}
        CREATE (a)-[r:{relationship_type}{rel_props_str}]->(b)
        RETURN r
        """
        
        # 组合参数
        params = {}
        params.update({f"from_{k}": v for k, v in from_properties.items()})
        params.update({f"to_{k}": v for k, v in to_properties.items()})
        params.update({f"rel_{k}": v for k, v in relationship_properties.items()})
        
        TerraLogUtil.debug(f"Creating relationship with query: {query}, params: {params}")
        result = self.execute_write_query(query, params)
        TerraLogUtil.debug(f"Create relationship result: {result}")
        return result[0] if result else {}

    def merge_relationship(self, from_label: str, from_properties: Dict[str, Any],
                            to_label: str, to_properties: Dict[str, Any],
                           relationship_type: str, relationship_properties: Dict[str, Any] = None,
                           database: str = None) -> Dict[str, Any]:
        """
        合并关系（存在则不重复创建）

        Args:
            from_label: 起始节点标签
            from_properties: 起始节点属性
            to_label: 目标节点标签
            to_properties: 目标节点属性
            relationship_type: 关系类型
            relationship_properties: 关系属性
            database: 逻辑数据库名称,默认为None

        Returns:
            关系信息
        """
        relationship_properties = relationship_properties or {}

        # 如果指定了database,添加到节点匹配条件和关系属性中
        if database is not None:
            from_properties = {**from_properties, 'database': database}
            to_properties = {**to_properties, 'database': database}
            relationship_properties['database'] = database

        # 构建匹配条件
        from_props_str = " AND ".join([f"a.{k} = $from_{k}" for k in from_properties.keys()])
        to_props_str = " AND ".join([f"b.{k} = $to_{k}" for k in to_properties.keys()])

        # 构建关系属性
        rel_props_str = ""
        if relationship_properties:
            rel_props_str = " {" + ", ".join([f"{k}: $rel_{k}" for k in relationship_properties.keys()]) + "}"

        query = f"""
                MATCH (a:{from_label}) WHERE {from_props_str}
                MATCH (b:{to_label}) WHERE {to_props_str}
                MERGE (a)-[r:{relationship_type}{rel_props_str}]->(b)
                RETURN r
                """

        # 组合参数
        params = {}
        params.update({f"from_{k}": v for k, v in from_properties.items()})
        params.update({f"to_{k}": v for k, v in to_properties.items()})
        params.update({f"rel_{k}": v for k, v in relationship_properties.items()})

        result = self.execute_write_query(query, params)
        return result[0] if result else {}

    def delete_all_relationships(self, database: str = None) -> int:
        """
        删除所有关系

        Args:
            database: 逻辑数据库名称,默认为None

        Returns:
            删除的关系数量
        """
        # 如果指定了database,在关系上添加过滤条件
        rel_filter = f"WHERE r.database = $rel_database" if database is not None else ""

        query = f"""
        MATCH ()-[r]->()
        {rel_filter}
        DELETE r
        """

        params = {}
        if database is not None:
            params['rel_database'] = database

        def _delete_tx(tx):
            result = tx.run(query, params)
            # 在事务内部获取计数器，避免事务关闭后访问结果
            summary = result.consume()
            return summary.counters.relationships_deleted

        with self.driver.session() as session:
            return session.execute_write(_delete_tx)
    
    def delete_relationship(self, from_label: str, from_properties: Dict[str, Any],
                          to_label: str, to_properties: Dict[str, Any],
                          relationship_type: str, database: str = None) -> int:
        """
        删除关系
        
        Args:
            from_label: 起始节点标签
            from_properties: 起始节点属性
            to_label: 目标节点标签
            to_properties: 目标节点属性
            relationship_type: 关系类型
            database: 逻辑数据库名称,默认为None
            
        Returns:
            删除的关系数量
        """
        # 如果指定了database,添加到节点和关系匹配条件中
        if database is not None:
            from_properties = {**from_properties, 'database': database}
            to_properties = {**to_properties, 'database': database}
        
        # 构建匹配条件
        from_props_str = " AND ".join([f"a.{k} = $from_{k}" for k in from_properties.keys()])
        to_props_str = " AND ".join([f"b.{k} = $to_{k}" for k in to_properties.keys()])
        
        # 如果指定了database,在关系上也添加过滤条件
        rel_filter = f" AND r.database = $rel_database" if database is not None else ""
        
        query = f"""
        MATCH (a:{from_label})-[r:{relationship_type}]->(b:{to_label})
        WHERE {from_props_str} AND {to_props_str}{rel_filter}
        DELETE r
        """
        
        # 组合参数
        params = {}
        params.update({f"from_{k}": v for k, v in from_properties.items()})
        params.update({f"to_{k}": v for k, v in to_properties.items()})
        if database is not None:
            params['rel_database'] = database
        
        def _delete_tx(tx):
            result = tx.run(query, params)
            # 在事务内部获取计数器，避免事务关闭后访问结果
            summary = result.consume()
            return summary.counters.relationships_deleted
        
        with self.driver.session() as session:
            return session.execute_write(_delete_tx)
    
    def delete_relationship_by_id(self, relationship_id: str) -> int:
        """
        通过关系ID删除关系（精确删除单条关系）
        
        Args:
            relationship_id: Neo4j 关系的内部 ID（格式："5:xxxxx:10"）
            
        Returns:
            删除的关系数量（0 或 1）
        """
        # Neo4j 5.x 使用 elementId() 替代已弃用的 id()
        # elementId() 返回字符串格式的 ID，如 "5:13367c5f-7851-4dee-a706-2d183e30da21:10"
        
        # 输入校验
        if not relationship_id or not isinstance(relationship_id, str):
            TerraLogUtil.error(f"Invalid relationship ID: {relationship_id}")
            raise ValueError(f"Invalid relationship ID: {relationship_id}")
        
        query = """
        MATCH ()-[r]-()
        WHERE elementId(r) = $rel_id
        DELETE r
        """
        
        params = {'rel_id': relationship_id}
        
        def _delete_tx(tx):
            result = tx.run(query, params)
            # 在事务内部获取计数器
            summary = result.consume()
            return summary.counters.relationships_deleted
        
        with self.driver.session() as session:
            return session.execute_write(_delete_tx)
    
    def update_relationship_properties(self, from_label: str, from_properties: Dict[str, Any],
                                     to_label: str, to_properties: Dict[str, Any],
                                     relationship_type: str, update_properties: Dict[str, Any],
                                     database: str = None) -> List[Dict[str, Any]]:
        """
        更新关系属性
        
        Args:
            from_label: 起始节点标签
            from_properties: 起始节点属性
            to_label: 目标节点标签
            to_properties: 目标节点属性
            relationship_type: 关系类型
            update_properties: 要更新的关系属性
            database: 逻辑数据库名称,默认为None
            
        Returns:
            更新后的关系列表
        """
        # 如果指定了database,添加到节点匹配条件中
        if database is not None:
            from_properties = {**from_properties, 'database': database}
            to_properties = {**to_properties, 'database': database}
        
        # 构建匹配条件
        from_props_str = " AND ".join([f"a.{k} = $from_{k}" for k in from_properties.keys()])
        to_props_str = " AND ".join([f"b.{k} = $to_{k}" for k in to_properties.keys()])
        
        # 如果指定了database,在关系上也添加过滤条件
        rel_filter = f" AND r.database = $rel_database" if database is not None else ""
        
        # 构建SET语句
        set_props_str = ", ".join([f"r.{k} = $set_{k}" for k in update_properties.keys()])
        
        query = f"""
        MATCH (a:{from_label})-[r:{relationship_type}]->(b:{to_label})
        WHERE {from_props_str} AND {to_props_str}{rel_filter}
        SET {set_props_str}
        RETURN r
        """
        
        # 组合参数
        params = {}
        params.update({f"from_{k}": v for k, v in from_properties.items()})
        params.update({f"to_{k}": v for k, v in to_properties.items()})
        params.update({f"set_{k}": v for k, v in update_properties.items()})
        if database is not None:
            params['rel_database'] = database
        
        return self.execute_write_query(query, params)
    
    # 查询方法
    
    def get_all_nodes(self, label: str = None, limit: int = 100, database: str = None) -> List[Dict[str, Any]]:
        """
        查询所有节点
        
        Args:
            label: 节点标签，如果为None则查询所有标签的节点
            limit: 限制返回数量
            database: 逻辑数据库名称,默认为None(查询所有数据库)
            
        Returns:
            节点列表，每个节点包含labels和properties
        """
        params = {}
        db_filter = ""
        if database is not None:
            db_filter = " WHERE n.database = $database"
            params['database'] = database
        
        if label:
            query = f"MATCH (n:{label}){db_filter} RETURN n, labels(n) as node_labels LIMIT {limit}"
        else:
            query = f"MATCH (n){db_filter} RETURN n, labels(n) as node_labels LIMIT {limit}"
        
        return self.execute_query(query, params)
    
    def get_node_properties(self, label: str, properties: Dict[str, Any], database: str = None) -> List[Dict[str, Any]]:
        """
        查询节点的属性
        
        Args:
            label: 节点标签
            properties: 用于匹配节点的属性
            database: 逻辑数据库名称,默认为None
            
        Returns:
            节点属性列表
        """
        # 如果指定了database,添加到匹配条件中
        if database is not None:
            properties = {**properties, 'database': database}
        
        props_str = " AND ".join([f"n.{k} =  ${k}" for k in properties.keys()])
        query = f"MATCH (n:{label}) WHERE {props_str} RETURN n"
        TerraLogUtil.info(f"Executing get_node_properties with query: {query} and properties: {properties}")
        
        return self.execute_query(query, properties)
    
    def get_relationships(self, relationship_type: str = None, 
                         from_label: str = None, to_label: str = None,
                         limit: int = 100, database: str = None) -> List[Dict[str, Any]]:
        """
        查询关系
        
        Args:
            relationship_type: 关系类型
            from_label: 起始节点标签
            to_label: 目标节点标签
            limit: 限制返回数量
            database: 逻辑数据库名称,默认为None(查询所有数据库)
            
        Returns:
            关系列表，包含节点和关系信息
        """
        # 构建查询
        from_pattern = f"(a:{from_label})" if from_label else "(a)"
        to_pattern = f"(b:{to_label})" if to_label else "(b)"
        rel_pattern = f"[r:{relationship_type}]" if relationship_type else "[r]"
        
        params = {}
        db_filter = ""
        if database is not None:
            db_filter = " WHERE a.database = $database AND b.database = $database AND r.database = $database"
            params['database'] = database
        
        query = f"MATCH {from_pattern}-{rel_pattern}->{to_pattern}{db_filter} RETURN a, labels(a) as from_labels, r, type(r) as rel_type, b, labels(b) as to_labels LIMIT {limit}"
        
        return self.execute_query(query, params)
    
    def get_relationship_properties(self, relationship_type: str, 
                                   from_label: str = None, from_properties: Dict[str, Any] = None,
                                   to_label: str = None, to_properties: Dict[str, Any] = None,
                                   limit: int = 100, database: str = None) -> List[Dict[str, Any]]:
        """
        查询关系的详细属性
        
        Args:
            relationship_type: 关系类型
            from_label: 起始节点标签
            from_properties: 起始节点匹配属性
            to_label: 目标节点标签  
            to_properties: 目标节点匹配属性
            limit: 限制返回数量
            database: 逻辑数据库名称,默认为None
            
        Returns:
            关系属性列表,每个元素包含 {'from_node': {...}, 'relationship': {...}, 'to_node': {...}}
        """
        # 构建查询条件
        from_pattern = f"(a:{from_label})" if from_label else "(a)"
        to_pattern = f"(b:{to_label})" if to_label else "(b)"
        rel_pattern = f"[r:{relationship_type}]" if relationship_type else "[r]"
        
        where_conditions = []
        params = {}
        
        # 如果指定了database,添加到所有匹配条件中
        if database is not None:
            where_conditions.append("a.database = $database")
            where_conditions.append("b.database = $database")
            where_conditions.append("r.database = $database")
            params['database'] = database
        
        # 添加起始节点条件
        if from_properties:
            from_conditions = [f"a.{k} = $from_{k}" for k in from_properties.keys()]
            where_conditions.extend(from_conditions)
            params.update({f"from_{k}": v for k, v in from_properties.items()})
        
        # 添加目标节点条件
        if to_properties:
            to_conditions = [f"b.{k} = $to_{k}" for k in to_properties.keys()]
            where_conditions.extend(to_conditions)
            params.update({f"to_{k}": v for k, v in to_properties.items()})        
        # 构建完整查询 - 使用properties()函数显式获取关系属性
        query = f"MATCH {from_pattern}-{rel_pattern}->{to_pattern}"
        if where_conditions:
            query += f" WHERE {' AND '.join(where_conditions)}"
        query += f" RETURN a as from_node, labels(a) as from_labels, properties(r) as relationship_props, type(r) as relationship_type, elementId(r) as relationship_id, b as to_node, labels(b) as to_labels LIMIT {limit}"
        
        result = self.execute_query(query, params)
        
        # 重新组织结果格式
        formatted_result = []
        for record in result:
            relationship_data = record['relationship_props'].copy()
            relationship_data.update({
                '_id': record['relationship_id'],
                '_type': record['relationship_type']
            })
            from_node_data = record['from_node'].copy()
            from_node_data.update({'labels': record.get('from_labels', [])})

            to_node_data = record['to_node'].copy()
            to_node_data.update({'labels': record.get('to_labels', [])})
            
            formatted_result.append({
                'from_node': from_node_data,
                'relationship': relationship_data,
                'to_node': to_node_data
            })
            
        return formatted_result
    
    def find_all_paths_from_node(self, label: str, properties: Dict[str, Any], 
                                max_depth: int = 5, database: str = None) -> List[Dict[str, Any]]:
        """
        查询从指定节点开始的所有路径
        
        Args:
            label: 起始节点标签
            properties: 起始节点属性
            max_depth: 最大深度
            database: 逻辑数据库名称,默认为None
            
        Returns:
            路径列表
        """
        # 如果指定了database,添加到匹配条件中
        if database is not None:
            properties = {**properties, 'database': database}
        
        props_str = " AND ".join([f"start.{k} = ${k}" for k in properties.keys()])
        
        # 添加database过滤条件到路径中的所有节点和关系
        db_filter = ""
        if database is not None:
            db_filter = f" AND all(n IN nodes(path) WHERE n.database = '{database}') AND all(r IN relationships(path) WHERE r.database = '{database}')"
        
        query = f"""
        MATCH (start:{label}) WHERE {props_str}
        MATCH path = (start)-[*1..{max_depth}]-(end)
        WHERE TRUE{db_filter}
        RETURN path
        """
        
        return self.execute_query(query, properties)

    def find_all_paths_from_node_all(self, label: str, properties: Dict[str, Any], database: str = None) -> List[Dict[str, Any]]:
        """
        查询从指定节点开始的所有路径

        Args:
            label: 起始节点标签
            properties: 起始节点属性
            database: 逻辑数据库名称,默认为None

        Returns:
            路径列表
        """
        # 如果指定了database,添加到匹配条件中
        if database is not None:
            properties = {**properties, 'database': database}
        
        props_str = " AND ".join([f"start.{k} = ${k}" for k in properties.keys()])
        
        # 添加database过滤条件
        db_filter = ""
        if database is not None:
            db_filter = f" AND end.database = '{database}' AND all(n IN nodes(path) WHERE n.database = '{database}') AND all(r IN relationships(path) WHERE r.database = '{database}')"
        
        query = f"""
        MATCH (start:{label}) WHERE {props_str}
        MATCH path = (start)-[*]-(end)
        WHERE end.FinalAnswer IS NOT NULL{db_filter}
        RETURN path
        """

        return self.execute_query(query, properties)

    def find_shortest_path(self, from_label: str, from_properties: Dict[str, Any],
                          to_label: str, to_properties: Dict[str, Any], database: str = None) -> List[Dict[str, Any]]:
        """
        查询两个节点之间的最短路径
        
        Args:
            from_label: 起始节点标签
            from_properties: 起始节点属性
            to_label: 目标节点标签
            to_properties: 目标节点属性
            database: 逻辑数据库名称,默认为None
            
        Returns:
            最短路径列表
        """
        # 如果指定了database,添加到匹配条件中
        if database is not None:
            from_properties = {**from_properties, 'database': database}
            to_properties = {**to_properties, 'database': database}
        
        from_props_str = " AND ".join([f"a.{k} = $from_{k}" for k in from_properties.keys()])
        to_props_str = " AND ".join([f"b.{k} = $to_{k}" for k in to_properties.keys()])
        
        # 添加database过滤条件到路径中的所有节点和关系
        db_filter = ""
        if database is not None:
            db_filter = f" AND all(n IN nodes(path) WHERE n.database = '{database}') AND all(r IN relationships(path) WHERE r.database = '{database}')"
        
        query = f"""
        MATCH (a:{from_label}) WHERE {from_props_str}
        MATCH (b:{to_label}) WHERE {to_props_str}
        MATCH path = shortestPath((a)-[*]-(b))
        WHERE TRUE{db_filter}
        RETURN path
        """
        
        # 组合参数
        params = {}
        params.update({f"from_{k}": v for k, v in from_properties.items()})
        params.update({f"to_{k}": v for k, v in to_properties.items()})
        
        return self.execute_query(query, params)
    
    # 工具方法
    
    def create_index(self, label: str, property_name: str, index_name: str = None) -> bool:
        """
        创建索引
        
        Args:
            label: 节点标签
            property_name: 属性名
            index_name: 索引名称（可选）
            
        Returns:
            是否成功创建
        """
        try:
            if index_name:
                query = f"CREATE INDEX {index_name} IF NOT EXISTS FOR (n:{label}) ON (n.{property_name})"
            else:
                query = f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.{property_name})"
            
            self.execute_write_query(query)
            return True
        except Exception as e:
            TerraLogUtil.error(f"Failed to create index: {e}")
            return False
    
    def create_unique_constraint(self, label: str, property_name: str, constraint_name: str = None) -> bool:
        """
        创建唯一性约束
        
        Args:
            label: 节点标签
            property_name: 属性名
            constraint_name: 约束名称（可选）
            
        Returns:
            是否成功创建
        """
        try:
            # 根据经验教训，先尝试删除同字段上的普通索引
            # Neo4j 5.x 需要通过索引名称来删除索引
            try:
                # 查询该标签和属性上的所有索引
                indexes_query = "SHOW INDEXES YIELD name, labelsOrTypes, properties, type WHERE $label IN labelsOrTypes AND properties = [$property] AND type <> 'RANGE'"
                indexes = self.execute_query(indexes_query, {"label": label, "property": property_name})
                
                # 删除找到的索引
                for index in indexes:
                    index_name = index.get('name')
                    if index_name:
                        drop_query = f"DROP INDEX {index_name} IF EXISTS"
                        self.execute_write_query(drop_query)
            except Exception as e:
                # 忽略删除索引的错误，因为索引可能不存在
                TerraLogUtil.debug(f"Failed to drop index: {e}")
            
            if constraint_name:
                query = f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS FOR (n:{label}) REQUIRE n.{property_name} IS UNIQUE"
            else:
                query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.{property_name} IS UNIQUE"
            
            self.execute_write_query(query)
            return True
        except Exception as e:
            TerraLogUtil.error(f"Failed to create unique constraint: {e}")
            return False
    
    def get_database_info(self, database: str = None) -> Dict[str, Any]:
        """
        获取数据库信息
        
        Args:
            database: 逻辑数据库名称,默认为None(查询所有数据库)
        
        Returns:
            数据库信息字典
        """
        try:
            params = {}
            db_filter = ""
            if database is not None:
                db_filter = " WHERE n.database = $database"
                params['database'] = database
            
            # 获取节点数量
            node_count_result = self.execute_query(f"MATCH (n){db_filter} RETURN count(n) as node_count", params)
            node_count = node_count_result[0]['node_count'] if node_count_result else 0
            
            # 获取关系数量
            rel_filter = ""
            if database is not None:
                rel_filter = " WHERE r.database = $database"
            rel_count_result = self.execute_query(f"MATCH ()-[r]->(){rel_filter} RETURN count(r) as rel_count", params)
            rel_count = rel_count_result[0]['rel_count'] if rel_count_result else 0
            
            # 获取标签信息
            labels_result = self.execute_query("CALL db.labels()")
            labels = [record['label'] for record in labels_result]
            
            # 获取关系类型信息
            rel_types_result = self.execute_query("CALL db.relationshipTypes()")
            rel_types = [record['relationshipType'] for record in rel_types_result]
            
            return {
                'node_count': node_count,
                'relationship_count': rel_count,
                'labels': labels,
                'relationship_types': rel_types,
                'database': database if database else 'all'
            }
        except Exception as e:
            TerraLogUtil.error(f"Failed to get database info: {e}")
            return {}