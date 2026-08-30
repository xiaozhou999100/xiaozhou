# -*- coding: utf-8 -*-
"""健康/能耗评估请求与响应模型。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EvaluationCreate(BaseModel):
    """触发评估入参（可选指定评估时间点/周期）。"""

    cycle: Optional[int] = Field(None, description="指定评估的运行周期，缺省取最新")


class EvaluationOut(BaseModel):
    """评估记录响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    equipment_id: int
    eval_time: datetime
    health_score: float
    energy_efficiency: float
    load_rate: float
    health_grade: str
    detail: str
