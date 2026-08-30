# -*- coding: utf-8 -*-
"""健康/能耗评估服务（阶段3：接入随机森林 RUL 预测）。

评估流程：
    1. 基于设备历史传感器时序构造窗口统计特征；
    2. 随机森林回归模型预测 RUL；
    3. RUL 映射为 0~100 健康度评分；
    4. 结合工况推导负载率与能耗效率；
    5. 保存评估记录并同步更新设备台账健康等级。
"""

from typing import Optional

from sqlalchemy.orm import Session

from ..models import Equipment, HealthEvaluation
from .anomaly import evaluate_rul


def _grade_of(score: float) -> str:
    if score >= 75:
        return "健康"
    if score >= 50:
        return "注意"
    if score >= 25:
        return "预警"
    return "严重"


def evaluate_device(db: Session, equipment_id: int, cycle: Optional[int] = None) -> HealthEvaluation:
    """对指定设备执行随机森林健康/能耗评估，保存并返回评估记录。"""
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        raise ValueError("设备不存在")

    result = evaluate_rul(db, equipment_id, cycle=cycle)
    health_score = result["health_score"]
    pred_cycle = result["cycle"]

    # 负载率/能耗效率由工况归一化值近似推导（与阶段2口径一致）
    from ..models import SensorData
    row = (db.query(SensorData)
           .filter(SensorData.equipment_id == equipment_id, SensorData.cycle == pred_cycle)
           .first())
    load_rate = round(100 * (row.op_setting_1_norm + row.op_setting_2_norm) / 2, 2)
    energy_efficiency = round(max(0.0, min(100.0, 100 - 0.6 * load_rate - 0.4 * (100 - health_score))), 2)

    grade = _grade_of(health_score)
    detail = (
        f"随机森林预测：基于第{pred_cycle}周期窗口特征，RUL≈{result['rul']}周期，"
        f"健康度{health_score}分；负载率{load_rate}%，能耗效率{energy_efficiency}%。"
    )

    record = HealthEvaluation(
        equipment_id=equipment_id,
        health_score=health_score,
        energy_efficiency=energy_efficiency,
        load_rate=load_rate,
        health_grade=grade,
        detail=detail,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # 同步更新设备台账健康等级
    equipment.health_grade = grade
    db.commit()

    return record
