# -*- coding: utf-8 -*-
"""传感器时序数据响应模型。"""

from pydantic import BaseModel, ConfigDict

from ..models.sensor_data import SENSOR_COLS


class SensorDataOut(BaseModel):
    """传感器时序数据响应（含原始值 + 归一化值）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    equipment_id: int
    cycle: int
    rul: float
    health_score: float
    health_grade: str
    anomaly_label: int
    op_setting_1: float
    op_setting_2: float
    op_setting_1_norm: float
    op_setting_2_norm: float
    # 15 个有效传感器原始值与归一化值
    sensor_2: float
    sensor_3: float
    sensor_4: float
    sensor_6: float
    sensor_7: float
    sensor_8: float
    sensor_9: float
    sensor_11: float
    sensor_12: float
    sensor_13: float
    sensor_14: float
    sensor_15: float
    sensor_17: float
    sensor_20: float
    sensor_21: float
    sensor_2_norm: float
    sensor_3_norm: float
    sensor_4_norm: float
    sensor_6_norm: float
    sensor_7_norm: float
    sensor_8_norm: float
    sensor_9_norm: float
    sensor_11_norm: float
    sensor_12_norm: float
    sensor_13_norm: float
    sensor_14_norm: float
    sensor_15_norm: float
    sensor_17_norm: float
    sensor_20_norm: float
    sensor_21_norm: float
