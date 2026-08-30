# -*- coding: utf-8 -*-
"""运维工单表：预警一键生成，状态流转（待处理→维修中→已完成）。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class WorkOrder(Base):
    """运维工单。"""

    __tablename__ = "work_order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[int | None] = mapped_column(
        ForeignKey("alert.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联预警ID")
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(128), comment="工单标题")
    description: Mapped[str] = mapped_column(Text, default="", comment="工单描述")
    diagnosis: Mapped[str] = mapped_column(Text, default="", comment="诊断建议")
    status: Mapped[str] = mapped_column(String(16), default="待处理", comment="状态: 待处理/维修中/已完成")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    alert = relationship("Alert", back_populates="work_order")
    equipment = relationship("Equipment", back_populates="work_orders")
