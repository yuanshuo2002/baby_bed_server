"""
睡眠报告模型 - sleep_report表
每日睡眠统计报告
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Date, DateTime, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SleepReport(Base):
    """睡眠报告表"""

    __tablename__ = "sleep_report"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    baby_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False, index=True, comment="报告日期")
    
    # 睡眠统计
    total_sleep_min: Mapped[int] = mapped_column(Integer, server_default="0", comment="总睡眠时长(分钟)")
    night_sleep_min: Mapped[int] = mapped_column(Integer, server_default="0", comment="夜间睡眠时长(分钟)")
    day_sleep_min: Mapped[int] = mapped_column(Integer, server_default="0", comment="白天睡眠时长(分钟)")
    nap_count: Mapped[int] = mapped_column(Integer, server_default="0", comment="小睡次数")
    
    # 睡眠质量
    deep_sleep_min: Mapped[int] = mapped_column(Integer, server_default="0", comment="深睡时长(分钟)")
    light_sleep_min: Mapped[int] = mapped_column(Integer, server_default="0", comment="浅睡时长(分钟)")
    avg_sleep_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="平均睡眠时长(分钟)")
    longest_sleep_min: Mapped[int] = mapped_column(Integer, server_default="0", comment="最长连续睡眠(分钟)")
    
    # 入睡/醒来时间
    first_sleep_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="首次入睡时间")
    last_wake_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="最后醒来时间")
    avg_fall_asleep_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="平均入睡耗时(分钟)")
    
    # 体征平均
    avg_breath_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, comment="平均呼吸频率")
    avg_heart_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, comment="平均心率")
    
    # 异常事件
    cry_count: Mapped[int] = mapped_column(Integer, server_default="0", comment="哭闹次数")
    danger_count: Mapped[int] = mapped_column(Integer, server_default="0", comment="危险事件次数")
    awake_count: Mapped[int] = mapped_column(Integer, server_default="0", comment="醒来次数")
    
    # 评分
    sleep_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="睡眠评分(0-100)")
    
    # AI分析
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="AI睡眠分析")
    suggestions: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="改善建议")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
