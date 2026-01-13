from typing_extensions import TypedDict

from apps.models.workflow.models import PlanSubType


class GraphAgentState(TypedDict):
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


class XwGraphAgentState(GraphAgentState):
    segment_id: str
