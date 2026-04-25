"""Resume Agent 请求与响应模型。"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ResumeDimension(str, Enum):
    """简历评审维度。"""

    WORK_EXPERIENCE = "work_experience"
    SKILL_MATCHING = "skill_matching"
    PROJECT_DESCRIPTION = "project_description"
    QUANTITATIVE_DATA = "quantitative_data"
    FORMATTING_LAYOUT = "formatting_layout"
    LANGUAGE_EXPRESSION = "language_expression"


class ReviewPriority(str, Enum):
    """问题优先级。"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ResumeReviewIssue(BaseModel):
    """逐句问题定位与修改建议。"""

    dimension: ResumeDimension
    priority: ReviewPriority
    issue: str = Field(..., min_length=1, description="问题描述。")
    original_text: str = Field(..., min_length=1, description="原文片段。")
    suggestion: str = Field(..., min_length=1, description="修改建议。")
    rewritten_text: str = Field(..., min_length=1, description="建议改写。")


class ResumeDimensionScore(BaseModel):
    """单维度评分。"""

    dimension: ResumeDimension
    score: float = Field(..., ge=0.0, le=100.0)
    rationale: str = Field(..., min_length=1)


class ResumeRadarMetric(BaseModel):
    """能力雷达图指标。"""

    dimension: ResumeDimension
    score: float = Field(..., ge=0.0, le=100.0)


class ResumeRadarChartData(BaseModel):
    """能力雷达图接口数据。"""

    indicators: list[str] = Field(default_factory=list, description="维度名称数组。")
    values: list[float] = Field(default_factory=list, description="维度得分数组。")
    max_value: float = Field(default=100.0, ge=1.0, description="雷达图坐标上限。")


class ResumeReviewRequest(BaseModel):
    """简历评审请求。"""

    resume_text: str = Field(..., min_length=20, description="简历全文。")
    target_role: str | None = Field(default=None, description="目标岗位。")
    job_description: str | None = Field(default=None, description="岗位 JD 文本。")


class ResumeReviewResponse(BaseModel):
    """结构化简历诊断报告。"""

    overall_score: float = Field(..., ge=0.0, le=100.0)
    dimension_scores: list[ResumeDimensionScore] = Field(default_factory=list)
    high_priority_issues: list[ResumeReviewIssue] = Field(default_factory=list)
    medium_priority_issues: list[ResumeReviewIssue] = Field(default_factory=list)
    low_priority_issues: list[ResumeReviewIssue] = Field(default_factory=list)
    radar_metrics: list[ResumeRadarMetric] = Field(default_factory=list)
    radar_chart: ResumeRadarChartData
    trace_id: str
