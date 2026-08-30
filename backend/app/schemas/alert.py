# -*- coding: utf-8 -*-
"""预警请求与响应模型。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AlertCreate(BaseModel):
    """创建预警入参。"""

    equipment_id: int
    alert_type: str = Field(..., description="预警类型: 传感器异常/能耗超标/健康度过低/节拍异常")
    level: str = Field("提示", description="级别: 提示/警告/严重")
    message: str = Field("", description="预警内容")
    sensor_point: str = Field("", description="关联传感器点位")


class AlertOut(BaseModel):
    """预警记录响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    equipment_id: int
    alert_type: str
    level: str
    message: str
    sensor_point: str
    is_handled: bool
    created_at: datetime
