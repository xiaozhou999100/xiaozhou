# -*- coding: utf-8 -*-
"""设备台账表：车间设备数字档案。"""

from datetime import datetime

from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Equipment(Base):
    """车间设备台账。"""

    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, comment="设备编号")
    name: Mapped[str] = mapped_column(String(64), comment="设备名称")
    model: Mapped[str] = mapped_column(String(64), comment="型号")
    station: Mapped[str] = mapped_column(String(32), index=True, comment="工位/产线位置")
    install_date: Mapped[datetime | None] = mapped_column(Date, nullable=True, comment="投运日期")
    twin_status: Mapped[str] = mapped_column(String(16), default="运行", comment="孪生状态: 运行/待机/报警")
    health_grade: Mapped[str] = mapped_column(String(16), default="健康", comment="健康等级: 健康/注意/预警/严重")
    description: Mapped[str] = mapped_column(Text, default="", comment="备注")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")

    sensor_data = relationship("SensorData", back_populates="equipment", cascade="all, delete-orphan")
    evaluations = relationship("HealthEvaluation", back_populates="equipment", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="equipment", cascade="all, delete-orphan")
    work_orders = relationship("WorkOrder", back_populates="equipment", cascade="all, delete-orphan")
