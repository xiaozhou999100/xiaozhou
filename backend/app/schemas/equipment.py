# -*- coding: utf-8 -*-
"""设备台账请求/响应模型。"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EquipmentCreate(BaseModel):
    """创建设备入参。"""

    device_code: str = Field(..., description="设备编号", examples=["DEV101"])
    name: str = Field(..., description="设备名称")
    model: str = Field("", description="型号")
    station: str = Field("", description="工位")
    install_date: Optional[date] = Field(None, description="投运日期")
    twin_status: str = Field("运行", description="孪生状态: 运行/待机/报警")
    health_grade: str = Field("健康", description="健康等级")
    description: str = Field("", description="备注")


class EquipmentUpdate(BaseModel):
    """更新设备入参（字段可选）。"""

    name: Optional[str] = None
    model: Optional[str] = None
    station: Optional[str] = None
    install_date: Optional[date] = None
    twin_status: Optional[str] = None
    health_grade: Optional[str] = None
    description: Optional[str] = None


class EquipmentOut(BaseModel):
    """设备响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_code: str
    name: str
    model: str
    station: str
    install_date: Optional[date]
    twin_status: str
    health_grade: str
    description: str
    created_at: datetime
