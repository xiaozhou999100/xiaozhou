# -*- coding: utf-8 -*-
"""FastAPI 应用入口：创建 app、创建表、挂载路由。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import ALL_ROUTERS
from .schemas import success

app = FastAPI(
    title="数字孪生车间智能监控与运维平台 API",
    description="设备台账 / 数字孪生可视化 / 实时监测 / 健康评估 / 预警 / 运维工单 闭环接口",
    version="0.2.0",
)

# 允许本地前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 建表（已存在则跳过）
Base.metadata.create_all(bind=engine)


@app.get("/api/v1/health", tags=["系统"])
def health_check():
    """服务健康检查。"""
    return success({"status": "ok", "service": "digital-twin-workshop"})


for router in ALL_ROUTERS:
    app.include_router(router)
