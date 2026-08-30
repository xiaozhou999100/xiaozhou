# -*- coding: utf-8 -*-
"""数据挖掘异常检测服务：孤立森林运行时检测 + 预警生成。"""

from typing import Optional

from sqlalchemy.orm import Session

from ..algorithms.features import device_feature_vector
from ..algorithms.isolation_forest import load_model
from ..algorithms.random_forest import load_model as load_rf
from ..models import Alert, Equipment, SensorData

# 模型懒加载（首次调用时加载）
_if_payload = None


def _get_model():
    global _if_payload
    if _if_payload is None:
        _if_payload = load_model()
    return _if_payload


def _device_rows(db: Session, equipment_id: int, cycle: Optional[int]):
    query = db.query(SensorData).filter(SensorData.equipment_id == equipment_id)
    if cycle is not None:
        query = query.filter(SensorData.cycle <= cycle)
    return query.order_by(SensorData.cycle.asc()).all()


def check_device_anomaly(db: Session, equipment_id: int, cycle: Optional[int] = None,
                         create_alert: bool = True) -> dict:
    """对设备最新状态执行孤立森林异常检测。

    返回：
        {is_anomaly, anomaly_score, cycle, message}
    若 is_anomaly 且 create_alert=True，自动生成一条「传感器异常」预警。
    """
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        raise ValueError("设备不存在")

    rows = _device_rows(db, equipment_id, cycle)
    if not rows:
        raise ValueError("该设备无传感器数据，无法检测")

    vec = device_feature_vector(rows)
    payload = _get_model()
    from ..algorithms.isolation_forest import predict_single
    is_anomaly, anomaly_score = predict_single(payload["model"], vec)

    latest = rows[-1]
    message = (
        f"设备 {equipment.device_code} 第 {latest.cycle} 周期检出数据异常"
        f"（异常度 {anomaly_score}），请结合专家系统诊断定位故障点"
        if is_anomaly else f"设备 {equipment.device_code} 状态正常（异常度 {anomaly_score}）"
    )

    if is_anomaly and create_alert:
        alert = Alert(
            equipment_id=equipment_id,
            alert_type="传感器异常",
            level="警告" if anomaly_score < 0.5 else "严重",
            message=message,
            sensor_point="多传感器综合",
        )
        db.add(alert)
        db.commit()

    return {
        "equipment_id": equipment_id,
        "is_anomaly": bool(is_anomaly),
        "anomaly_score": anomaly_score,
        "cycle": latest.cycle,
        "message": message,
    }


def evaluate_rul(db: Session, equipment_id: int, cycle: Optional[int] = None) -> dict:
    """随机森林 RUL/健康度预测（供评估服务调用）。

    返回：{rul, health_score, cycle}
    """
    rows = _device_rows(db, equipment_id, cycle)
    if not rows:
        raise ValueError("该设备无传感器数据，无法评估")

    vec = device_feature_vector(rows)
    from ..algorithms.random_forest import rul_to_health_score
    rf = load_rf()
    rul = float(rf["model"].predict([vec])[0])
    latest = rows[-1]
    return {
        "rul": round(rul, 2),
        "health_score": round(rul_to_health_score(rul), 2),
        "cycle": latest.cycle,
    }
