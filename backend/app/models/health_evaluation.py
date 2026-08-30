# -*- coding: utf-8 -*-
"""健康/能耗评估记录表。"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class HealthEvaluation(Base):
    """设备健康/能耗评估记录。"""

    __tablename__ = "health_evaluation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id", ondelete="CASCADE"), index=True)
    eval_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="评估时间")
    health_score: Mapped[float] = mapped_column(Float, comment="健康度评分0-100")
    energy_efficiency: Mapped[float] = mapped_column(Float, comment="能耗效率0-100")
    load_rate: Mapped[float] = mapped_column(Float, comment="负载率0-100")
    health_grade: Mapped[str] = mapped_column(String(16), comment="健康等级")
    detail: Mapped[str] = mapped_column(Text, default="", comment="评估详情(JSON/文本)")

    equipment = relationship("Equipment", back_populates="evaluations")
