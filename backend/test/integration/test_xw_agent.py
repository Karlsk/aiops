import json
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
    from apps.workflow.node.plan import PlannerNode
    from apps.workflow.node.reflection import ReflectionNode
    from apps.workflow.node.worker import WorkerNode
    from apps.models.workflow.models import ReflectionConfig, PlannerConfig, PlanSubType, WorkerConfig, WorkerSubType
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
    history: list
    goals: list
    worker_status: dict
    worker_result: dict
    final_answer: str
    sub_type: PlanSubType
    seq: int


def test_simple_xw_agent(sub_type: PlanSubType = PlanSubType.SIMPLE,
                         user_input: str = "故障卫星：A0015， start_time: 2025-11-25T01:04:49 ，end_time: 2025-11-25T01:05:00"):
    def init_history_node(state: MyState) -> MyState:
        state["event_name"] = "单圈次单落地星不通"
        # 由于 history 使用 Annotated[list, operator.add]，这里直接返回一个列表
        # 而不是修改 state['history']，避免重复追加
        return {
            "event_name": "单圈次单落地星不通",
            "history": [{"type": "user", "content": "联通子段 CSCN-A0007-CSCN-A0026"}],
            "sub_type": PlanSubType.SIMPLE
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

    def create_worker_node(name):
        server_configs = {
            "cscn_tool_mcp": {
                "url": "http://172.17.1.143:18000/sse",
                "transport": "sse"
            }
        }

        config = {
            "sub_type": "mcp",
            "mcp_configs": server_configs,
            "goals": [
                # 不在这里设置终止任务，让 Reflection 决定何时终止
            ],
        }
        worker_node = WorkerNode(
            name=name,
            config=config
        )
        worker_runnable = worker_node.build_runnable()
        return worker_runnable

    def print_node(state: MyState) -> MyState:
        print()
        print("=" * 60)
        print("Print Node:")
        for key, value in state.items():
            print(f"Print Node: {key}: {value}")
        print("=" * 60)
        print()
        return state

    builder = StateGraph(MyState)

    plan_node = create_plan_node("planner_vx_Sequence", sub_type)
    reflection_node = create_reflection_node("reflection_vx_Sequence", sub_type)
    worker_node = create_worker_node("worker_vx_Sequence")
    builder.add_node("init_history", init_history_node)
    builder.add_node("planner_node", plan_node)
    builder.add_node("print_plan", print_node)
    builder.add_node("worker_node", worker_node)
    builder.add_node("print_worker", print_node)
    builder.add_node("reflection_node", reflection_node)
    builder.add_node("print_reflection", print_node)

    builder.add_edge(START, "init_history")
    builder.add_edge("init_history", "planner_node")
    builder.add_edge("planner_node", "print_plan")
    builder.add_edge("print_plan", "reflection_node")
    builder.add_edge("reflection_node", "print_reflection")
    builder.add_edge("print_reflection", "worker_node")
    builder.add_edge("worker_node", "print_worker")
    builder.add_edge("print_worker", END)

    graph = builder.compile()
    print(f"Graph compiled successfully")

    result = graph.invoke({"input": user_input})
    print("=" * 60)
    print("执行结果:", result)
    print("测试完成")


def test_cycle_xw_agent(sub_type: PlanSubType = PlanSubType.SIMPLE,
                        user_input: str = "故障卫星：A0015， start_time: 2025-11-25T01:04:49 ，end_time: 2025-11-25T01:05:00"):
    def init_history_node(state: MyState) -> MyState:
        state["event_name"] = "单圈次单落地星不通"
        # 由于 history 使用 Annotated[list, operator.add]，这里直接返回一个列表
        # 而不是修改 state['history']，避免重复追加
        return {
            "event_name": "单圈次单落地星不通",
            "history": [{"type": "user", "content": "联通子段 CSCN-A0007-CSCN-A0026"}],
            "sub_type": sub_type
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

    def create_worker_node(name):
        server_configs = {
            "cscn_tool_mcp": {
                "url": "http://172.17.1.143:18000/sse",
                "transport": "sse"
            }
        }

        config = {
            "sub_type": "mcp",
            "mcp_configs": server_configs,
            "goals": [
                # 不在这里设置终止任务，让 Reflection 决定何时终止
            ],
        }
        worker_node = WorkerNode(
            name=name,
            config=config
        )
        worker_runnable = worker_node.build_runnable()
        return worker_runnable

    def print_node(state: MyState) -> MyState:
        print()
        print("=" * 60)
        print("Print Node:")
        for key, value in state.items():
            print(f"Print Node: {key}: {value}")
        print("=" * 60)
        print()
        return state

    def cycle_condition(state: MyState) -> Literal["worker_node", "__end__"]:
        # 根据 state 中的某个字段决定是否继续循环
        final_answer = state.get("final_answer", "")
        if final_answer:
            return END
        else:
            return "worker_node"
    def plan_type_condition(state: MyState) -> Literal["reflection_node", "planner_node"]:
        # 根据 sub_type 决定下一步走反思节点还是工作节点
        sub_type_e = state.get("sub_type", PlanSubType.SIMPLE)
        if sub_type_e == PlanSubType.SIMPLE:
            return "reflection_node"
        else:
            return "planner_node"


    builder = StateGraph(MyState)

    plan_node = create_plan_node("planner_vx_Cycle", sub_type)
    reflection_node = create_reflection_node("reflection_vx_Cycle", sub_type)
    worker_node = create_worker_node("worker_vx_Cycle")

    builder.add_node("init_history", init_history_node)
    builder.add_node("planner_node", plan_node)
    builder.add_node("print_plan", print_node)
    builder.add_node("worker_node", worker_node)
    builder.add_node("print_worker", print_node)
    builder.add_node("reflection_node", reflection_node)
    builder.add_node("print_reflection", print_node)

    builder.add_edge(START, "init_history")
    builder.add_edge("init_history", "planner_node")
    builder.add_edge("planner_node", "print_plan")
    builder.add_edge("print_plan", "reflection_node")
    builder.add_edge("reflection_node", "print_reflection")
    builder.add_conditional_edges(
        "print_reflection",
        cycle_condition
    )
    builder.add_edge("worker_node", "print_worker")
    builder.add_conditional_edges(
        "print_worker",
        plan_type_condition
    )

    graph = builder.compile()

    print(f"Graph compiled successfully")
    result = graph.invoke({"input": user_input})
    print("=" * 60)
    print("执行结果:", result)
    print("测试完成")



def main():
    print("开始运行 XW Agent 集成测试...")
    # test_simple_xw_agent(PlanSubType.SUPERVISION)
    test_cycle_xw_agent(PlanSubType.SUPERVISION)
    print("所有集成测试完成。")


if __name__ == "__main__":
    main()
