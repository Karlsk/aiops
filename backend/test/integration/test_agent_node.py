import sys
import asyncio
import operator
from pathlib import Path
from typing import Annotated, Literal
import os

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END  # LangGraph的核心类

# 添加 backend 路径到 Python 路径
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

try:
    from apps.workflow.agent.xw_agent import XwAgent
    from apps.models.workflow.models import GraphPlanAgentConfig, PlanSubType, ActionType
except ImportError as e:
    print(f"注意: 部分模块导入失败，但基础单元测试仍可运行: {e}")
    # 直接导入必要的模块
    sys.path.insert(0, os.path.join(backend_path, 'apps'))
    from workflow.node.plan import PlannerNode
    from workflow.node.reflection import ReflectionNode
    from models.workflow.models import ReflectionConfig, PlannerConfig, PlanSubType


def test_e2e_agent(sub_type: PlanSubType = PlanSubType.SIMPLE,
                   user_input: str = "故障卫星：A0015， start_time: 2025-11-25T01:04:49 ，end_time: 2025-11-25T01:05:00"):
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

    input = {
        "input": user_input,
        "event_name": "单圈次单落地星不通",
        "segment_id": "CSCN-A0007-CSCN-A0026"
    }

    print("Running XwAgent with input:", input)
    output = agent_runnable.invoke(input)
    print()
    print("=" * 60)
    print("XwAgent output:", output)
    print("=" * 60)


def main():
    test_e2e_agent(sub_type=PlanSubType.SIMPLE)
    # test_e2e_agent(sub_type=PlanSubType.SUPERVISION)

if __name__ == "__main__":
    main()