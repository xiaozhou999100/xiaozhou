# -*- coding: utf-8 -*-
"""运维工单路由：预警一键生成工单，状态流转。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import WORK_ORDER_STATUS
from ..database import get_db
from ..models import Alert, Equipment, WorkOrder
from ..schemas import WorkOrderCreate, WorkOrderOut, WorkOrderStatusUpdate, success

router = APIRouter(prefix="/api/v1/work-orders", tags=["运维工单"])


@router.get("")
def list_work_orders(
    equipment_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """工单列表（支持按设备/状态筛选）。"""
    query = db.query(WorkOrder)
    if equipment_id is not None:
        query = query.filter(WorkOrder.equipment_id == equipment_id)
    if status:
        query = query.filter(WorkOrder.status == status)

    rows = query.order_by(WorkOrder.created_at.desc()).limit(min(max(limit, 1), 1000)).all()
    return success({
        "items": [WorkOrderOut.model_validate(r).model_dump() for r in rows],
    })


@router.post("", status_code=201)
def create_work_order(payload: WorkOrderCreate, db: Session = Depends(get_db)):
    """创建工单；若传入 alert_id 则从预警一键生成并关联。"""
    if not db.get(Equipment, payload.equipment_id):
        raise HTTPException(status_code=404, detail="设备不存在")

    alert = None
    if payload.alert_id is not None:
        alert = db.get(Alert, payload.alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="关联预警不存在")

    order = WorkOrder(**payload.model_dump())
    if alert:
        # 预警生成工单：自动带入预警内容与诊断建议
        order.description = order.description or alert.message
        order.diagnosis = order.diagnosis or f"关联预警[{alert.alert_type}/{alert.level}]，请按点位排查"
        alert.is_handled = True

    db.add(order)
    db.commit()
    db.refresh(order)
    return success(WorkOrderOut.model_validate(order).model_dump(), message="工单已生成")


@router.patch("/{order_id}/status")
def update_work_order_status(order_id: int, payload: WorkOrderStatusUpdate, db: Session = Depends(get_db)):
    """更新工单状态：待处理 → 维修中 → 已完成。"""
    order = db.get(WorkOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    if payload.status not in WORK_ORDER_STATUS:
        raise HTTPException(status_code=400, detail=f"状态须为: {'/'.join(WORK_ORDER_STATUS)}")

    order.status = payload.status
    db.commit()
    db.refresh(order)
    return success(WorkOrderOut.model_validate(order).model_dump(), message="状态已更新")
