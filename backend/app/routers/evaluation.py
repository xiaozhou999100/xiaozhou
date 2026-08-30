# -*- coding: utf-8 -*-
"""健康/能耗评估路由。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Equipment, HealthEvaluation
from ..schemas import EvaluationCreate, EvaluationOut, success
from ..services.health import evaluate_device

router = APIRouter(prefix="/api/v1", tags=["健康评估"])


@router.get("/equipment/{equipment_id}/evaluations")
def list_evaluations(
    equipment_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """设备历史评估记录（时间倒序）。"""
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="设备不存在")

    rows = (db.query(HealthEvaluation)
            .filter(HealthEvaluation.equipment_id == equipment_id)
            .order_by(HealthEvaluation.eval_time.desc())
            .limit(min(max(limit, 1), 500))
            .all())
    return success({
        "equipment_id": equipment_id,
        "items": [EvaluationOut.model_validate(r).model_dump() for r in rows],
    })


@router.post("/equipment/{equipment_id}/evaluate", status_code=201)
def create_evaluation(equipment_id: int, payload: EvaluationCreate, db: Session = Depends(get_db)):
    """触发一次健康/能耗评估。"""
    try:
        record = evaluate_device(db, equipment_id, cycle=payload.cycle)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return success(EvaluationOut.model_validate(record).model_dump(), message="评估完成")
