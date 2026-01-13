from typing import Dict, Any, Optional
import time
import json
from langchain_core.runnables import Runnable, RunnableLambda
from typing_extensions import TypedDict

from .base import BaseNode
from apps.models.workflow.models import NodeType
from apps.models.workflow.models import PlannerConfig, ExecutionLog, OperatorLog
from apps.workflow.agent.game_react.goal import Goal
from apps.utils.utils import convert_state_to_dict, generate_plan_json, map_output_to_state
from apps.utils.logger import TerraLogUtil


class PlannerNode(BaseNode):
    """
    Planner 节点：基于 LangGraph 的规划工作流
    配置包含：图数据库名称和事件名称
    """

    def __init__(
            self,
            name: str,
            config: Dict[str, Any],
            operator_log: Optional[OperatorLog] = None
    ):
        super().__init__(name, NodeType.Planner, config, operator_log)
        self.planner_config = PlannerConfig(**config) if isinstance(config, dict) else config

    def validate_config(self) -> bool:
        """验证 Planner 配置"""
        if not self.planner_config.graph_db_name:
            raise ValueError(f"Planner '{self.name}': graph_db_name is required")
        # if not self.planner_config.event_name:
        #     raise ValueError(f"Planner '{self.name}': event_name is required")
        return True

    def build_runnable(self) -> Runnable:
        """构建 Planner 节点的 Runnable"""
        self.validate_config()

        def planner_func(state: Dict[str, Any]) -> Dict[str, Any]:
            """
            执行规划逻辑
            调用 generate_plan_json 获取 JSON 格式的 Plan Schema
            generate_plan_json 通过调用 FastAPI 接口 GET /api/v1/neo4j/json来获取数据
            """
            state_dict = convert_state_to_dict(state)

            start_time = time.time()

            try:
                event_name = state.get("event_name", "")
                if not event_name:
                    raise ValueError("event_name is required in state for PlannerNode")
                goals = state.get("goals", [])
                if self.planner_config.sub_type == "supervision" and goals:
                    goal = goals[-1]
                    if isinstance(goal, Goal):
                        step = goal.name
                    elif isinstance(goal, dict):
                        step = goal.get("name", event_name)
                    else:
                        step = str(goal)
                else:
                    step = event_name
                TerraLogUtil.info("PlannerNode step: %s", step)

                api_url = self.planner_config.api_url
                database = self.planner_config.graph_db_name
                sub_type = self.planner_config.sub_type
                json_data = generate_plan_json(step, database=database, sub_type=sub_type, base_url=api_url)
                # 转换为 JSON 字符串
                plan_json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
                output = {
                    "plan": plan_json_str,
                    "status": "planned"
                }

                execution_time = (time.time() - start_time) * 1000
                self.log_execution(ExecutionLog(
                    node_name=self.name,
                    node_type=self.node_type,
                    input_data=state_dict,
                    output_data=output,
                    execution_time_ms=execution_time
                ))

                state_dict["plan"] = plan_json_str
                # 使用 map_output_to_state 将输出映射到状态更新
                # 采用 Dify 风格，为输出添加 {node_name}_result 字段
                return map_output_to_state(self.name, output, state_dict)

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

        return RunnableLambda(planner_func).with_config(tags=[self.name])
