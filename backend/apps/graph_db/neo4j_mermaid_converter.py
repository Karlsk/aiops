import networkx as nx
from typing import List, Dict, Any

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from .neo4j_helper import Neo4jHelper

class Neo4jMermaidConverter:
    def __init__(self, neo4j_helper):

        # 初始化Neo4jHelper类
        self.neo4j_helper = neo4j_helper
        self.graph = nx.DiGraph()
        # 存储边的额外信息（关系类型和条件）
        self.edge_info = {}

    def query_paths(self, name: str, database: str = None) -> List[Dict[str, Any]]:
        """
        执行 Neo4j 查询，返回路径中的节点和关系信息。
        
        Args:
            name: 事件名称
            database: 逻辑数据库名称，默认为None
        """
        # 如果指定了database,添加到匹配条件中
        db_filter = ""
        if database is not None:
            db_filter = f" AND start.database = '{database}' AND end.database = '{database}' AND all(n IN nodes(path) WHERE n.database = '{database}') AND all(r IN relationships(path) WHERE r.database = '{database}')"
        
        # 使用更详细的查询来获取关系信息
        query = f"""
        MATCH (start:Event {{name: '{name}'}}) 
        MATCH path = (start)-[*]->(end) 
        WHERE end.FinalAnswer IS NOT NULL{db_filter}  
        WITH path, 
             [node IN nodes(path) | node] as node_list,
             [rel IN relationships(path) | {{type: type(rel), condition: rel.Condition}}] as rel_list 
        RETURN node_list, rel_list
        """
        
        results = self.neo4j_helper.execute_query(query)
        
        # 重新组织数据，将节点和关系交替排列
        paths = []
        for result in results:
            node_list = result.get('node_list', [])
            rel_list = result.get('rel_list', [])
            
            # 交替合并节点和关系
            path = []
            for i, node in enumerate(node_list):
                path.append(node)
                if i < len(rel_list):
                    path.append(rel_list[i])
            
            paths.append({'path': path})
        
        return paths


    def build_graph(self, paths: List[Dict[str, Any]]) -> nx.DiGraph:
        """
        根据 paths 构建有向图，并提取关系类型和条件信息。
        """
        for record in paths:
            path_nodes = record["path"]
            prev_name = None
            current_rel_info = None

            for i, item in enumerate(path_nodes):
                # 如果是关系信息（字典且包含 'type' 键）
                if isinstance(item, dict) and 'type' in item and 'condition' in item:
                    current_rel_info = item
                    continue
                
                # 如果是字符串（旧格式的关系类型）
                if isinstance(item, str) and item in ['Sequence', 'Branch']:
                    if current_rel_info is None:
                        current_rel_info = {'type': item, 'condition': None}
                    continue

                # 处理节点
                if isinstance(item, dict):
                    node_name = item.get("name") or item.get("FinalAnswer")
                    if not node_name:
                        continue

                    # 添加节点（附加属性）
                    if node_name not in self.graph:
                        self.graph.add_node(node_name, **item)

                    # 建立边关系
                    if prev_name:
                        edge_key = (prev_name, node_name)
                        if not self.graph.has_edge(prev_name, node_name):
                            self.graph.add_edge(prev_name, node_name)
                            # 存储边的关系类型和条件
                            if current_rel_info:
                                self.edge_info[edge_key] = {
                                    'rel_type': current_rel_info.get('type'),
                                    'condition': current_rel_info.get('condition')
                                }

                    prev_name = node_name
                    current_rel_info = None  # 重置关系信息
                    
        return self.graph

    def to_mermaid(self) -> str:
        """
        将 graph 转换为 Mermaid flowchart 格式。
        """
        lines = ["flowchart TD"]
        step_counter = 1
        node_to_step = {}  # 节点名到步骤编号的映射
        final_counter = 1
        final_nodes = {}  # FinalAnswer 节点映射

        # === Step1: 创建 subgraph（普通步骤节点）===
        for node, data in self.graph.nodes(data=True):
            if "Action" in data:  # 普通步骤
                node_name = data['name']
                node_to_step[node] = step_counter
                
                lines.append(f"    subgraph S{step_counter} [Step{step_counter}: {node_name}]")
                lines.append(f"        A_{node_name}[Action: {data['Action']}]")
                
                if "Observation" in data:
                    lines.append(f"        O_{node_name}[Observation: {data['Observation']}]")
                
                # 确定 Next Step 描述
                next_step_desc = self._get_next_step_description(node)
                lines.append(f"        N_{node_name}[Next Step: {next_step_desc}]")
                
                lines.append("    end")
                step_counter += 1

        # === Step2: 创建 FinalAnswer 节点 ===
        for node, data in self.graph.nodes(data=True):
            if "FinalAnswer" in data:
                fa = data["FinalAnswer"]
                lines.append(f"    T{final_counter}[(终结输出：{fa})]")
                final_nodes[node] = f"T{final_counter}"
                final_counter += 1

        # === Step3: 创建边 ===
        for src, dst in self.graph.edges():
            src_data = self.graph.nodes[src]
            dst_data = self.graph.nodes[dst]
            edge_key = (src, dst)
            edge_info = self.edge_info.get(edge_key, {})

            # 确定源节点标识
            if src in node_to_step:
                src_node = f"N_{src_data['name']}"
            else:
                # 可能是起始节点或其他类型
                continue  # 跳过非步骤节点作为源

            # 确定目标节点标识
            if dst in node_to_step:
                dst_node = f"S{node_to_step[dst]}"
            elif dst in final_nodes:
                dst_node = final_nodes[dst]
            else:
                continue

            # 获取边的条件标签
            edge_label = ""
            condition = edge_info.get('condition')
            if condition:
                edge_label = f"|{condition}|"

            lines.append(f"    {src_node} -->{edge_label} {dst_node}")

        return "\n".join(lines)

    def _get_next_step_description(self, node_name: str) -> str:
        """
        根据出边的关系类型确定 Next Step 的描述。
        
        Args:
            node_name: 节点名称
            
        Returns:
            Next Step 的描述文本
        """
        # 获取该节点的所有出边
        out_edges = list(self.graph.out_edges(node_name))
        
        if not out_edges:
            return "完成"
        
        # 检查是否有 Branch 类型的边
        has_branch = False
        next_node_name = None
        
        for src, dst in out_edges:
            edge_key = (src, dst)
            edge_info = self.edge_info.get(edge_key, {})
            rel_type = edge_info.get('rel_type')
            
            if rel_type == 'Branch':
                has_branch = True
            elif rel_type == 'Sequence':
                dst_data = self.graph.nodes[dst]
                next_node_name = dst_data.get('name')
        
        if has_branch:
            return "根据结果选择分支"
        elif next_node_name:
            return next_node_name
        else:
            return "继续下一步"

if __name__ == "__main__":
    from apps.utils.config import settings
    config_path = os.path.join(os.path.dirname(__file__), '../..', 'etc', 'config.yaml')
    config = settings.get_graph_db_config()
    neo4j_config = config.get('neo4j', {})

    # 初始化Neo4jHelper类
    neo4j_helper = Neo4jHelper(neo4j_config=neo4j_config)

    converter = Neo4jMermaidConverter(neo4j_helper)
    try:
        paths = converter.query_paths("bgp邻居down")
        print(f"查询到 {len(paths)} 条路径")
        graph = converter.build_graph(paths)
        print(f"构建的图包含 {graph.number_of_nodes()} 个节点和 {graph.number_of_edges()} 条边")
        print(f"图结构如下：")
        print(f"节点：{graph.nodes}")
        print(f"边：{graph.edges}")
        print(f"属性：{graph.graph}")
        
        print(f"转换后的 Mermaid 流程图如下：")
        mermaid_output = converter.to_mermaid()
        print(mermaid_output)
    finally:
        neo4j_helper.close()