from typing import Dict, Any, Optional, List
import time
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.messages import BaseMessage
from langchain_core.prompts.chat import ChatPromptTemplate

from .base import BaseNode
from apps.models.workflow.models import NodeType, LLMConfig, ExecutionLog, OperatorLog
from apps.llm.llm_helper import get_llm_helper
from ...utils.utils import convert_state_to_dict, map_output_to_state
from apps.llm.prompt.prompt_template import get_xw_report_llm


class LLMDefaultNode(BaseNode):
    """
    LLM 节点：调用大语言模型进行推理
    支持多种 LLM 类型（OpenAI、Anthropic 等）
    """

    def __init__(
            self,
            name: str,
            config: Dict[str, Any],
            messages: Optional[List[BaseMessage]] = None,
            operator_log: Optional[OperatorLog] = None
    ):
        super().__init__(name, NodeType.LLM, config, operator_log)
        self.llm_config = LLMConfig(**config)
        self.messages = messages if messages is not None else []
        self.llm_helper = get_llm_helper()

    def validate_config(self) -> bool:
        """验证 LLM 配置"""
        pass

    def build_runnable(self) -> Runnable:
        def llm_func(state: Dict[str, Any]) -> Dict[str, Any]:
            state_dict = convert_state_to_dict(state)
            print(f"llm node input: {state_dict}")
            start_time = time.time()

            try:
                prompt_str = get_xw_report_llm(state_dict)
                question = state_dict.get("input", "")
                prompt = ChatPromptTemplate.from_messages([
                    ("system", prompt_str),
                    ("human", "{input}")
                ])
                response = self.llm_helper.invoke(question, prompt=prompt, return_raw=False)
                response_text = response.content if hasattr(response, 'content') else str(response)
                output = {
                    "response": response_text
                }
                state_dict["llm_result"] = response_text

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

        return RunnableLambda(llm_func).with_config(tags=[self.name])


