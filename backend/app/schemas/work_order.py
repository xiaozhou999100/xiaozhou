# -*- coding: utf-8 -*-
"""运维工单请求与响应模型。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkOrderCreate(BaseModel):
    """创建工单入参（支持从预警一键生成）。"""

    alert_id: Optional[int] = Field(None, description="关联预警ID（预警生成工单）")
    equipment_id: int
    title: str = Field(..., description="工单标题")
    description: str = Field("", description="工单描述")
    diagnosis: str = Field("", description="诊断建议")


class WorkOrderStatusUpdate(BaseModel):
    """更新工单状态入参。"""

    status: str = Field(..., description="状态: 待处理/维修中/已完成")


class WorkOrderOut(BaseModel):
    """工单响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_id: Optional[int]
    equipment_id: int
    title: str
    description: str
    diagnosis: str
    status: str
    created_at: datetime
    updated_at: datetime
