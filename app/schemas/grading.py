"""Grading Agent 请求与响应模型。"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """题目类型。"""

    OBJECTIVE = "objective"
    SUBJECTIVE = "subjective"
    CODING = "coding"


class ObjectiveRule(BaseModel):
    """客观题判分规则。"""

    expected_answer: str = Field(..., description="标准答案。")
    ignore_case: bool = Field(default=True, description="是否忽略大小写。")
    trim_whitespace: bool = Field(default=True, description="是否忽略首尾空白。")


class SubjectiveRubricPoint(BaseModel):
    """主观题采分点。"""

    key: str = Field(..., min_length=1, description="采分点标识。")
    description: str = Field(..., min_length=1, description="采分点描述。")
    score: float = Field(..., ge=0.0, description="该采分点分值。")


class CodingRubric(BaseModel):
    """编程题判题规则（LLM 语义判读）。"""

    requirements: list[str] = Field(default_factory=list, description="代码实现要求。")
    test_cases: list[str] = Field(default_factory=list, description="测试用例说明。")


class GradingQuestion(BaseModel):
    """待批改单题。"""

    question_id: str = Field(..., min_length=1)
    question_type: QuestionType
    stem: str = Field(..., min_length=1, description="题干。")
    max_score: float = Field(..., gt=0.0, description="本题满分。")
    student_answer: str = Field(..., description="学员作答。")
    objective_rule: ObjectiveRule | None = None
    subjective_rubric: list[SubjectiveRubricPoint] = Field(default_factory=list)
    coding_rubric: CodingRubric | None = None
    knowledge_tags: list[str] = Field(default_factory=list, description="知识点标签。")


class GradingRequest(BaseModel):
    """试卷批改请求。"""

    exam_id: str = Field(..., min_length=1)
    student_id: str = Field(..., min_length=1)
    teacher_id: str | None = None
    questions: list[GradingQuestion] = Field(..., min_length=1)


class GradingSuggestion(BaseModel):
    """评分建议项。"""

    type: str = Field(..., description="建议类型。")
    content: str = Field(..., description="建议内容。")


class GradingQuestionResult(BaseModel):
    """单题批改结果。"""

    question_id: str
    question_type: QuestionType
    score: float = Field(..., ge=0.0)
    is_correct: bool | None = Field(default=None, description="客观题对错。")
    rationale: str = Field(..., description="判分理由。")
    matched_points: list[str] = Field(default_factory=list, description="命中采分点。")
    missed_points: list[str] = Field(default_factory=list, description="遗漏采分点。")
    suggestions: list[GradingSuggestion] = Field(default_factory=list)


class TeacherReviewItem(BaseModel):
    """教师审核项。"""

    question_id: str
    ai_score: float = Field(..., ge=0.0)
    final_score: float = Field(..., ge=0.0)
    modified_by_teacher: bool
    teacher_comment: str | None = None


class WeakKnowledgePoint(BaseModel):
    """薄弱知识点统计。"""

    tag: str
    wrong_count: int = Field(..., ge=0)
    impact_score: float = Field(..., ge=0.0)


class LearningAnalysisReport(BaseModel):
    """结构化学情分析。"""

    wrong_reason_summary: list[str] = Field(default_factory=list)
    weak_knowledge_points: list[WeakKnowledgePoint] = Field(default_factory=list)
    answering_shortcomings: list[str] = Field(default_factory=list)
    optimization_suggestions: list[str] = Field(default_factory=list)


class GradingResponse(BaseModel):
    """批改结果。"""

    exam_id: str
    student_id: str
    total_score: float = Field(..., ge=0.0)
    full_score: float = Field(..., ge=0.0)
    reviewed: bool = Field(default=False, description="是否已教师确认发布。")
    question_results: list[GradingQuestionResult] = Field(default_factory=list)
    teacher_review_items: list[TeacherReviewItem] = Field(default_factory=list)
    analysis_report: LearningAnalysisReport
    trace_id: str


class TeacherScoreOverride(BaseModel):
    """教师改单项。"""

    question_id: str
    final_score: float = Field(..., ge=0.0)
    teacher_comment: str | None = None


class TeacherReviewPublishRequest(BaseModel):
    """教师审核并确认发布请求。"""

    grading_result: GradingResponse
    overrides: list[TeacherScoreOverride] = Field(default_factory=list)
