from typing import Any, Dict, Optional

from .base import BaseNode, NodeType
# from .agent import AgentNode
# from .plan import PlannerNode
from .worker import WorkerNode
# from .reflection import ReflectionNode
# from .llm_node import LLMNode
# from .tool_node import ToolNode
from apps.models.workflow.models import NodeDefinition, OperatorLog, LLMConfig, ToolConfig


# --- 节点工厂函数 ---

def create_node(
        definition: NodeDefinition,
        operator_log: Optional[OperatorLog] = None,
        workflow_registry: Optional[Dict[str, Any]] = None
) -> BaseNode:
    """
    统一的节点工厂函数
    根据节点定义创建对应的节点实例

    Args:
        definition: 节点定义
        operator_log: 操作符日志
        workflow_registry: 工作流注册表（用于 Agent 节点）

    Returns:
        BaseNode: 创建的节点实例

    Raises:
        ValueError: 不支持的节点类型
    """
    node_type = definition.type

    # 如果没有提供 operator_log，创建一个默认的
    if not operator_log:
        operator_log = OperatorLog(
            node_name=definition.name,
            input_schema={},  # 默认空 schema
            output_schema={}
        )

    if node_type == NodeType.Planner:
        # return PlannerNode(definition.name, definition.config, operator_log)
        pass
    elif node_type == NodeType.Worker:
        return WorkerNode(definition.name, definition.config, operator_log)
    elif node_type == NodeType.Reflection:
        # return ReflectionNode(definition.name, definition.config, operator_log)
        pass
    elif node_type == NodeType.Agent:
        # return AgentNode(definition.name, definition.config, operator_log, workflow_registry)
        pass
    elif node_type == NodeType.LLM:
        # LLM 节点需要 LLMConfig
        llm_config = LLMConfig(**definition.config)
        # return LLMNode(definition.name, llm_config, operator_log=operator_log)
        pass
    elif node_type == NodeType.Tool:
        # Tool 节点需要 ToolConfig
        tool_config = ToolConfig(**definition.config)
        # return ToolNode(definition.name, tool_config, operator_log=operator_log)
        pass
    else:
        raise ValueError(f"Unknown node type: {node_type}")
