# -*- coding: utf-8 -*-
"""路由统一导出。"""

from .equipment import router as equipment_router
from .sensor import router as sensor_router
from .evaluation import router as evaluation_router
from .alert import router as alert_router
from .work_order import router as work_order_router

ALL_ROUTERS = [
    equipment_router,
    sensor_router,
    evaluation_router,
    alert_router,
    work_order_router,
]
