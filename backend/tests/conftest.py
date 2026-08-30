# -*- coding: utf-8 -*-
"""pytest 公共夹具：独立临时数据库 + TestClient。

测试使用内存 SQLite（StaticPool），不触碰 data/equipment.db。
"""

import sys
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Alert, Equipment, SensorData, WorkOrder  # noqa: E402


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_engine):
    Session = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_data(db_engine):
    """构造两台设备 + 少量传感器数据 + 一条预警/工单，供各接口测试。"""
    Session = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
    db = Session()

    eq1 = Equipment(
        device_code="DEV001", name="车间设备001", model="CMAPSS-FD001",
        station="工位01", install_date=date(2024, 1, 1),
        twin_status="运行", health_grade="健康",
    )
    eq2 = Equipment(
        device_code="DEV002", name="车间设备002", model="CMAPSS-FD001",
        station="工位01", install_date=date(2024, 2, 1),
        twin_status="报警", health_grade="严重",
    )
    db.add_all([eq1, eq2])
    db.commit()
    db.refresh(eq1)
    db.refresh(eq2)

    def _sensor(eq, cycle, score=90.0, anomaly=0):
        return SensorData(
            equipment_id=eq.id, cycle=cycle, rul=float(200 - cycle),
            health_score=score, health_grade="健康" if score >= 75 else "预警",
            anomaly_label=anomaly,
            op_setting_1=10.0, op_setting_2=20.0,
            op_setting_1_norm=0.1, op_setting_2_norm=0.2,
            sensor_2=600.0, sensor_3=1600.0, sensor_4=1500.0, sensor_6=2200.0,
            sensor_7=550.0, sensor_8=2400.0, sensor_9=17800.0, sensor_11=48.0,
            sensor_12=520.0, sensor_13=23800.0, sensor_14=8100.0, sensor_15=8.0,
            sensor_17=390.0, sensor_20=39.0, sensor_21=23.0,
            sensor_2_norm=0.5, sensor_3_norm=0.5, sensor_4_norm=0.5, sensor_6_norm=0.5,
            sensor_7_norm=0.5, sensor_8_norm=0.5, sensor_9_norm=0.5, sensor_11_norm=0.5,
            sensor_12_norm=0.5, sensor_13_norm=0.5, sensor_14_norm=0.5, sensor_15_norm=0.5,
            sensor_17_norm=0.5, sensor_20_norm=0.5, sensor_21_norm=0.5,
        )

    db.add_all([
        _sensor(eq1, 1), _sensor(eq1, 2), _sensor(eq1, 3),
        _sensor(eq2, 1, score=10.0, anomaly=1), _sensor(eq2, 2, score=10.0, anomaly=1),
    ])
    db.commit()

    alert = Alert(
        equipment_id=eq2.id, alert_type="健康度过低", level="严重",
        message="健康度严重偏低", sensor_point="health_score",
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    order = WorkOrder(
        alert_id=alert.id, equipment_id=eq2.id, title="健康度过低-严重",
        description="健康度严重偏低", diagnosis="请排查", status="待处理",
    )
    db.add(order)
    db.commit()

    # 在关闭会话前读取 id（关闭后访问会触发过期刷新）
    ids = {"eq1_id": eq1.id, "eq2_id": eq2.id, "alert_id": alert.id, "order_id": order.id}
    db.close()
    return ids
