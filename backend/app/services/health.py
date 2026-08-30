# -*- coding: utf-8 -*-
"""健康/能耗评估服务。

阶段2：采用可解释的规则式评估（基于预处理数据的健康度评分与工况负载推导）。
阶段3：将升级为随机森林回归模型（基于传感器统计特征预测），本服务为模型调用层预留入口。
"""

from typing import Optional

from sqlalchemy.orm import Session

from ..models import Equipment, HealthEvaluation, SensorData


def _grade_of(score: float) -> str:
    if score >= 75:
        return "健康"
    if score >= 50:
        return "注意"
    if score >= 25:
        return "预警"
    return "严重"


def evaluate_device(db: Session, equipment_id: int, cycle: Optional[int] = None) -> HealthEvaluation:
    """对指定设备执行健康/能耗评估，返回并保存评估记录。

    规则：
      - health_score：取该设备指定周期（默认最新）预处理数据的健康度评分；
      - load_rate：由工况归一化均值近似表示设备负载率；
      - energy_efficiency：综合健康度与负载推导（数值越低越耗能）。
    """
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        raise ValueError("设备不存在")

    query = db.query(SensorData).filter(SensorData.equipment_id == equipment_id)
    if cycle is not None:
        row = query.filter(SensorData.cycle == cycle).order_by(SensorData.cycle.desc()).first()
    else:
        row = query.order_by(SensorData.cycle.desc()).first()
    if not row:
        raise ValueError("该设备无传感器数据，无法评估")

    health_score = round(float(row.health_score), 2)
    load_rate = round(100 * (row.op_setting_1_norm + row.op_setting_2_norm) / 2, 2)
    energy_efficiency = round(max(0.0, min(100.0, 100 - 0.6 * load_rate - 0.4 * (100 - health_score))), 2)

    grade = _grade_of(health_score)
    detail = (
        f"基于第{row.cycle}周期数据评估；健康度{health_score}分，"
        f"负载率{load_rate}%，能耗效率{energy_efficiency}%。"
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
