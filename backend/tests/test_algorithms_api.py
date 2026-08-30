# -*- coding: utf-8 -*-
"""算法服务接口测试：异常检测 / 专家诊断 / 随机森林评估。"""


def test_anomaly_check(client, sample_data):
    resp = client.post(f"/api/v1/equipment/{sample_data['eq2_id']}/anomaly-check")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert "is_anomaly" in data
    assert 0 <= data["anomaly_score"] <= 1
    assert "message" in data


def test_anomaly_check_device_not_found(client, sample_data):
    resp = client.post("/api/v1/equipment/9999/anomaly-check")
    assert resp.status_code == 404


def test_diagnose_returns_rules(client, sample_data):
    resp = client.post(f"/api/v1/equipment/{sample_data['eq2_id']}/diagnose", json={})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "diagnoses" in data
    assert isinstance(data["diagnoses"], list)
    # DEV002 健康度 10 → 应命中 R001
    codes = {d["code"] for d in data["diagnoses"]}
    assert "R001" in codes
    assert "fault_part" in data["diagnoses"][0]
    assert "steps" in data["diagnoses"][0]
    assert "advice" in data["diagnoses"][0]


def test_diagnose_create_order(client, sample_data):
    resp = client.post(
        f"/api/v1/equipment/{sample_data['eq2_id']}/diagnose",
        json={"create_order": True},
    )
    assert resp.status_code == 200
    orders = client.get(
        "/api/v1/work-orders", params={"equipment_id": sample_data["eq2_id"]}).json()["data"]["items"]
    assert len(orders) >= 2  # 原有 1 条 + 诊断生成 1 条


def test_diagnose_no_data(client, db_engine):
    from sqlalchemy.orm import sessionmaker
    from app.models import Equipment
    Session = sessionmaker(bind=db_engine)
    db = Session()
    eq = Equipment(device_code="DEVX2", name="无数据设备", model="X", station="S")
    db.add(eq)
    db.commit()
    db.refresh(eq)
    eq_id = eq.id
    db.close()

    resp = client.post(f"/api/v1/equipment/{eq_id}/diagnose", json={})
    assert resp.status_code == 400


def test_evaluate_uses_rf(client, sample_data):
    resp = client.post(f"/api/v1/equipment/{sample_data['eq1_id']}/evaluate", json={})
    assert resp.status_code == 201
    detail = resp.json()["data"]["detail"]
    assert "随机森林" in detail
