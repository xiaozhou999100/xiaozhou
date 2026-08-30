# -*- coding: utf-8 -*-
"""预警记录表：传感器异常/能耗超标/健康度过低/节拍异常。"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Alert(Base):
    """孪生预警记录（提示/警告/严重三级）。"""

    __tablename__ = "alert"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id", ondelete="CASCADE"), index=True)
    alert_type: Mapped[str] = mapped_column(String(32), comment="预警类型: 传感器异常/能耗超标/健康度过低/节拍异常")
    level: Mapped[str] = mapped_column(String(16), default="提示", comment="级别: 提示/警告/严重")
    message: Mapped[str] = mapped_column(Text, comment="预警内容")
    sensor_point: Mapped[str] = mapped_column(String(32), default="", comment="关联传感器点位")
    is_handled: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已处理")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")

    equipment = relationship("Equipment", back_populates="alerts")
    work_order = relationship("WorkOrder", back_populates="alert", uselist=False)
