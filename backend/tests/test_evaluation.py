# -*- coding: utf-8 -*-
"""健康评估接口测试。"""


def test_evaluate_healthy_device(client, sample_data):
    resp = client.post(f"/api/v1/equipment/{sample_data['eq1_id']}/evaluate", json={})
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert "随机森林" in data["detail"]        # 使用机器学习评估
    assert 0 <= data["health_score"] <= 100
    assert 0 <= data["load_rate"] <= 100
    assert 0 <= data["energy_efficiency"] <= 100
    assert data["health_grade"] in ("健康", "注意", "预警", "严重")


def test_evaluate_warning_device(client, sample_data):
    resp = client.post(f"/api/v1/equipment/{sample_data['eq2_id']}/evaluate", json={})
    data = resp.json()["data"]
    assert 0 <= data["health_score"] <= 100
    assert "随机森林" in data["detail"]


def test_evaluate_updates_equipment_grade(client, sample_data):
    eval_resp = client.post(f"/api/v1/equipment/{sample_data['eq2_id']}/evaluate", json={})
    eval_grade = eval_resp.json()["data"]["health_grade"]
    resp = client.get(f"/api/v1/equipment/{sample_data['eq2_id']}")
    # 设备台账健康等级应与最新评估结果一致
    assert resp.json()["data"]["health_grade"] == eval_grade


def test_list_evaluations(client, sample_data):
    client.post(f"/api/v1/equipment/{sample_data['eq1_id']}/evaluate", json={})
    client.post(f"/api/v1/equipment/{sample_data['eq1_id']}/evaluate", json={})
    resp = client.get(f"/api/v1/equipment/{sample_data['eq1_id']}/evaluations")
    body = resp.json()
    assert body["code"] == 0
    assert len(body["data"]["items"]) == 2


def test_evaluate_no_data(client, db_engine, sample_data):
    # 用空库构造的设备（无传感器数据）应返回 400
    from sqlalchemy.orm import sessionmaker
    from app.database import Base
    from app.models import Equipment
    Session = sessionmaker(bind=db_engine)
    db = Session()
    eq = Equipment(device_code="DEVX", name="无数据设备", model="X", station="S")
    db.add(eq)
    db.commit()
    db.refresh(eq)
    eq_id = eq.id
    db.close()

    resp = client.post(f"/api/v1/equipment/{eq_id}/evaluate", json={})
    assert resp.status_code == 400
