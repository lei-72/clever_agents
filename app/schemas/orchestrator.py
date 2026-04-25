"""编排层请求与响应模型（Phase 3 MVP）。"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.grading import GradingRequest, GradingResponse
from app.schemas.interview import InterviewStartRequest, InterviewStartResponse
from app.schemas.qa import QAResponse
from app.schemas.resume import ResumeReviewRequest, ResumeReviewResponse


class IntentLabel(str, Enum):
    """编排层支持的最小意图集合。

    说明：当前为 Phase 3 MVP 标签集，后续可按分类器能力扩展。
    """

    QA = "qa"
    GRADING = "grading"
    RESUME = "resume"
    INTERVIEW = "interview"
    UNKNOWN = "unknown"


class AgentName(str, Enum):
    """可被编排层选择的 Agent 标识。"""

    QA_AGENT = "qa_agent"
    GRADING_AGENT = "grading_agent"
    RESUME_AGENT = "resume_agent"
    INTERVIEW_AGENT = "interview_agent"
    FALLBACK_AGENT = "fallback_agent"


class OrchestratorRequest(BaseModel):
    """统一编排请求。"""

    query: str = Field(..., min_length=1, description="用户输入内容。")
    user_id: str | None = Field(default=None, description="调用方用户标识。")
    session_id: str | None = Field(default=None, description="会话标识。")


class OrchestratorRouteResult(BaseModel):
    """编排路由结果。"""

    intent: IntentLabel
    agent: AgentName
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field(..., description="路由原因说明。")


class OrchestratorRouteResponse(BaseModel):
    """同步路由响应。"""

    route: OrchestratorRouteResult
    message: str = Field(default="routed")


class OrchestratorExecuteResponse(BaseModel):
    """编排执行响应。"""

    route: OrchestratorRouteResult
    qa_result: QAResponse | None = None
    grading_result: GradingResponse | None = None
    interview_result: InterviewStartResponse | None = None
    message: str = Field(default="executed")


class OrchestratorExecuteRequest(OrchestratorRequest):
    """编排执行请求（支持附带 Agent 业务载荷）。"""

    grading_payload: GradingRequest | None = None
    interview_payload: InterviewStartRequest | None = None


class SseEventType(str, Enum):
    """SSE 事件类型。

    协议约定：
    - route: 路由决策
    - delta: 增量内容
    - done: 流结束
    - error: 错误信息
    """

    ROUTE = "route"
    DELTA = "delta"
    DONE = "done"
    ERROR = "error"


class SseEnvelope(BaseModel):
    """统一 SSE 事件包结构。

    前后端统一结构：{"event": "...", "data": {...}}
    """

    event: SseEventType
    data: dict[str, object]


class PipelineType(str, Enum):
    """预置流水线类型。"""

    JOB_COACHING = "job_coaching"
    CODING_COACHING = "coding_coaching"
    AUTO = "auto"


class TaskStatus(str, Enum):
    """任务状态。"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineTaskName(str, Enum):
    """流水线原子任务名称。"""

    RESUME_REVIEW = "resume_review"
    INTERVIEW_SIMULATION = "interview_simulation"
    CAREER_QA = "career_qa"
    OFFER_ANALYSIS = "offer_analysis"
    CODING_INTENT_PARSE = "coding_intent_parse"
    CODE_GRADING = "code_grading"
    BUG_FIX_QA = "bug_fix_qa"
    KNOWLEDGE_EXPLAIN = "knowledge_explain"
    OPTIMIZATION_QA = "optimization_qa"


class PipelineTaskSpec(BaseModel):
    """任务拆解结果。"""

    name: PipelineTaskName
    agent: AgentName
    order: int = Field(..., ge=1)
    reason: str = Field(..., min_length=1)
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class PipelineNodeTrace(BaseModel):
    """节点级可观测追踪。"""

    node_id: str
    task: PipelineTaskName
    agent: AgentName
    status: TaskStatus
    elapsed_ms: int = Field(..., ge=0)
    input_preview: dict[str, object] = Field(default_factory=dict)
    output_preview: dict[str, object] = Field(default_factory=dict)
    error_message: str | None = None


class PipelineTrace(BaseModel):
    """全链路追踪信息。"""

    pipeline_id: str
    started_at: str
    finished_at: str
    total_elapsed_ms: int = Field(..., ge=0)
    status: TaskStatus
    nodes: list[PipelineNodeTrace] = Field(default_factory=list)


class UnifiedResultItem(BaseModel):
    """归一化后的标准结果项。"""

    task: PipelineTaskName
    title: str
    summary: str
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    source_agent: AgentName
    tags: list[str] = Field(default_factory=list)
    payload: dict[str, object] = Field(default_factory=dict)


class UnifiedPipelineOutput(BaseModel):
    """统一风格输出。"""

    style: str = Field(default="unified-v1")
    viewpoint: str = Field(default="assistant")
    highlights: list[str] = Field(default_factory=list)
    action_plan: list[str] = Field(default_factory=list)
    result_items: list[UnifiedResultItem] = Field(default_factory=list)
    final_message: str


class OrchestratorPipelineRequest(OrchestratorRequest):
    """多 Agent 流水线请求。"""

    pipeline_type: PipelineType = Field(default=PipelineType.AUTO)
    resume_payload: ResumeReviewRequest | None = None
    interview_payload: InterviewStartRequest | None = None
    grading_payload: GradingRequest | None = None
    expect_trace: bool = Field(default=True, description="是否返回可观测链路追踪。")


class OrchestratorPipelineResponse(BaseModel):
    """多 Agent 流水线响应。"""

    pipeline_type: PipelineType
    inferred_intents: list[IntentLabel] = Field(default_factory=list)
    tasks: list[PipelineTaskSpec] = Field(default_factory=list)
    unified_output: UnifiedPipelineOutput
    trace: PipelineTrace | None = None
    message: str = Field(default="pipeline_executed")
