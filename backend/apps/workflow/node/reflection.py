from typing import Dict, Any, Optional
import time
import json

from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.prompts import ChatPromptTemplate

from .base import BaseNode
from apps.models.workflow.models import NodeType
from apps.models.workflow.models import ReflectionConfig, ExecutionLog, OperatorLog, PlanSubType
from apps.utils.utils import convert_state_to_dict, map_output_to_state, extract_json_block
from apps.llm.llm_helper import _get_llm_helper
from apps.llm.prompt.prompt_template import get_reflection_rules_prompt, get_reflection_role_prompt, \
    get_reflection_input_prompt

from apps.utils.logger import TerraLogUtil


class ReflectionNode(BaseNode):
    """
    Reflection 节点：反思工作流
    配置包含可选的 RAG 配置
    """

    def __init__(self, name: str, config: Dict[str, Any], operator_log: Optional[OperatorLog] = None):
        super().__init__(name, NodeType.Reflection, config, operator_log)
        self.reflection_config = ReflectionConfig(**config)
        self.llm_helper = _get_llm_helper()

    def validate_config(self) -> bool:
        """验证 Reflection 配置"""
        # Reflection 的 RAG 配置是可选的，所以这里不做强制检查
        return True

    def build_runnable(self) -> Runnable:
        """构建 Reflection 节点的 Runnable"""
        self.validate_config()

        def reflection_func(state: Dict[str, Any]) -> Dict[str, Any]:
            state_dict = convert_state_to_dict(state)

            start_time = time.time()

            try:
                # 1. 从状态中获取必要的数据
                plan = state_dict.get("plan", "")
                worker_result = state_dict.get("worker_result", "")
                question = state_dict.get("input", "")
                # 2. 构建系统 prompt
                plan_sub_type = self.reflection_config.sub_type if self.reflection_config.sub_type else PlanSubType.SIMPLE
                full_prompt = get_reflection_role_prompt()
                full_prompt += get_reflection_input_prompt(plan, worker_result, plan_sub_type)
                full_prompt += get_reflection_rules_prompt(plan_sub_type)

                # 4. 调用 LLM
                # 转义 full_prompt 中的大括号，避免被 LangChain 误认为是变量
                safe_full_prompt = full_prompt.replace("{", "{{").replace("}", "}}")
                prompt = ChatPromptTemplate.from_messages([
                    ("system", safe_full_prompt),
                    ("human", "{input}")
                ])
                # TerraLogUtil.info("ReflectionNode invoking LLM with prompt: %s", safe_full_prompt)
                response = self.llm_helper.invoke(question, prompt=prompt, return_raw=False)

                # 5. 解析响应
                response_text = response.content if hasattr(response, 'content') else str(response)

                # 尝试提取 JSON
                json_text = extract_json_block(response_text)
                if json_text:
                    result_dict = json.loads(json_text)
                else:
                    result_dict = {}

                output = {
                    "status": "reflected",
                    "reflection_result": result_dict,
                }
                for key, value in result_dict.items():
                    if key == "next_step":
                        if isinstance(value, str):
                            state_dict["goals"] = [{
                                "name": value,
                                "description": ""
                            }]
                        elif isinstance(value, dict):
                            state_dict["goals"] = [value]
                        else:
                            raise ValueError("next_step must be a string or a dict")
                    else:
                        state_dict["final_answer"] = value

                execution_time = (time.time() - start_time) * 1000
                self.log_execution(ExecutionLog(
                    node_name=self.name,
                    node_type=self.node_type,
                    input_data=state_dict,
                    output_data=output,
                    execution_time_ms=execution_time
                ))

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

        return RunnableLambda(reflection_func).with_config(tags=[self.name])
