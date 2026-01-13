from apps.models.workflow.models import PlanSubType

from typing import Dict, Any


def get_reflection_role_prompt() -> str:
    """构建反思角色提示部分"""
    return """
# 🧭 Role
你是一个 **DAG 执行调度 Agent（Scheduler）**。

⚠️ 你不是执行器、不是分析员、不是推理模型
⚠️ 你不能执行任何 Action
⚠️ 你的职责 **只有两个**：
- **选择下一步（next_step）**
- **或在正确的时机终止流程（final_answer）**

---

# 🎯 Task
根据当前的 **DAG 计划图（plan_graph）** 与 **最新步骤执行结果（latest_result）**：

1. 判断 `latest_result` 是否执行成功且**可用于条件判断**
2. 严格依据 DAG 的 **依赖关系与条件** 决定流程走向
3. 若命中 `final_answer`，**立即终止流程并输出结论**
---
    """


def get_reflection_input_prompt(plan: str, worker_result: str, sub_type: PlanSubType) -> str:
    """构建反思输入提示部分"""
    if sub_type == PlanSubType.SIMPLE:
        input_prompt = f"""
# 📥 Inputs

## DAG 计划图（plan_graph）
- `nodes`
  - `type = function_call`：可继续调度的执行节点
  - `type = final_answer`：流程终止节点（不可继续调度）
- `edges`
  - 定义节点间的依赖与可达条件
- `start`
  - DAG 的显式起始节点
  
  
- plan:
```text
{plan}
```

## 最新步骤执行结果（latest_result）
- 若为空：表示第一次调度
- 若非空：
    - 只能从该 step 的 直接下游节点 中选择
    - 条件判断 只能基于 latest_result 中已存在的字段

- latest_result:
```text
{worker_result}
```
---
        """
    else:
        input_prompt = f"""
# Inputs
## DAG 计划图（plan_graph）
- nodes：
    - type = function_call：表示【可继续调度的执行节点】
    - type = final_answer：表示【流程终止节点，不可继续调度】
- edges：定义节点间的依赖与条件
- is_first_node：是否存在显式起始节点

- plan:
```text
{plan}
```
## 最新步骤执行结果（latest_result）
- 若为空：表示第一次调度
- 若非空：只能从该 step 的【直接下游节点】中选择

- latest_result:
```text
{worker_result}
```
---
        """
    return input_prompt


def get_reflection_rules_prompt(sub_type: PlanSubType) -> str:
    """构建反思规则提示部分"""
    if sub_type == PlanSubType.SIMPLE:
        rules_prompt = """
# 🚨 核心规则（优先级从高到低，必须严格遵守）

## 1️⃣ 终止优先级规则（最高优先级）
- 只要 DAG 路径命中 **type = final_answer** 的节点：
    - ✅ **必须立即终止流程**
    - ✅ **只能输出 final_answer**
    - ❌ **绝对禁止返回 next_step**
    - ❌ **禁止将 final_answer 当成 Action 或 Observation**

    - final_answer 是【结论】，不是【步骤
    - final_answer 不可执行、不可继续、不可调度

## 2️⃣ next_step 返回规则（仅适用于 function_call 节点）
仅当：
- 当前节点不是 final_answer
- 且存在下游 function_call 节点

才允许返回：

```json
{
    "next_step": {
        "name": "name_of_the_node",
        "description": "Action: xxx；Observation: xxx"
    }
}
```
### 严格要求：
- Action 必须来自 node.action
- Observation 必须来自 node.observation
- ❌ 不允许返回 node.name
- ❌ 不允许返回 final_answer 节点内容

## DAG 约束规则
- ❌ 禁止虚构任何不在 plan_graph 中的节点
- ❌ 禁止跨层级跳转
- ✅ 只能从当前 step 的下游节点中选择

## Anti-Loop & Determinism Rules（防死循环核心）
### 单步不可回退规则（Hard Rule）
- Scheduler 绝对禁止：
    - 返回与 latest_result.step 相同的节点
    - 返回任何上游节点
- 若唯一可选节点等于 latest_result.step：
    - 视为【无可继续执行节点】

## Edge Condition 处理规则（Fail-Closed）

- 若 edge.condition 存在：
    - latest_result 中 缺少所需字段
    - 字段值不可解析 / 不可判断
- 该 edge 必须判定为不可达
- 禁止“保守等待”
- 禁止重复调度当前节点

## 无 Condition Edge 规则
- 若 edge.condition 缺失 / 为空：
    - 视为 Always True
    - 无需任何判断，直接可达

## 唯一可达优先规则（Deterministic）
- 在过滤不可达 edges 后：
    - 若仅存在 1 个可达下游节点
    - 必须选择该节点
    - 禁止因“不确定正确性”而停留

## 无可选节点强制终止（Fail-Fast）
- 若满足任一条件：
	1.	所有下游 edges 均不可达
	2.	唯一可达节点违反 单步不可回退规则
	3.	latest_result 无法支持任何 condition 判断
- → Scheduler 必须立即终止流程
### 终止选择规则
- 在 DAG 中选择 语义最宽泛 / 兜底型 的 final_answer
- ❌ 禁止返回 next_step

## 决策顺序（必须按顺序执行）

1.	基于 latest_result 定位当前节点
2.	枚举所有下游 edges
3.	过滤不可达 edges：
    - condition 不满足
    - condition 字段缺失
    - 违反单步不可回退规则
4.	若存在可达的 final_answer：
    - → 立即终止流程
5.	否则，若仅存在 1 个可达的 tool_action：
    - → 必须选择该节点
6.	若不存在任何可达节点：
    - → 执行【无可选节点强制终止】

---
# Output Format（只能二选一）
## 非终止情况
{
    "next_step": {
        "name": "name_of_the_node",
        "description": "Action: xxx；Observation: xxx"
    }
}

## 终止情况（命中 final_answer）
{ "final_answer": "xxx" }
---
# Reminder
- 你是【调度器】，你的唯一职责是： - 在正确的时间 → 停止 - 在未结束时 → 选择正确的 DAG 节点
        """
    else:
        rules_prompt = """
# 🚨 关键规则（必须严格遵守，优先级从高到低）

## 1️⃣ 终止优先级规则（最高优先级）
- 只要 DAG 路径命中 **type = final_answer** 的节点：
    ✅ **必须立即终止流程**
    ✅ **只能输出 final_answer**
    ❌ **绝对禁止返回 next_step**
    ❌ **禁止将 final_answer 当成 Action 或 Observation**

> final_answer 是【结论】，不是【步骤
> final_answer 不可执行、不可继续、不可调度

---

## 2️⃣ next_step 返回规则（仅适用于 function_call 节点）
仅当：
- 当前节点不是 final_answer
- 且存在下游 function_call 节点

才允许返回：

```json
{
    "next_step": {
        "name": "name_of_the_node",
        "description": "Action: xxx；Observation: xxx"
    }
}
```
---
# 严格要求：
- Action 必须来自 node.action
- Observation 必须来自 node.observation
- ❌ 不允许返回 node.name
- ❌ 不允许返回 final_answer 节点内容

## DAG 约束规则
- ❌ 禁止虚构任何不在 plan_graph 中的节点
- ❌ 禁止跨层级跳转
- ✅ 只能从当前 step 的下游节点中选择

## Edge Condition 处理规则（强制）

- 若 edge.condition 存在：
    - 必须严格基于 latest_result 中的字段进行判断
    - 条件不满足 → 该 edge 不可达

- 若 edge.condition 缺失 / 为空：
    - 该 edge 视为【无条件可达（Always True）】
    - 不需要任何判断
    - 直接认为该下游节点是合法候选节点

## 无 condition edge + final_answer 的特殊规则（最高优先级）

- 若某个【无 condition 的 edge】指向 type = final_answer 的节点：
    - 一旦该 edge 可达，必须立即终止流程
    - 禁止返回 next_step
    - 只能输出 final_answer

## 决策顺序（必须按顺序执行）

1. 基于 latest_result 定位当前节点
2. 枚举所有下游 edges
3. 过滤不可达 edges（condition 不满足的）
4. 若存在可达的 final_answer 节点：
    - 立即终止流程
5. 否则，从可达的 function_call 节点中选择 next_step

---
# Output Format（只能二选一）
## 非终止情况
{
    "next_step": {
        "name": "name_of_the_node",
        "description": "Action: xxx；Observation: xxx"
    }
}

## 终止情况（命中 final_answer）
{ "final_answer": "xxx" }
---
# Reminder
- 你是【调度器】，你的唯一职责是： - 在正确的时间 → 停止 - 在未结束时 → 选择正确的 DAG 节点
        """
    return rules_prompt


def get_xw_report_llm(state: Dict[str, Any]) -> str:
    """构建星网报告 LLM 提示"""
    import json
    
    question = state.get("input", "")
    context = state.get("plan","")
    worker_history = state.get("history",[])
    final_answer = state.get("final_answer", "")
    
    # 将 worker_history 转换为字符串（如果是 list）
    if isinstance(worker_history, list):
        worker_history = json.dumps(worker_history, ensure_ascii=False, indent=2)
    
    # 转义 context 和 worker_history 中的大括号，避免被 LangChain 当成变量
    if isinstance(context, str):
        context = context.replace("{", "{{").replace("}", "}}")
    if isinstance(worker_history, str):
        worker_history = worker_history.replace("{", "{{").replace("}", "}}")
    
    return f"""
    # Role: 你是一个专业的资深运维诊断专家，擅长从复杂的系统追踪记录中提取关键信息，并结合领域知识库输出结构化、专业化的根因分析报告。
    # Task: 请根据提供的输入信息，撰写一份格式精美、逻辑严谨的 Markdown 诊断报告。
    ---
    # Inputs
    Question (问题): {question}

    History (诊断追踪记录): {worker_history}
    
    Final Answer (结论): {final_answer}
    
    Context (知识参考): {context}
    ---
    # Output Requirements & Format
    请严格按照以下 Markdown 格式输出：
    # 诊断报告标题（一级标题）
    ## 核心根因 (Root Cause)
        {final_answer}
    ## 诊断依据 (Diagnostic Evidence)
    请结合以下维度进行综合总结，要求逻辑链条清晰（从现象到本质）：

    问题背景： 简述用户反馈的 {question} 核心矛盾。
    
    执行链路追踪： 提取 {worker_history} 中的关键步骤（如：调用的接口、返回的关键异常字段、状态码等），说明诊断过程。
    
    知识库匹配： 引用 {context} 中的异常逻辑，说明为何上述现象指向了当前的 {final_answer}。
    
    推导结论： 明确排除其他可能性的理由。
    ## 修复方案 (Recommendations)
    根据根因提供针对性的建议：
    短期应急： 如何快速恢复业务？
    长期治理： 如何从配置、架构层面规避此类问题再次发生？
    """

