# -*- coding: utf-8 -*-
"""传感器时序数据路由：数字孪生实时同步数据源。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Equipment, SensorData
from ..schemas import SensorDataOut, success

router = APIRouter(prefix="/api/v1", tags=["传感器数据"])


@router.get("/equipment/{equipment_id}/sensor-data")
def get_sensor_data(
    equipment_id: int,
    limit: int = 100,
    start_cycle: Optional[int] = None,
    end_cycle: Optional[int] = None,
    normalized: bool = False,
    db: Session = Depends(get_db),
):
    """设备传感器时序数据（按周期范围/条数查询，异常点可标红）。

    - normalized=True 时仅返回归一化传感器列（0~1，供图表展示）
    - 默认取最近 limit 条
    """
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="设备不存在")

    query = db.query(SensorData).filter(SensorData.equipment_id == equipment_id)
    if start_cycle is not None:
        query = query.filter(SensorData.cycle >= start_cycle)
    if end_cycle is not None:
        query = query.filter(SensorData.cycle <= end_cycle)

    rows = query.order_by(SensorData.cycle.desc()).limit(min(max(limit, 1), 5000)).all()
    rows = list(reversed(rows))  # 时间正序返回

    if normalized:
        # 仅返回图表所需归一化字段（含 RUL/健康度，供概览面板展示）
        items = []
        for r in rows:
            item = {
                "cycle": r.cycle,
                "rul": r.rul,
                "health_score": r.health_score,
                "health_grade": r.health_grade,
                "anomaly_label": r.anomaly_label,
            }
            for c in SensorData.sensor_columns(normalized=True):
                item[c] = getattr(r, c)
            item["op_setting_1_norm"] = r.op_setting_1_norm
            item["op_setting_2_norm"] = r.op_setting_2_norm
            items.append(item)
        return success({"equipment_id": equipment_id, "items": items})

    return success({
        "equipment_id": equipment_id,
        "items": [SensorDataOut.model_validate(r).model_dump() for r in rows],
    })


@router.get("/sensor-data/{record_id}")
def get_sensor_record(record_id: int, db: Session = Depends(get_db)):
    """单条传感器数据详情。"""
    record = db.get(SensorData, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return success(SensorDataOut.model_validate(record).model_dump())
