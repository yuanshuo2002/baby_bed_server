"""
作息相关Schema
"""
from datetime import date, datetime, time
from pydantic import BaseModel, Field


class RoutineCreate(BaseModel):
    """创建作息请求"""
    baby_id: int = Field(..., description="宝宝ID")
    template_name: str = Field(..., min_length=1, max_length=50, description="模板名称")
    age_month_min: int | None = Field(None, description="适用最小月龄")
    age_month_max: int | None = Field(None, description="适用最大月龄")
    time_slot: time = Field(..., description="时间段")
    activity_type: str = Field(..., description="活动类型：eat/active/sleep/y")
    activity_name: str | None = Field(None, max_length=100, description="活动名称")
    duration_min: int | None = Field(None, ge=1, description="预计时长(分钟)")
    reminder_enabled: int = Field(default=1, description="是否开启提醒")
    reminder_before_min: int = Field(default=10, description="提前提醒分钟数")
    effective_date: date = Field(..., description="生效日期")
    expire_date: date | None = Field(None, description="失效日期")


class RoutineUpdate(BaseModel):
    """更新作息请求"""
    template_name: str | None = Field(None, min_length=1, max_length=50, description="模板名称")
    time_slot: time | None = Field(None, description="时间段")
    activity_type: str | None = Field(None, description="活动类型")
    activity_name: str | None = Field(None, max_length=100, description="活动名称")
    duration_min: int | None = Field(None, ge=1, description="预计时长")
    reminder_enabled: int | None = Field(None, description="是否开启提醒")
    reminder_before_min: int | None = Field(None, description="提前提醒分钟数")
    expire_date: date | None = Field(None, description="失效日期")
    is_active: int | None = Field(None, ge=0, le=1, description="是否启用")


class RoutineInfo(BaseModel):
    """作息信息响应"""
    id: int
    baby_id: int
    template_name: str
    age_month_min: int | None = None
    age_month_max: int | None = None
    time_slot: time | None = None
    activity_type: str
    activity_name: str | None = None
    duration_min: int | None = None
    reminder_enabled: int | None = None
    reminder_before_min: int | None = None
    is_auto_adjusted: int | None = None
    adjust_reason: str | None = None
    effective_date: date | None = None
    expire_date: date | None = None
    is_active: int | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ========== EASY模式作息引导 (2.3) ==========
class EASYTemplateRequest(BaseModel):
    """EASY模式模板请求"""
    baby_id: int = Field(..., description="宝宝ID")
    age_month: int = Field(..., ge=0, le=48, description="宝宝月龄(0-48)")


class EASYActivity(BaseModel):
    """EASY活动项"""
    time_slot: str = Field(..., description="时间段")
    activity_type: str = Field(..., description="活动类型: Eat/Activity/Sleep/You")
    activity_name: str = Field(..., description="活动名称")
    duration_min: int = Field(..., description="预计时长(分钟)")
    reminder_enabled: bool = Field(default=True, description="是否提醒")


class EASYTemplateResponse(BaseModel):
    """EASY模式模板响应"""
    template_id: str
    baby_id: int
    age_month: int
    template_name: str = Field(..., description="模板名称")
    activities: list[EASYActivity] = Field(..., description="活动列表")
    cycle_days: int = Field(default=7, description="循环周期(天)")
    created_at: datetime | None = None


class RoutineOptimizeRequest(BaseModel):
    """作息优化请求"""
    baby_id: int = Field(..., description="宝宝ID")
    analysis_days: int = Field(default=7, ge=1, le=30, description="分析天数")


class RoutineOptimizeResponse(BaseModel):
    """作息优化响应"""
    baby_id: int
    optimization_id: str
    current_plan: list[dict] = Field(..., description="当前作息计划")
    optimized_plan: list[dict] = Field(..., description="优化后作息计划")
    changes: list[str] = Field(..., description="变更说明")
    confidence_score: float = Field(..., ge=0, le=1, description="优化置信度")
    generated_at: datetime | None = None


# ========== 作息冲突检测与优化 (2.4) ==========
class ConflictCheckRequest(BaseModel):
    """冲突检测请求"""
    baby_id: int = Field(..., description="宝宝ID")
    check_days: int = Field(default=7, ge=1, le=30, description="检测天数")


class ConflictCheckResponse(BaseModel):
    """冲突检测响应"""
    baby_id: int
    check_period: str = Field(..., description="检测周期")
    total_conflicts: int = Field(..., description="冲突总数")
    conflicts: list[dict] = Field(..., description="冲突详情列表")
    summary: str = Field(..., description="冲突总结")
    suggestions: list[str] = Field(..., description="优化建议")
    can_auto_fix: bool = Field(..., description="是否可自动修复")


class RoutineFixRequest(BaseModel):
    """作息修复请求"""
    baby_id: int = Field(..., description="宝宝ID")
    fix_type: str = Field(default="auto", description="修复类型: auto/manual")
    conflict_ids: list[int] | None = Field(None, description="指定修复的冲突ID")


class ConflictInfo(BaseModel):
    """冲突信息响应"""
    id: int
    baby_id: int
    routine_id: int | None = None
    conflict_date: date | None = None
    expected_time: time | None = None
    actual_time: time | None = None
    deviation_min: int | None = None
    conflict_type: str | None = None
    audit_analysis: str | None = None
    suggested_fix: str | None = None
    auto_fixed: int | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
