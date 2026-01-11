"""
基础节点接口和工厂函数
定义所有节点类型的统一接口，确保工业级代码质量
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_core.runnables import Runnable
from apps.models.workflow.models import (
    NodeType, ExecutionLog, OperatorLog
)


class BaseNode(ABC):
    """
    所有节点类型的基类
    定义节点的统一接口和生命周期
    """

    def __init__(
            self,
            name: str,
            node_type: NodeType,
            config: Dict[str, Any],
            operator_log: Optional[OperatorLog] = None
    ):
        """
        初始化节点

        Args:
            name: 节点名称
            node_type: 节点类型
            config: 节点配置
            operator_log: 操作符日志（记录输入输出 schema）
        """
        self.name = name
        self.node_type = node_type
        self.config = config
        self.operator_log = operator_log
        self._execution_history: list[ExecutionLog] = []

    @abstractmethod
    def build_runnable(self) -> Runnable:
        """
        构建可执行的 Runnable 对象
        每种节点类型需要实现自己的 Runnable 逻辑

        Returns:
            Runnable: LangChain 的可执行对象
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """
        验证节点配置的合法性

        Returns:
            bool: 配置是否合法

        Raises:
            ValueError: 配置不合法时抛出异常
        """
        pass

    def get_execution_history(self) -> list[ExecutionLog]:
        """获取节点的执行历史"""
        return self._execution_history.copy()

    def log_execution(self, execution_log: ExecutionLog) -> None:
        """记录一次执行日志"""
        self._execution_history.append(execution_log)

    def clear_execution_history(self) -> None:
        """清除执行历史"""
        self._execution_history.clear()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, type={self.node_type})"
