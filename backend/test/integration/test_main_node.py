from re import S
import sys
import asyncio
import operator
from pathlib import Path
from typing import Annotated, Literal
import os

from langchain_core.outputs import llm_result
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END  # LangGraph的核心类

# 添加 backend 路径到 Python 路径
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

try:
    from apps.workflow.agent.xw_agent import XwAgent
    from apps.workflow.node.llm import LLMDefaultNode
    from apps.models.workflow.models import GraphPlanAgentConfig, PlanSubType, ActionType
except ImportError as e:
    print(f"注意: 部分模块导入失败，但基础单元测试仍可运行: {e}")
    # 直接导入必要的模块
    sys.path.insert(0, os.path.join(backend_path, 'apps'))

from typing_extensions import TypedDict


class MainState(TypedDict):
    input: str
    event_name: str
    plan: str
    history: list
    final_answer: str
    segment_id: str
    llm_result: str


def test_simple_e2e(sub_type: PlanSubType = PlanSubType.SIMPLE,
                    user_input: str = "故障卫星：A0015， start_time: 2025-11-25T01:04:49 ，end_time: 2025-11-25T01:05:00"):
    def create_agent():
        config = {
            "name": "xw_agent_test",
            "run_mode": sub_type,
            "action_config": {
                "action_type": ActionType.MCP,
                "mcp_config": {
                    "cscn_tool_mcp": {
                        "url": "http://172.17.1.143:18000/sse",
                        "transport": "sse"
                    }
                }
            },
            "graph_config": {
                "graph_db_name": "xw-issue-new1",
                "api_url": "http://127.0.0.1:7082"
            }
        }
        xw_agent = XwAgent(
            name="xw_agent_node",
            config=config
        )

        agent_runnable = xw_agent.build_runnable()
        return agent_runnable

    def create_llm_node():
        config = {}

        llm_default = LLMDefaultNode(
            name="xw_llm_node",
            config=config
        )
        llm_runnable = llm_default.build_runnable()

        return llm_runnable

    def init_node(state: MainState) -> MainState:
        return {
            "input": state["input"],
            "event_name": "单圈次单落地星不通",
            "segment_id": "CSCN-A0007-CSCN-A0026",
        }

    agent_node = create_agent()

    llm_node = create_llm_node()

    builder = StateGraph(MainState)
    builder.add_node("agent_node", agent_node)
    builder.add_node("llm_node", llm_node)
    builder.add_node("init_node", init_node)

    builder.add_edge(START, "init_node")
    builder.add_edge("init_node", "agent_node")
    builder.add_edge("agent_node", "llm_node")
    builder.add_edge("llm_node", END)

    graph = builder.compile()

    print("Graph compiled successfully")
    res = graph.invoke({"input": user_input})
    markdown_str = res.get("llm_result")
    print(markdown_str)
    from rich.console import Console
    from rich.markdown import Markdown

    console = Console()
    md = Markdown(markdown_str)
    console.print(md)


def main():
    test_simple_e2e(PlanSubType.SUPERVISION)


if __name__ == "__main__":
    main()
