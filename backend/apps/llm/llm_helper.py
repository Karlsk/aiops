import os

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage

from typing import Dict, List, Optional, Any, Union
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from apps.utils.logger import TerraLogUtil
from apps.utils.utils import retry_with_backoff


class LLMHelper:
    """通用大模型调用辅助类
    
    特性:
    - 支持自定义 prompt 模板
    - 灵活的参数配置（temperature, max_tokens 等）
    - 多层级容错机制（主模型 -> 备用模型 -> 默认响应）
    - 性能监控统计
    - 支持批量处理
    """

    def __init__(
            self,
            primary_model_name: Optional[str] = None,
            backup_model_name: Optional[str] = None,
            temperature: float = 0.1,
            max_tokens: int = 2048,
            enable_timeout: bool = False,
            timeout_seconds: float = 30.0
    ):
        """初始化 LLMHelper
        
        Args:
            primary_model_name: 主模型名称，默认从配置读取
            backup_model_name: 备用模型名称，默认从配置读取
            temperature: 温度参数 (0-2)，默认 0.1
            max_tokens: 最大 token 数，默认 2048
            enable_timeout: 是否启用超时控制，默认 False
            timeout_seconds: 超时时间（秒），默认 30
        """
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enable_timeout = enable_timeout
        self.timeout_seconds = timeout_seconds
        self.parser = StrOutputParser()

        # 初始化模型
        self.primary_model = self._create_model(
            primary_model_name or os.getenv("LLM_MODEL_NAME", "gpt-4"),
            os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
            os.getenv("LLM_API_KEY", "")
        )
        self.backup_model = self._create_model(
            backup_model_name or os.getenv("BACKUP_LLM_MODEL_NAME", "gpt-3.5-turbo"),
            os.getenv("BACKUP_LLM_BASE_URL", "https://api.backup-openai.com/v1"),
            os.getenv("BACKUP_LLM_API_KEY", "")
        )

        # 性能统计
        self.performance_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0
        }

    def _create_model(
            self,
            model_name: str,
            base_url: str,
            api_key: str
    ) -> ChatOpenAI:
        """创建模型实例"""
        return ChatOpenAI(
            model_name=model_name,
            base_url=base_url,
            api_key=api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout_seconds if self.enable_timeout else None
        )

    def _build_chain(
            self,
            model: ChatOpenAI,
            prompt: Optional[ChatPromptTemplate] = None
    ) -> Runnable:
        """构建处理链
        
        Args:
            model: 要使用的模型
            prompt: 自定义 prompt 模板，如果为 None 则使用通用模板
            
        Returns:
            Runnable: LangChain 处理链
        """
        if prompt is None:
            prompt = ChatPromptTemplate.from_messages(
                [("user", "{input}")]
            )
        return prompt | model | self.parser

    def _invoke_with_fallback(
            self,
            input_data: Union[str, Dict[str, Any]],
            prompt: Optional[ChatPromptTemplate] = None,
            output_parser: Optional[Any] = None
    ) -> str:
        """带容错机制的调用
        
        Args:
            input_data: 输入数据，可以是字符串或字典
            prompt: 自定义 prompt 模板
            output_parser: 自定义输出解析器
            
        Returns:
            str: 模型响应
        """
        parser = output_parser or self.parser

        # 统一输入格式：如果是字符串，则包装为字典，适配 ChatPromptTemplate
        actual_input = input_data
        if isinstance(input_data, str):
            actual_input = {"input": input_data}

        # 第一层：尝试主模型
        try:
            TerraLogUtil.info("使用主模型处理请求")
            chain = self._build_chain(self.primary_model, prompt)
            result = chain.invoke(actual_input)
            return result
        except Exception as e:
            TerraLogUtil.warning(f"主模型失败，尝试备用模型: {e}")

        # 第二层：尝试备用模型
        try:
            TerraLogUtil.info("使用备用模型处理请求")
            chain = self._build_chain(self.backup_model, prompt)
            result = chain.invoke(actual_input)
            return result
        except Exception as e2:
            TerraLogUtil.error(f"备用模型失败: {e2}")

        # 第三层：返回默认响应
        TerraLogUtil.error("所有模型均失败，返回默认响应")
        return "抱歉，系统暂时繁忙，请稍后重试。"

    def _run_with_timeout(
            self,
            func,
            *args,
            **kwargs
    ) -> Any:
        """使用线程超时机制（兼容所有操作系统）
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            Any: 函数执行结果
            
        Raises:
            TimeoutError: 如果执行超时
        """
        if not self.enable_timeout:
            return func(*args, **kwargs)

        result = [None]
        error = [None]

        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                error[0] = e

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout=self.timeout_seconds)

        if thread.is_alive():
            raise TimeoutError(f"操作超时 ({self.timeout_seconds}秒)")

        if error[0]:
            raise error[0]

        return result[0]

    @retry_with_backoff(max_attempts=3, base_delay=1.0)
    def _invoke_with_retry(
            self,
            input_data: Union[str, Dict[str, Any]],
            prompt: Optional[ChatPromptTemplate] = None,
            output_parser: Optional[Any] = None
    ) -> str:
        """带重试机制的调用
        
        Args:
            input_data: 输入数据
            prompt: 自定义 prompt 模板
            output_parser: 自定义输出解析器
            
        Returns:
            str: 模型响应
        """
        if self.enable_timeout:
            return self._run_with_timeout(
                self._invoke_with_fallback,
                input_data,
                prompt,
                output_parser
            )
        else:
            return self._invoke_with_fallback(input_data, prompt, output_parser)

    def invoke(
            self,
            input_data: Union[str, Dict[str, Any]],
            prompt: Optional[ChatPromptTemplate] = None,
            output_parser: Optional[Any] = None,
            return_raw: bool = False,
            tools: Optional[List[Dict[str, Any]]] = None
    ) -> Union[str, Dict[str, Any]]:
        """执行单次大模型调用
        
        Args:
            input_data: 输入数据，可以是:
                - 字符串: 直接作为 prompt 输入
                - 字典: 作为 prompt 模板的变量
            prompt: 自定义 ChatPromptTemplate，如果为 None 使用通用模板
            output_parser: 自定义输出解析器，默认使用 StrOutputParser
            return_raw: 如果为 True，返回包含元数据的字典；否则仅返回响应内容
            tools: 工具定义列表（可选），如果提供则自动启用工具调用模式
            
        Returns:
            str | Dict: 根据 return_raw 参数决定
                - return_raw=False: 返回响应字符串
                - return_raw=True: 返回包含时间、状态等的字典
                
        Examples:
            # 简单调用
            response = helper.invoke("你好")
            
            # 自定义 prompt
            custom_prompt = ChatPromptTemplate.from_messages([
                ("user", "请总结以下文本: {text}")
            ])
            response = helper.invoke(
                {"text": "长文本内容..."},
                prompt=custom_prompt
            )
            
            # 带工具调用
            tools = [{"name": "get_weather", "description": "获取天气"}]
            response = helper.invoke(
                "今天天气如何？",
                tools=tools
            )
        """
        # 如果提供了 tools，则委托给工具调用方法
        if tools:
            return self.invoke_with_tools(
                input_data=input_data,
                tools=tools,
                prompt=prompt,
                output_parser=output_parser,
                return_raw=return_raw
            )

        start_time = time.time()
        self.performance_stats["total_requests"] += 1

        try:
            if isinstance(input_data, str):
                TerraLogUtil.info(f"处理请求: {input_data[:50]}...")
            else:
                TerraLogUtil.info(f"处理请求，参数数: {len(input_data)}")

            # 执行调用（带重试和超时）
            response = self._invoke_with_retry(input_data, prompt, output_parser)

            # 处理成功
            processing_time = round(time.time() - start_time, 2)
            self.performance_stats["successful_requests"] += 1
            self._update_average_response_time(processing_time)

            TerraLogUtil.info(f"处理完成，耗时: {processing_time}秒")

            if return_raw:
                return {
                    "response": response,
                    "status": "success",
                    "processing_time": processing_time
                }
            return response

        except Exception as e:
            processing_time = round(time.time() - start_time, 2)
            self.performance_stats["failed_requests"] += 1
            TerraLogUtil.error(f"处理失败: {e}")

            if return_raw:
                return {
                    "response": "系统出现异常，请重试。",
                    "status": "error",
                    "error": str(e),
                    "processing_time": processing_time
                }
            return "系统出现异常，请重试。"

    def _update_average_response_time(self, new_time: float) -> None:
        """更新平均响应时间
        
        Args:
            new_time: 新的响应时间（秒）
        """
        total_successful = self.performance_stats["successful_requests"]
        current_avg = self.performance_stats["average_response_time"]

        # 计算新的平均值
        new_avg = ((current_avg * (total_successful - 1)) + new_time) / total_successful
        self.performance_stats["average_response_time"] = round(new_avg, 2)

    def batch_invoke(
            self,
            batch_inputs: List[Union[str, Dict[str, Any]]],
            prompt: Optional[ChatPromptTemplate] = None,
            output_parser: Optional[Any] = None,
            return_raw: bool = False,
            parallel: bool = False,
            max_workers: Optional[int] = None
    ) -> List[Union[str, Dict[str, Any]]]:
        """批量处理请求
        
        Args:
            batch_inputs: 输入数据列表
            prompt: 自定义 prompt 模板
            output_parser: 自定义输出解析器
            return_raw: 是否返回包含元数据的字典
            parallel: 是否使用并行执行（默认 False 保持向后兼容）
            max_workers: 最大工作线程数，默认为 CPU 核心数的 2 倍
            
        Returns:
            List[str | Dict]: 批量结果列表，顺序与输入一致
            
        Example:
            # 顺序执行（默认）
            inputs = ["问题1", "问题2", "问题3"]
            results = helper.batch_invoke(inputs)
            
            # 并行执行（更快）
            results = helper.batch_invoke(inputs, parallel=True, max_workers=4)
        """
        TerraLogUtil.info(f"批量处理开始，请求数: {len(batch_inputs)}, 并行: {parallel}")

        if not parallel:
            # 顺序执行模式
            return self._batch_invoke_sequential(batch_inputs, prompt, output_parser, return_raw)
        else:
            # 并行执行模式
            return self._batch_invoke_parallel(batch_inputs, prompt, output_parser, return_raw, max_workers)

    def _batch_invoke_sequential(
            self,
            batch_inputs: List[Union[str, Dict[str, Any]]],
            prompt: Optional[ChatPromptTemplate],
            output_parser: Optional[Any],
            return_raw: bool
    ) -> List[Union[str, Dict[str, Any]]]:
        """顺序执行批处理（保持向后兼容）"""
        results = []

        for i, input_data in enumerate(batch_inputs, 1):
            try:
                result = self.invoke(input_data, prompt, output_parser, return_raw)
                results.append(result)
                TerraLogUtil.info(f"批次 {i}/{len(batch_inputs)} 完成")
            except Exception as e:
                TerraLogUtil.error(f"批次 {i} 处理失败: {e}")
                results.append({
                                   "response": "处理失败",
                                   "status": "error",
                                   "error": str(e)
                               } if return_raw else "处理失败")

        TerraLogUtil.info("批量处理完成")
        return results

    def _batch_invoke_parallel(
            self,
            batch_inputs: List[Union[str, Dict[str, Any]]],
            prompt: Optional[ChatPromptTemplate],
            output_parser: Optional[Any],
            return_raw: bool,
            max_workers: Optional[int] = None
    ) -> List[Union[str, Dict[str, Any]]]:
        """并行执行批处理
        
        注意：结果顺序与输入顺序保持一致，不受执行顺序影响
        """
        results = [None] * len(batch_inputs)

        # 确定工作线程数
        if max_workers is None:
            max_workers = min(10, (len(batch_inputs) + 3) // 4)  # 最多 10 个线程

        TerraLogUtil.info(f"使用 {max_workers} 个工作线程并行处理")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务，保持原始索引
            future_to_index = {
                executor.submit(
                    self.invoke,
                    input_data,
                    prompt,
                    output_parser,
                    return_raw
                ): idx
                for idx, input_data in enumerate(batch_inputs)
            }

            # 处理完成的任务
            completed = 0
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    result = future.result()
                    results[idx] = result
                    completed += 1
                    TerraLogUtil.info(f"批次 {idx + 1}/{len(batch_inputs)} 完成 ({completed}/{len(batch_inputs)})")
                except Exception as e:
                    TerraLogUtil.error(f"批次 {idx + 1} 处理失败: {e}")
                    results[idx] = {
                        "response": "处理失败",
                        "status": "error",
                        "error": str(e)
                    } if return_raw else "处理失败"

        TerraLogUtil.info("批量处理完成")
        return results

    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计信息
        
        Returns:
            Dict: 包含以下字段的统计字典:
                - total_requests: 总请求数
                - successful_requests: 成功请求数
                - failed_requests: 失败请求数
                - average_response_time: 平均响应时间（秒）
                - success_rate: 成功率（百分比）
                
        Example:
            stats = helper.get_stats()
            print(f"成功率: {stats['success_rate']}%")
        """
        stats = self.performance_stats.copy()
        if stats["total_requests"] > 0:
            stats["success_rate"] = round(
                (stats["successful_requests"] / stats["total_requests"]) * 100, 2
            )
        else:
            stats["success_rate"] = 0.0

        return stats

    def reset_stats(self) -> None:
        """重置性能统计
        
        Example:
            helper.reset_stats()
        """
        self.performance_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0
        }
        TerraLogUtil.info("性能统计已重置")

    def invoke_with_tools(
            self,
            input_data: Union[str, Dict[str, Any]],
            tools: List[Dict[str, Any]],
            prompt: Optional[ChatPromptTemplate] = None,
            output_parser: Optional[Any] = None,
            return_raw: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """支持工具调用的大模型调用方法
        
        使用 OpenAI 的原生 function_calls 機制，简洁高效地处理工具调用。
        
        Args:
            input_data: 输入数据（字符串或字典）
            tools: 工具定义列表，每个工具应包含:
                - name: 工具名称
                - description: 工具描述
                - parameters: 参数定义 (OpenAI JSON Schema 格式，可选)
            prompt: 自定义 prompt 模板（可选）
            output_parser: 自定义输出解析器（可选）
            return_raw: 是否返回原始元数据（可选）
            
        Returns:
            str | Dict: 根据 return_raw 参数决定
                - return_raw=False: 
                  * 如果没有工具调用，返回普通文本响应
                  * 如果有工具调用，返回 JSON 格式：{"tool": "工具名", "args": {...}}
                - return_raw=True: 返回包含元数据的字典
                
        Examples:
            tools = [
                {
                    "name": "get_bgp_status",
                    "description": "获取 BGP 邻居状态",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device": {"type": "string", "description": "设备名称"},
                            "neighbor_ip": {"type": "string", "description": "邻居 IP"}
                        },
                        "required": ["device", "neighbor_ip"]
                    }
                }
            ]
            
            response = helper.invoke_with_tools(
                input_data="查询BGP状态",
                tools=tools
            )
            # 返回：{"tool": "get_bgp_status", "args": {...}} 或文本回复
        """
        start_time = time.time()
        self.performance_stats["total_requests"] += 1

        try:
            # 获取用户输入
            if isinstance(input_data, str):
                user_input = input_data
            else:
                user_input = str(input_data)

            TerraLogUtil.info(f"工具调用模式: 提供了 {len(tools)} 个工具")

            # 使用 OpenAI 原生 function_calls 機制
            response = self._invoke_with_tools_and_fallback(
                user_input=user_input,
                tools=tools
            )

            # 处理成功
            processing_time = round(time.time() - start_time, 2)
            self.performance_stats["successful_requests"] += 1
            self._update_average_response_time(processing_time)

            TerraLogUtil.info(f"工具调用完成，耗时: {processing_time}秒")

            if return_raw:
                return {
                    "response": response,
                    "status": "success",
                    "processing_time": processing_time,
                    "tools_count": len(tools)
                }
            return response

        except Exception as e:
            processing_time = round(time.time() - start_time, 2)
            self.performance_stats["failed_requests"] += 1
            TerraLogUtil.error(f"工具调用失败: {e}")

            if return_raw:
                return {
                    "response": "系统出现异常，请重试。",
                    "status": "error",
                    "error": str(e),
                    "processing_time": processing_time
                }
            return "系统出现异常，请重试。"

    def _invoke_with_tools_and_fallback(
            self,
            user_input: str,
            tools: List[Dict[str, Any]]
    ) -> str:
        """使用 OpenAI function_calls 機制与容错機制调用工具
        
        具有三层容错频、重试控制:
        1. 主模型 + 原生 function_calls
        2. 备用模型 + 原生 function_calls  
        3. 默认响应
        """
        import json

        # 步骤1: 尝试主模型 + function_calls
        try:
            TerraLogUtil.info("使用主模型调用工具")
            response = self._call_with_tools(
                model=self.primary_model,
                user_input=user_input,
                tools=tools
            )
            return response
        except Exception as e:
            TerraLogUtil.warning(f"主模型失败，尝试备用模型: {e}")

        # 步骤2: 尝试备用模型 + function_calls
        try:
            TerraLogUtil.info("使用备用模型调用工具")
            response = self._call_with_tools(
                model=self.backup_model,
                user_input=user_input,
                tools=tools
            )
            return response
        except Exception as e2:
            TerraLogUtil.error(f"备用模型也失败: {e2}")

        # 步骤3: 返回默认响应
        TerraLogUtil.error("所有模型均失败，返回默认响应")
        return "抱歉，系统暂时繁忙，请稍后重试。"

    def _call_with_tools(
            self,
            model: ChatOpenAI,
            user_input: str,
            tools: List[Dict[str, Any]]
    ) -> str:
        """使用指定模型调用 function_calls
        
        使用 OpenAI 的原生 function_calls 機制。
        """
        import json

        # 步骤1: 验证工具列表，过滤掉无效的工具
        valid_tools = []
        for tool in tools:
            # 处理工具格式：
            # 方案A: {"name": "...", "description": "...", "parameters": {...}}
            # 方案B: {"type": "function", "function": {"name": "...", "description": "...", "parameters": {...}}}

            if isinstance(tool, dict) and "function" in tool and "type" in tool:
                # 方案B：已经是 OpenAI 格式
                func_info = tool.get("function", {})
                tool_name = func_info.get("name", "").strip() if isinstance(func_info.get("name"), str) else ""
                tool_desc = func_info.get("description", "").strip() if isinstance(func_info.get("description"),
                                                                                   str) else ""
                tool_params = func_info.get("parameters", {})
            else:
                # 方案A：简洁格式
                tool_name = tool.get("name", "").strip() if isinstance(tool.get("name"), str) else ""
                tool_desc = tool.get("description", "").strip() if isinstance(tool.get("description"), str) else ""
                tool_params = tool.get("parameters", {})

            # 验证工具名称不为空
            if not tool_name:
                TerraLogUtil.warning(f"跳过无效工具：工具 name 为空。工具信息: {tool}")
                continue

            # 验证description不为空
            if not tool_desc:
                tool_desc = f"调用 {tool_name} 工具"

            # 验证parameters
            if not tool_params or not isinstance(tool_params, dict):
                tool_params = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }

            # 构建有效的工具定义（OpenAI 格式）
            valid_tools.append({
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_desc,
                    "parameters": tool_params
                }
            })

        if not valid_tools:
            TerraLogUtil.warning("没有有效的工具可用")
            return "没有可用的工具"

        # 步骤2: 构建 messages
        messages = [HumanMessage(content=user_input)]

        # 步骤3: 调用模型的 bind() 方法上传 tools
        model_with_tools = model.bind(tools=valid_tools)

        # 步骤4: 调用模型
        response = model_with_tools.invoke(messages)

        # 检查是否有 tool_calls
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # 接取第一个工具调用
            tool_call = response.tool_calls[0]

            # 提取工具名称和参数
            tool_name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name", "")
            tool_args = tool_call.get("args") if isinstance(tool_call, dict) else getattr(tool_call, "args", {})

            # 构造 JSON 整数，与 OpenAI 原生一致
            result = {
                "tool": tool_name,
                "args": tool_args
            }

            TerraLogUtil.info(f"检测到工具调用: {tool_name}")
            return json.dumps(result, ensure_ascii=False)
        else:
            # 没有工具调用，返回普通文本
            text_response = response.content if hasattr(response, 'content') else str(response)
            TerraLogUtil.info("无工具调用，返回普通文本")
            return text_response


_llm_helper: Optional[LLMHelper] = None


def get_llm_helper() -> LLMHelper:
    """获取 LLMHelper 实例，首次调用时初始化（延迟初始化模式）

    这种设计避免了模块导入时的初始化，只在实际需要时创建实例。
    这对于测试环境特别重要，可以避免导入错误。
    """
    global _llm_helper
    if _llm_helper is None:
        _llm_helper = LLMHelper(
            temperature=0.1,
            max_tokens=1024,
            enable_timeout=False
        )
    return _llm_helper
