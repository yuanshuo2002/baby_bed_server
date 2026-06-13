"""
危险事件模型 - danger_event表
记录危险动作事件：呼吸暂停、靠近床边、翻床、探出床外、站立等
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DangerEvent(Base):
    """危险事件表"""

    __tablename__ = "danger_event"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    baby_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    device_sn: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    # 危险类型
    danger_type: Mapped[str] = mapped_column(
        Enum(
            "breath_pause",      # 呼吸暂停
            "near_edge",         # 靠近床边
            "climbing",          # 翻床
            "body_out",          # 身体探出
            "standing",          # 站立
            "prone_sleep",       # 趴睡
            "face_covered",      # 捂口鼻
        ),
        nullable=False,
        comment="危险类型"
    )
    
    # 严重程度
    severity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="严重程度: 1=警告, 2=危险, 3=紧急"
    )
    
    # 时间信息
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="检测时间")
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="结束时间")
    duration_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="持续时长(秒)")
    
    # 检测数据
    breath_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, comment="呼吸频率")
    heart_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, comment="心率")
    body_offset_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, comment="身体偏移距离")
    pose_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="姿态")
    position_x: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, comment="位置X坐标")
    position_y: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, comment="位置Y坐标")
    
    # 响应执行
    alert_played: Mapped[int] = mapped_column(Integer, server_default="0", comment="是否播放警报")
    voice_played: Mapped[int] = mapped_column(Integer, server_default="0", comment="是否播放父母语音")
    screen_alert: Mapped[int] = mapped_column(Integer, server_default="0", comment="是否屏幕警报")
    push_sent: Mapped[int] = mapped_column(Integer, server_default="0", comment="是否推送通知")
    call_triggered: Mapped[int] = mapped_column(Integer, server_default="0", comment="是否触发电话")
    
    # 处理结果
    parent_handled: Mapped[int] = mapped_column(Integer, server_default="0", comment="父母是否处理")
    handled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="处理时间")
    handle_result: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="处理结果")
    
    # 媒体资源
    snapshot_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="快照图片URL")
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="视频片段URL")
    
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
