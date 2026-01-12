"""
plan and reflection Node 集成测试
验证 planNode and reflectionNode langgraph 的正确性
"""

import sys
import asyncio
import operator
from pathlib import Path
from typing import Annotated
import os

from typing_extensions import TypedDict

# 添加 backend 路径到 Python 路径
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

try:
    from apps.workflow.node.plan import PlannerNode
    from apps.workflow.node.reflection import ReflectionNode
    from apps.models.workflow.models import ReflectionConfig, PlannerConfig, PlanSubType
except ImportError as e:
    print(f"注意: 部分模块导入失败，但基础单元测试仍可运行: {e}")
    # 直接导入必要的模块
    sys.path.insert(0, os.path.join(backend_path, 'apps'))
    from workflow.node.plan import PlannerNode
    from workflow.node.reflection import ReflectionNode
    from models.workflow.models import ReflectionConfig, PlannerConfig, PlanSubType


class MyState(TypedDict):
    input: str
    event_name: str
    plan: str
    context: str
    history: Annotated[list, operator.add]
    goals: Annotated[list, operator.add]
    worker_status: dict
    worker_result: dict


def test_simple_node_e2e():
    """
    测试 PlannerNode 的端到端功能
    """
    sub_type = PlanSubType.SIMPLE
    plan_config = {
        "sub_type": sub_type,
        "graph_db_name": "xw-issue-new1",
        "api_url": "http://127.0.0.1:7082"
    }
    planner_node = PlannerNode(
        name="test_simple_node",
        config=plan_config
    )

    # 4. 构建 Runnable
    plan_runnable = planner_node.build_runnable()

    user_input = "故障卫星：A0015， start_time: 2025-11-25T01:04:49 ，end_time: 2025-11-25T01:05:00"
    state = MyState(
        input=user_input,
        event_name="单圈次单落地星不通",
        context="故障诊断工作流",
        history=[{"type": "user", "content": "联通子段 CSCN-A0007-CSCN-A0026"}],  # 初始空历史
        goals=[],
        worker_status={},
        worker_result={}
    )

    # 5. 运行 Runnable
    plan_res = plan_runnable.invoke(state)
    print("=" * 50)
    print("PlannerNode 结果:")
    for key, value in plan_res.items():
        print(f"{key}: {value}")
    print("=" * 50)

    reflection_config = {
        "sub_type": sub_type,
    }

    reflection_node = ReflectionNode(
        name="test_reflection_node",
        config=reflection_config
    )
    # 4. 构建 Runnable
    reflection_runnable = reflection_node.build_runnable()
    # 5. 运行 Runnable
    reflection_res = reflection_runnable.invoke(plan_res)
    print("=" * 50)
    print("ReflectionNode 结果:")
    for key, value in reflection_res.items():
        print(f"{key}: {value}")
    print("=" * 50)


def test_supervision_node_e2e():
    """
        测试 PlannerNode 的端到端功能
        """
    sub_type = PlanSubType.SUPERVISION
    plan_config = {
        "sub_type": sub_type,
        "graph_db_name": "xw-issue-new1",
        "api_url": "http://127.0.0.1:7082"
    }
    planner_node = PlannerNode(
        name="test_simple_node",
        config=plan_config
    )

    # 4. 构建 Runnable
    plan_runnable = planner_node.build_runnable()

    user_input = "故障卫星：A0015， start_time: 2025-11-25T01:04:49 ，end_time: 2025-11-25T01:05:00"
    state = MyState(
        input=user_input,
        event_name="单圈次单落地星不通",
        context="故障诊断工作流",
        history=[{"type": "user", "content": "联通子段 CSCN-A0007-CSCN-A0026"}],  # 初始空历史
        goals=[],
        worker_status={},
        worker_result={}
    )

    # 5. 运行 Runnable
    plan_res = plan_runnable.invoke(state)
    print("=" * 50)
    print("PlannerNode 结果:")
    for key, value in plan_res.items():
        print(f"{key}: {value}")
    print("=" * 50)

    reflection_config = {
        "sub_type": sub_type,
    }

    reflection_node = ReflectionNode(
        name="test_reflection_node",
        config=reflection_config
    )
    # 4. 构建 Runnable
    reflection_runnable = reflection_node.build_runnable()
    # 5. 运行 Runnable
    reflection_res = reflection_runnable.invoke(plan_res)
    print("=" * 50)
    print("ReflectionNode 结果:")
    for key, value in reflection_res.items():
        print(f"{key}: {value}")
    print("=" * 50)

def run_e2e_by_langgraph(sub_type: PlanSubType = PlanSubType.SIMPLE):
    def init_history_node(state: MyState) -> MyState:
        state["event_name"] = "单圈次单落地星不通"
        # 由于 history 使用 Annotated[list, operator.add]，这里直接返回一个列表
        # 而不是修改 state['history']，避免重复追加
        return {
            "event_name": "单圈次单落地星不通",
            "history": [{"type": "user", "content": "联通子段 CSCN-A0007-CSCN-A0026"}]
        }

    def create_plan_node(name, sub_type):
        config = {
            "sub_type": sub_type,
            "graph_db_name": "xw-issue-new1",
            "api_url": "http://127.0.0.1:7082"
        }

        planner_node = PlannerNode(
            name=name,
            config=config
        )
        plan_runnable = planner_node.build_runnable()
        return plan_runnable

    def create_reflection_node(name, sub_type):
        config = {
            "sub_type": sub_type,
        }
        reflection_node = ReflectionNode(
            name=name,
            config=config
        )
        reflection_runnable = reflection_node.build_runnable()
        return reflection_runnable

    def print_node(state: MyState) -> MyState:
        print("=" * 60)
        print("Print Node:")
        for key, value in state.items():
            print(f"Print Node: {key}: {value}")
        print("=" * 60)
        return state

    from langgraph.graph import StateGraph, START, END  # LangGraph的核心类

    builder = StateGraph(MyState)

    plan_node = create_plan_node("planner_node_e2e", sub_type)
    reflection_node = create_reflection_node("reflection_node_e2e", sub_type)

    builder.add_node("init_history", init_history_node)
    builder.add_node("planner_node", plan_node)
    builder.add_node("print_plan", print_node)
    builder.add_node("reflection_node", reflection_node)
    builder.add_node("print_reflection", print_node)

    builder.add_edge(START, "init_history")
    builder.add_edge("init_history", "planner_node")
    builder.add_edge("planner_node", "print_plan")
    builder.add_edge("print_plan", "reflection_node")
    builder.add_edge("reflection_node", "print_reflection")
    builder.add_edge("print_reflection", END)

    graph = builder.compile()
    print(f"Graph compiled successfully")
    user_input = "故障卫星：A0015， start_time: 2025-11-25T01:04:49 ，end_time: 2025-11-25T01:05:00"

    result = graph.invoke({"input": user_input})
    print("=" * 60)
    print("执行结果:", result)
    print("测试完成")
def run_all_tests():
    print("开始运行所有集成测试...")
    # test_simple_node_e2e()
    # print("简单 PlannerNode 集成测试完成。")
    run_e2e_by_langgraph(PlanSubType.SIMPLE)
    print("所有集成测试已完成。")


if __name__ == "__main__":
    run_all_tests()
