# -*- coding: utf-8 -*-
"""设备台账路由：增删改查。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..config import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from ..database import get_db
from ..models import Equipment
from ..schemas import EquipmentCreate, EquipmentOut, EquipmentUpdate, success

router = APIRouter(prefix="/api/v1/equipment", tags=["设备台账"])


@router.get("")
def list_equipment(
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    keyword: Optional[str] = None,
    health_grade: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """设备台账列表（支持关键字/健康等级筛选 + 分页）。"""
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    query = db.query(Equipment)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(
            Equipment.device_code.like(like),
            Equipment.name.like(like),
            Equipment.station.like(like),
            Equipment.model.like(like),
        ))
    if health_grade:
        query = query.filter(Equipment.health_grade == health_grade)

    total = query.count()
    items = query.order_by(Equipment.id).offset((page - 1) * page_size).limit(page_size).all()
    return success({
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [EquipmentOut.model_validate(e).model_dump() for e in items],
    })


@router.post("", status_code=201)
def create_equipment(payload: EquipmentCreate, db: Session = Depends(get_db)):
    """新增设备。"""
    exists = db.query(Equipment).filter(Equipment.device_code == payload.device_code).first()
    if exists:
        raise HTTPException(status_code=400, detail=f"设备编号 {payload.device_code} 已存在")

    equipment = Equipment(**payload.model_dump())
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return success(EquipmentOut.model_validate(equipment).model_dump(), message="创建成功")


@router.get("/{equipment_id}")
def get_equipment(equipment_id: int, db: Session = Depends(get_db)):
    """设备详情。"""
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="设备不存在")
    return success(EquipmentOut.model_validate(equipment).model_dump())


@router.put("/{equipment_id}")
def update_equipment(equipment_id: int, payload: EquipmentUpdate, db: Session = Depends(get_db)):
    """更新设备信息。"""
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="设备不存在")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(equipment, field, value)
    db.commit()
    db.refresh(equipment)
    return success(EquipmentOut.model_validate(equipment).model_dump(), message="更新成功")


@router.delete("/{equipment_id}")
def delete_equipment(equipment_id: int, db: Session = Depends(get_db)):
    """删除设备（级联删除其传感器数据/评估/预警/工单）。"""
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="设备不存在")
    db.delete(equipment)
    db.commit()
    return success(message="删除成功")
