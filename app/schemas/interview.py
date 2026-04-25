"""Interview Agent 请求与响应模型。"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class InterviewStage(str, Enum):
    """面试阶段。"""

    INTRO = "intro"
    TECH = "tech"
    PROJECT = "project"
    REPORT = "report"


class InterviewStatus(str, Enum):
    """面试会话状态。"""

    RUNNING = "running"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"


class QuestionSource(str, Enum):
    """题目来源类型。"""

    RESUME = "resume"
    HISTORY = "history"
    WEAKNESS = "weakness"
    GENERAL = "general"


class InterviewQuestion(BaseModel):
    """结构化面试题。"""

    question_id: str = Field(..., min_length=1)
    stage: InterviewStage
    content: str = Field(..., min_length=1)
    source: QuestionSource = Field(default=QuestionSource.GENERAL)
    knowledge_tags: list[str] = Field(default_factory=list)
    difficulty: int = Field(default=2, ge=1, le=5)
    follow_up_to: str | None = None


class InterviewAnswerTurn(BaseModel):
    """单轮问答。"""

    question: InterviewQuestion
    answer: str = Field(..., min_length=1)


class InterviewScoreBreakdown(BaseModel):
    """独立评分链路分项。"""

    technical_depth: float = Field(default=0.0, ge=0.0, le=100.0)
    problem_solving: float = Field(default=0.0, ge=0.0, le=100.0)
    system_design: float = Field(default=0.0, ge=0.0, le=100.0)
    communication_clarity: float = Field(default=0.0, ge=0.0, le=100.0)
    structure_expression: float = Field(default=0.0, ge=0.0, le=100.0)
    collaboration_signal: float = Field(default=0.0, ge=0.0, le=100.0)


class InterviewStageScore(BaseModel):
    """阶段评分。"""

    stage: InterviewStage
    technical_score: float = Field(..., ge=0.0, le=100.0)
    communication_score: float = Field(..., ge=0.0, le=100.0)


class InterviewAssessmentPoint(BaseModel):
    """实时评估打点。"""

    question_id: str
    stage: InterviewStage
    technical_score: float = Field(..., ge=0.0, le=100.0)
    communication_score: float = Field(..., ge=0.0, le=100.0)
    weak_tags: list[str] = Field(default_factory=list)
    summary: str = Field(..., min_length=1)


class InterviewRadarChartData(BaseModel):
    """能力雷达图结构化数据。"""

    indicators: list[str] = Field(default_factory=list)
    values: list[float] = Field(default_factory=list)
    max_value: float = Field(default=100.0, ge=1.0)


class InterviewReport(BaseModel):
    """面试综合评估报告。"""

    session_id: str
    overall_score: float = Field(..., ge=0.0, le=100.0)
    stage_scores: list[InterviewStageScore] = Field(default_factory=list)
    technical_breakdown: InterviewScoreBreakdown
    communication_breakdown: InterviewScoreBreakdown
    radar_chart: InterviewRadarChartData
    weak_points: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    generated_in_seconds: int = Field(default=30, ge=0)


class InterviewLifecycleLog(BaseModel):
    """状态流转日志。"""

    from_stage: InterviewStage
    to_stage: InterviewStage
    reason: str


class InterviewSessionSnapshot(BaseModel):
    """面试会话快照。"""

    session_id: str
    candidate_id: str
    status: InterviewStatus
    current_stage: InterviewStage
    pending_question: InterviewQuestion | None = None
    asked_questions: list[InterviewQuestion] = Field(default_factory=list)
    qna_turns: list[InterviewAnswerTurn] = Field(default_factory=list)
    follow_up_chain: dict[str, list[str]] = Field(default_factory=dict)
    weak_tag_marks: list[str] = Field(default_factory=list)
    assessment_points: list[InterviewAssessmentPoint] = Field(default_factory=list)
    stage_logs: list[InterviewLifecycleLog] = Field(default_factory=list)
    stage_scores: list[InterviewStageScore] = Field(default_factory=list)
    report_ready: bool = False
    report: InterviewReport | None = None


class InterviewResumeProfile(BaseModel):
    """候选人简历画像。"""

    summary: str = Field(..., min_length=1)
    skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)


class InterviewPerformanceRecord(BaseModel):
    """历史作答表现。"""

    question_signature: str = Field(..., min_length=1)
    score: float = Field(..., ge=0.0, le=100.0)
    weak_tags: list[str] = Field(default_factory=list)


class InterviewStartRequest(BaseModel):
    """发起面试会话。"""

    candidate_id: str = Field(..., min_length=1)
    resume_profile: InterviewResumeProfile
    history_performance: list[InterviewPerformanceRecord] = Field(default_factory=list)
    weak_tag_pool: list[str] = Field(default_factory=list)


class InterviewStartResponse(BaseModel):
    """发起面试响应。"""

    session: InterviewSessionSnapshot


class InterviewAnswerRequest(BaseModel):
    """提交答案请求。"""

    answer: str = Field(..., min_length=1)
    jump_to_stage: InterviewStage | None = None
    rollback_to_stage: InterviewStage | None = None
    interrupt: bool = False


class InterviewAnswerResponse(BaseModel):
    """提交答案响应。"""

    session: InterviewSessionSnapshot


class InterviewReportGenerateResponse(BaseModel):
    """一键生成报告响应。"""

    session_id: str
    report_status: str
    report: InterviewReport | None = None


class InterviewReportQueryResponse(BaseModel):
    """查询报告响应。"""

    report_status: str
    report: InterviewReport | None = None
