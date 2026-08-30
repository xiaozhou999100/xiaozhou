# -*- coding: utf-8 -*-
"""专家系统诊断服务：基于设备状态运行 IF-THEN 规则库，输出诊断结论。

可结合预警一键生成运维工单（严重/警告级别自动带入诊断建议）。
"""

from typing import Optional

from sqlalchemy.orm import Session

from ..algorithms.expert_system import diagnose as run_rules
from ..models import Alert, Equipment, SensorData, WorkOrder
from .anomaly import check_device_anomaly


def build_context(db: Session, equipment_id: int, cycle: Optional[int] = None) -> dict:
    """组装专家系统输入上下文（设备实时状态）。"""
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        raise ValueError("设备不存在")

    query = db.query(SensorData).filter(SensorData.equipment_id == equipment_id)
    if cycle is not None:
        query = query.filter(SensorData.cycle <= cycle)
    latest = query.order_by(SensorData.cycle.desc()).first()
    if not latest:
        raise ValueError("该设备无传感器数据，无法诊断")

    # 异常检测结果（不自动生成预警，仅提供上下文）
    try:
        anomaly = check_device_anomaly(db, equipment_id, cycle=latest.cycle, create_alert=False)
    except ValueError:
        anomaly = {"is_anomaly": False, "anomaly_score": 0.0}

    load_rate = round(100 * (latest.op_setting_1_norm + latest.op_setting_2_norm) / 2, 2)
    energy_efficiency = round(max(0.0, min(100.0, 100 - 0.6 * load_rate - 0.4 * (100 - latest.health_score))), 2)

    sensors = {c: getattr(latest, f"{c}_norm", 0.0) for c in
               ["sensor_2", "sensor_3", "sensor_4", "sensor_7", "sensor_9",
                "sensor_11", "sensor_12", "sensor_13", "sensor_14", "sensor_15",
                "sensor_17", "sensor_20", "sensor_21"]}

    return {
        "equipment_id": equipment_id,
        "device_code": equipment.device_code,
        "cycle": latest.cycle,
        "health_score": float(latest.health_score),
        "health_grade": latest.health_grade,
        "load_rate": load_rate,
        "energy_efficiency": energy_efficiency,
        "is_anomaly": anomaly["is_anomaly"],
        "anomaly_score": anomaly["anomaly_score"],
        "sensors": sensors,
    }


def diagnose_device(db: Session, equipment_id: int, cycle: Optional[int] = None,
                    create_order: bool = False) -> dict:
    """对设备执行专家系统诊断。

    Returns:
        {equipment_id, device_code, cycle, health_summary, diagnoses}
    """
    ctx = build_context(db, equipment_id, cycle)
    diagnoses = run_rules(ctx)

    # 严重/警告级别诊断可自动生成工单
    if create_order and diagnoses:
        severe = [d for d in diagnoses if d["level"] in ("严重", "警告")]
        if severe:
            top = severe[0]
            alert = Alert(
                equipment_id=equipment_id,
                alert_type="专家诊断",
                level=top["level"],
                message=f"{ctx['device_code']} {top['name']}：{top['fault_part']}",
                sensor_point="规则引擎",
            )
            db.add(alert)
            db.flush()
            order = WorkOrder(
                alert_id=alert.id,
                equipment_id=equipment_id,
                title=f"{top['name']}-{top['level']}",
                description=ctx["device_code"] + " " + top["name"] + "，故障部位：" + top["fault_part"],
                diagnosis="；".join(top["steps"]) + "。" + top["advice"],
                status="待处理",
            )
            db.add(order)
            db.commit()

    return {
        "equipment_id": equipment_id,
        "device_code": ctx["device_code"],
        "cycle": ctx["cycle"],
        "health_score": ctx["health_score"],
        "health_grade": ctx["health_grade"],
        "is_anomaly": ctx["is_anomaly"],
        "anomaly_score": ctx["anomaly_score"],
        "diagnoses": diagnoses,
    }
