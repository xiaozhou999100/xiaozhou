# -*- coding: utf-8 -*-
"""设备传感器时序数据表：数字孪生实时同步的数据底座。

来源：data/processed/train_FD001_processed.csv（C-MAPSS FD001 预处理结果）。
保留 15 个有效传感器 + 2 个工况列，均含原始值与 MinMax 归一化值（0~1）。
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

# 有效传感器与工况列（预处理后保留）
SENSOR_COLS = ["sensor_2", "sensor_3", "sensor_4", "sensor_6", "sensor_7", "sensor_8",
               "sensor_9", "sensor_11", "sensor_12", "sensor_13", "sensor_14", "sensor_15",
               "sensor_17", "sensor_20", "sensor_21"]
OP_COLS = ["op_setting_1", "op_setting_2"]


class SensorData(Base):
    """设备传感器时序数据。"""

    __tablename__ = "sensor_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id", ondelete="CASCADE"), index=True)
    cycle: Mapped[int] = mapped_column(Integer, index=True, comment="运行循环数(时间轴)")
    rul: Mapped[float] = mapped_column(Float, comment="剩余使用寿命")
    health_score: Mapped[float] = mapped_column(Float, comment="健康度评分0-100")
    health_grade: Mapped[str] = mapped_column(String(16), comment="健康等级")
    anomaly_label: Mapped[int] = mapped_column(Integer, default=0, comment="异常标签0/1")

    op_setting_1: Mapped[float] = mapped_column(Float)
    op_setting_2: Mapped[float] = mapped_column(Float)
    op_setting_1_norm: Mapped[float] = mapped_column(Float)
    op_setting_2_norm: Mapped[float] = mapped_column(Float)

    # 15 个有效传感器：原始值 + 归一化值
    sensor_2: Mapped[float] = mapped_column(Float)
    sensor_3: Mapped[float] = mapped_column(Float)
    sensor_4: Mapped[float] = mapped_column(Float)
    sensor_6: Mapped[float] = mapped_column(Float)
    sensor_7: Mapped[float] = mapped_column(Float)
    sensor_8: Mapped[float] = mapped_column(Float)
    sensor_9: Mapped[float] = mapped_column(Float)
    sensor_11: Mapped[float] = mapped_column(Float)
    sensor_12: Mapped[float] = mapped_column(Float)
    sensor_13: Mapped[float] = mapped_column(Float)
    sensor_14: Mapped[float] = mapped_column(Float)
    sensor_15: Mapped[float] = mapped_column(Float)
    sensor_17: Mapped[float] = mapped_column(Float)
    sensor_20: Mapped[float] = mapped_column(Float)
    sensor_21: Mapped[float] = mapped_column(Float)

    sensor_2_norm: Mapped[float] = mapped_column(Float)
    sensor_3_norm: Mapped[float] = mapped_column(Float)
    sensor_4_norm: Mapped[float] = mapped_column(Float)
    sensor_6_norm: Mapped[float] = mapped_column(Float)
    sensor_7_norm: Mapped[float] = mapped_column(Float)
    sensor_8_norm: Mapped[float] = mapped_column(Float)
    sensor_9_norm: Mapped[float] = mapped_column(Float)
    sensor_11_norm: Mapped[float] = mapped_column(Float)
    sensor_12_norm: Mapped[float] = mapped_column(Float)
    sensor_13_norm: Mapped[float] = mapped_column(Float)
    sensor_14_norm: Mapped[float] = mapped_column(Float)
    sensor_15_norm: Mapped[float] = mapped_column(Float)
    sensor_17_norm: Mapped[float] = mapped_column(Float)
    sensor_20_norm: Mapped[float] = mapped_column(Float)
    sensor_21_norm: Mapped[float] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="入库时间")

    equipment = relationship("Equipment", back_populates="sensor_data")

    @classmethod
    def sensor_columns(cls, normalized: bool = False):
        """返回传感器列名列表（原始或归一化）。"""
        return [f"{c}_norm" if normalized else c for c in SENSOR_COLS]
