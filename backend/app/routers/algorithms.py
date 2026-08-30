# -*- coding: utf-8 -*-
"""算法服务路由：异常检测 / 专家系统诊断。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Equipment
from ..services.anomaly import check_device_anomaly
from ..services.diagnosis import diagnose_device
from ..schemas import success

router = APIRouter(prefix="/api/v1", tags=["算法服务"])


class DiagnoseRequest(BaseModel):
    """诊断请求（可选指定周期，可选自动生成工单）。"""

    cycle: Optional[int] = Field(None, description="指定周期，缺省取最新")
    create_order: bool = Field(False, description="严重/警告级别是否自动生成工单")


def _ensure_equipment(db: Session, equipment_id: int) -> None:
    if not db.get(Equipment, equipment_id):
        raise HTTPException(status_code=404, detail="设备不存在")


@router.post("/equipment/{equipment_id}/anomaly-check")
def anomaly_check(equipment_id: int, db: Session = Depends(get_db)):
    """孤立森林异常检测；检出异常自动生成「传感器异常」预警。"""
    _ensure_equipment(db, equipment_id)
    try:
        result = check_device_anomaly(db, equipment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return success(result, message="异常检测完成")


@router.post("/equipment/{equipment_id}/diagnose")
def diagnose(equipment_id: int, payload: DiagnoseRequest, db: Session = Depends(get_db)):
    """专家系统 IF-THEN 规则诊断；可选自动生成工单。"""
    _ensure_equipment(db, equipment_id)
    try:
        result = diagnose_device(db, equipment_id, cycle=payload.cycle, create_order=payload.create_order)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return success(result, message="诊断完成")
