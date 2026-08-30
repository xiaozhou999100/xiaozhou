# -*- coding: utf-8 -*-
"""预警中心路由：自动预警生成/查询/标记处理。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import ALERT_LEVELS
from ..database import get_db
from ..models import Alert, Equipment
from ..schemas import AlertCreate, AlertOut, success

router = APIRouter(prefix="/api/v1/alerts", tags=["预警中心"])


@router.get("")
def list_alerts(
    equipment_id: Optional[int] = None,
    level: Optional[str] = None,
    is_handled: Optional[bool] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """预警列表（支持按设备/级别/处理状态筛选）。"""
    query = db.query(Alert)
    if equipment_id is not None:
        query = query.filter(Alert.equipment_id == equipment_id)
    if level:
        query = query.filter(Alert.level == level)
    if is_handled is not None:
        query = query.filter(Alert.is_handled == is_handled)

    rows = query.order_by(Alert.created_at.desc()).limit(min(max(limit, 1), 1000)).all()
    return success({
        "items": [AlertOut.model_validate(r).model_dump() for r in rows],
    })


@router.post("", status_code=201)
def create_alert(payload: AlertCreate, db: Session = Depends(get_db)):
    """创建预警（由异常检测/规则引擎调用）。"""
    if not db.get(Equipment, payload.equipment_id):
        raise HTTPException(status_code=404, detail="设备不存在")
    if payload.level not in ALERT_LEVELS:
        raise HTTPException(status_code=400, detail=f"级别须为: {'/'.join(ALERT_LEVELS)}")

    alert = Alert(**payload.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return success(AlertOut.model_validate(alert).model_dump(), message="预警已生成")


@router.patch("/{alert_id}/handle")
def handle_alert(alert_id: int, db: Session = Depends(get_db)):
    """将预警标记为已处理。"""
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="预警不存在")
    alert.is_handled = True
    db.commit()
    db.refresh(alert)
    return success(AlertOut.model_validate(alert).model_dump(), message="已标记处理")
