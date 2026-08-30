# -*- coding: utf-8 -*-
"""数据导入脚本：将 data/processed 预处理结果导入 SQLite。

用法（在 backend/ 目录下）：
    python -m app.seed

功能：
    1. 重建数据库表（equipment / sensor_data / health_evaluation / alert / work_order）；
    2. 读取 device_profile.csv 生成 100 台设备台账；
    3. 读取 train_FD001_processed.csv 导入传感器时序数据；
    4. 生成少量演示用预警与工单，便于阶段4前端联调。
"""

import sys
from datetime import date, datetime
from pathlib import Path

# 保证以 backend/ 为根可导入 app 包
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pandas as pd

from app.config import PROCESSED_DIR
from app.database import Base, SessionLocal, engine
from app.models import Alert, Equipment, SensorData, WorkOrder


def _grade_of(score: float) -> str:
    if score >= 75:
        return "健康"
    if score >= 50:
        return "注意"
    if score >= 25:
        return "预警"
    return "严重"


def seed_equipment(db) -> dict[int, int]:
    """导入设备台账，返回 unit -> equipment.id 映射。"""
    profile = pd.read_csv(PROCESSED_DIR / "device_profile.csv")
    unit2id: dict[int, int] = {}

    for _, row in profile.iterrows():
        unit = int(row["device_id"])
        avg_score = float(row["avg_health_score"])
        init_state = str(row["init_state"])
        twin_status = {"运行": "运行", "关注": "待机", "报警": "报警"}.get(init_state, "运行")

        equipment = Equipment(
            device_code=f"DEV{unit:03d}",
            name=f"车间设备{unit:03d}",
            model="CMAPSS-FD001 模拟设备",
            station=f"工位{(unit - 1) // 10 + 1:02d}",
            install_date=date.fromordinal(date(2023, 1, 1).toordinal() + unit),  # 模拟不同投运日期
            twin_status=twin_status,
            health_grade=_grade_of(avg_score),
            description=f"由 C-MAPSS FD001 仿真数据映射的孪生设备（单元 {unit}）",
        )
        db.add(equipment)
        db.flush()
        unit2id[unit] = equipment.id

    db.commit()
    return unit2id


def seed_sensor_data(db, unit2id: dict[int, int]) -> None:
    """导入传感器时序数据（分批，避免内存峰值）。"""
    train = pd.read_csv(PROCESSED_DIR / "train_FD001_processed.csv")

    # 只保留 ORM 模型需要的列
    sensor_cols = SensorData.sensor_columns() + SensorData.sensor_columns(normalized=True)
    cols = ["unit", "cycle", "rul", "health_score", "health_grade", "anomaly_label",
            "op_setting_1", "op_setting_2", "op_setting_1_norm", "op_setting_2_norm"] + sensor_cols

    records = []
    batch = 2000
    for _, row in train[cols].iterrows():
        records.append(SensorData(
            equipment_id=unit2id[int(row["unit"])],
            cycle=int(row["cycle"]),
            rul=float(row["rul"]),
            health_score=float(row["health_score"]),
            health_grade=str(row["health_grade"]),
            anomaly_label=int(row["anomaly_label"]),
            op_setting_1=float(row["op_setting_1"]),
            op_setting_2=float(row["op_setting_2"]),
            op_setting_1_norm=float(row["op_setting_1_norm"]),
            op_setting_2_norm=float(row["op_setting_2_norm"]),
            **{c: float(row[c]) for c in sensor_cols},
        ))
        if len(records) >= batch:
            db.bulk_save_objects(records)
            records.clear()
    if records:
        db.bulk_save_objects(records)
    db.commit()


def seed_demo_alerts_and_orders(db, unit2id: dict[int, int]) -> None:
    """生成少量演示用预警与工单，验证预警→工单闭环。"""
    demo = [
        # (unit, alert_type, level, message, sensor_point)
        (1, "健康度过低", "严重", "设备 DEV001 健康度降至 12.5，低于严重阈值 25", "health_score"),
        (2, "传感器异常", "警告", "设备 DEV002 sensor_11 偏离正常范围，疑似传感器漂移", "sensor_11"),
        (5, "能耗超标", "警告", "设备 DEV005 负载率持续偏高，能耗超过基线 20%", "op_setting_1"),
        (8, "节拍异常", "提示", "设备 DEV008 节拍波动超过 10%，需关注产线节拍", "cycle"),
    ]
    for unit, alert_type, level, message, point in demo:
        if unit not in unit2id:
            continue
        alert = Alert(
            equipment_id=unit2id[unit],
            alert_type=alert_type,
            level=level,
            message=message,
            sensor_point=point,
        )
        db.add(alert)
        db.flush()
        order = WorkOrder(
            alert_id=alert.id,
            equipment_id=unit2id[unit],
            title=f"{alert_type}-{level}",
            description=message,
            diagnosis=f"请结合传感器点位[{point}]按专家系统规则库排查并维修",
            status="待处理",
        )
        db.add(order)
    db.commit()


def main() -> None:
    print(f"[seed] 数据库: {engine.url}")
    print("[seed] 重建数据表 ...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("[seed] 导入设备台账 ...")
        unit2id = seed_equipment(db)
        print(f"  -> {len(unit2id)} 台设备")

        print("[seed] 导入传感器时序数据 ...")
        seed_sensor_data(db, unit2id)
        total = db.query(SensorData).count()
        print(f"  -> {total} 条传感器记录")

        print("[seed] 生成演示预警与工单 ...")
        seed_demo_alerts_and_orders(db, unit2id)
        print(f"  -> 预警 {db.query(Alert).count()} 条 / 工单 {db.query(WorkOrder).count()} 条")

        print("[seed] 完成 ✓")
    finally:
        db.close()


if __name__ == "__main__":
    main()
