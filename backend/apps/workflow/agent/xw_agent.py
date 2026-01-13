from typing import Dict, Any, Optional, Literal
import time
from langgraph.graph import StateGraph, START, END  # LangGraph的核心类

from langchain_core.runnables import Runnable, RunnableLambda
from ..node.base import BaseNode
from apps.models.workflow.models import NodeType
from apps.models.workflow.models import GraphPlanAgentConfig, ExecutionLog, OperatorLog, PlanSubType, ActionType
from apps.models.workflow.custom_state import XwGraphAgentState, XwGraphAgentOutputState, GraphAgentState, GraphAgentOutputState

from ..node.plan import PlannerNode
from ..node.worker import WorkerNode
from ..node.reflection import ReflectionNode
from ...utils.utils import convert_state_to_dict, map_output_to_state


class XwAgent(BaseNode):
    """
    XwAgent 节点：基于图数据库的智能体工作流
    """

    def __init__(self, name: str, config: Dict[str, Any], operator_log: Optional[OperatorLog] = None):
        super().__init__(name, NodeType.Reflection, config, operator_log)
        self.agent_config = GraphPlanAgentConfig(**config)
        self.agent_name = self.agent_config.name
        self.graph = None

    def get_agent_config(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "graph_db_config": self.agent_config.graph_config if self.agent_config.graph_config else {},
            "run_mode": self.agent_config.run_mode,
            "action_config": self.agent_config.action_config if self.agent_config.action_config else {}
        }

    def get_agent_mcp_config(self) -> Dict[str, Any]:
        if self.agent_config.action_config.action_type != ActionType.MCP:
            return {}

        return self.agent_config.action_config.mcp_config

    def create_plan_node(self) -> Runnable:
        graph_db_name = self.agent_config.graph_config.graph_db_name if self.agent_config.graph_config else "default"
        api_url = self.agent_config.graph_config.api_url if self.agent_config.graph_config else "http://localhost:7801"
        sub_type = self.agent_config.run_mode

        config = {
            "sub_type": sub_type,
            "graph_db_name": graph_db_name,
            "api_url": api_url
        }

        planner_node = PlannerNode(
            name=f"planner_{self.agent_name}",
            config=config
        )

        return planner_node.build_runnable()

    def create_reflection_node(self) -> Runnable:
        sub_type = self.agent_config.run_mode
        config = {
            "sub_type": sub_type,
        }
        reflection_node = ReflectionNode(
            name=f"reflection_{self.agent_name}",
            config=config
        )
        return reflection_node.build_runnable()

    def create_worker_node(self) -> Runnable:
        server_configs = self.get_agent_mcp_config()
        if self.agent_config.action_config.action_type != ActionType.MCP:
            raise NotImplementedError("Currently only MCP action type is supported in XwAgent")
        config = {
            "sub_type": self.agent_config.action_config.action_type.value,
            "mcp_configs": server_configs,
        }
        worker_node = WorkerNode(
            name=f"worker_{self.agent_name}",
            config=config
        )
        return worker_node.build_runnable()

    def init_history_node(self, state: XwGraphAgentState) -> XwGraphAgentState:
        event_name = state.get("event_name", "")
        segment_id = state.get("segment_id", "")
        history_entry = {"type": "user", "content": f"联通子段:{segment_id}"}
        history = state.get("history", [])
        history.append(history_entry)
        state["history"] = history
        return {
            "event_name": event_name,
            "segment_id": segment_id,
            "history": history,
            "sub_type": self.agent_config.run_mode
        }

    @staticmethod
    def cycle_condition(state: XwGraphAgentState) -> Literal["worker_node", "__end__"]:
        # 根据 state 中的某个字段决定是否继续循环
        final_answer = state.get("final_answer", "")
        if final_answer:
            return END
        else:
            return "worker_node"

    @staticmethod
    def plan_type_condition(state: XwGraphAgentState) -> Literal["reflection_node", "planner_node"]:
        # 根据 sub_type 决定下一步走反思节点还是工作节点
        sub_type_e = state.get("sub_type", PlanSubType.SIMPLE)
        if sub_type_e == PlanSubType.SIMPLE:
            return "reflection_node"
        else:
            return "planner_node"

    def validate_config(self) -> bool:
        """验证 XwAgent 配置"""
        if not self.agent_config.name:
            raise ValueError(f"XwAgent '{self.name}': agent name is required")
        if not self.agent_config.graph_config or not self.agent_config.graph_config.graph_db_name:
            raise ValueError(f"XwAgent '{self.name}': graph_db_name is required in graph_config")
        return True

    def build_graph(self):
        """构建星网的异常排查agent图结构"""
        self.validate_config()

        plan_node = self.create_plan_node()
        reflection_node = self.create_reflection_node()
        worker_node = self.create_worker_node()

        builder = StateGraph(XwGraphAgentState, output_schema=XwGraphAgentOutputState)
        builder.add_node("init_history", self.init_history_node)
        builder.add_node("planner_node", plan_node)
        builder.add_node("reflection_node", reflection_node)
        builder.add_node("worker_node", worker_node)

        builder.add_edge(START, "init_history")
        builder.add_edge("init_history", "planner_node")
        builder.add_edge("planner_node", "reflection_node")
        builder.add_conditional_edges(
            "reflection_node",
            self.cycle_condition
        )

        builder.add_conditional_edges(
            "worker_node",
            self.plan_type_condition
        )

        graph = builder.compile()
        return graph

    def get_graph(self):
        if self.graph is None:
            self.graph = self.build_graph()
        return self.graph

    def build_runnable(self) -> Runnable:
        """构建 XwAgent 节点的 Runnable"""
        graph = self.get_graph()

        def agent_func(state: Dict[str, Any]) -> Dict[str, Any]:
            start_time = time.time()
            state_dict = convert_state_to_dict(state)
            try:
                result = graph.invoke(state_dict)
                output = {
                    "status": "completed",
                    "agent_result": result
                }
                execution_time = (time.time() - start_time) * 1000
                self.log_execution(ExecutionLog(
                    node_name=self.name,
                    node_type=self.node_type,
                    input_data=state_dict,
                    output_data=output,
                    execution_time_ms=execution_time
                ))
                # 将子 Agent 的输出字段直接合并到主流程状态中
                # 保留原始 state_dict，然后更新子 Agent 返回的字段
                merged_state = dict(state_dict)
                merged_state.update(result)  # 直接展开子 Agent 的输出
                merged_state[f"{self.name}_result"] = output  # 同时保留完整结果用于调试
                return merged_state
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                self.log_execution(ExecutionLog(
                    node_name=self.name,
                    node_type=self.node_type,
                    input_data=state_dict,
                    output_data={},
                    execution_time_ms=execution_time,
                    error=str(e)
                ))
                raise


        return RunnableLambda(agent_func).with_config(tags=[self.agent_name])

