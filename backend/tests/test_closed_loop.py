# -*- coding: utf-8 -*-
"""阶段5：预警-诊断-工单闭环集成测试。

覆盖完整业务闭环：异常检测 → 风险预警 → 专家诊断 → 工单生成 → 工单状态流转 → 预警闭环。
模型采用已固化的随机森林/孤立森林（backend/app/model_files），测试库为独立临时库。
"""


def _count_orders(client, equipment_id):
    return len(
        client.get("/api/v1/work-orders", params={"equipment_id": equipment_id}).json()["data"]["items"]
    )


def _count_alerts(client, equipment_id):
    return len(
        client.get("/api/v1/alerts", params={"equipment_id": equipment_id}).json()["data"]["items"]
    )


def test_anomaly_to_alert(client, sample_data):
    """环节1-2：孤立森林异常检测，检出异常则自动生成「传感器异常」预警。"""
    eq = sample_data["eq2_id"]
    before = _count_alerts(client, eq)
    resp = client.post(f"/api/v1/equipment/{eq}/anomaly-check")
    assert resp.status_code == 200
    data = resp.json()["data"]
    after = _count_alerts(client, eq)
    if data["is_anomaly"]:
        assert after == before + 1          # 异常 → 预警
        assert any(a["alert_type"] == "传感器异常" for a in
                   client.get("/api/v1/alerts", params={"equipment_id": eq}).json()["data"]["items"])
    else:
        assert after == before              # 正常 → 不产生预警


def test_diagnose_to_workorder(client, sample_data):
    """环节3-4：专家系统诊断，严重/警告级别命中则自动生成工单。"""
    eq = sample_data["eq2_id"]
    before = _count_orders(client, eq)
    resp = client.post(f"/api/v1/equipment/{eq}/diagnose", json={"create_order": True})
    assert resp.status_code == 200
    diagnoses = resp.json()["data"]["diagnoses"]
    auto_levels = [d for d in diagnoses if d["level"] in ("严重", "警告")]
    after = _count_orders(client, eq)
    assert after == before + len(auto_levels)   # 严重/警告数 = 新增工单数
    # 诊断结果结构完整
    assert all({"code", "name", "level", "fault_part", "steps", "advice"} <= set(d) for d in diagnoses)


def test_workorder_status_flow(client, sample_data):
    """环节5：工单状态流转 待处理→维修中→已完成。"""
    oid = sample_data["order_id"]
    resp = client.patch(f"/api/v1/work-orders/{oid}/status", json={"status": "维修中"})
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "维修中"
    resp = client.patch(f"/api/v1/work-orders/{oid}/status", json={"status": "已完成"})
    assert resp.json()["data"]["status"] == "已完成"


def test_alert_to_workorder_and_handle(client, sample_data):
    """环节4b：预警一键生成工单，生成后预警自动标记处理。"""
    aid = sample_data["alert_id"]
    eq = sample_data["eq2_id"]
    before = _count_orders(client, eq)
    resp = client.post("/api/v1/work-orders", json={
        "alert_id": aid, "equipment_id": eq, "title": "[预警]健康度过低",
        "description": "由预警自动生成",
    })
    assert resp.status_code == 201
    assert _count_orders(client, eq) == before + 1
    # 预警已处理
    alerts = client.get("/api/v1/alerts", params={"equipment_id": eq}).json()["data"]["items"]
    assert any(a["id"] == aid and a["is_handled"] for a in alerts)


def test_full_closed_loop(client, sample_data):
    """全链路：异常检测→预警→诊断→工单→状态流转→完成。"""
    eq = sample_data["eq2_id"]
    alerts0 = _count_alerts(client, eq)
    orders0 = _count_orders(client, eq)

    # 1) 异常检测（可能生成预警）
    ano = client.post(f"/api/v1/equipment/{eq}/anomaly-check").json()["data"]
    alerts1 = _count_alerts(client, eq)
    if ano["is_anomaly"]:
        assert alerts1 == alerts0 + 1

    # 2) 专家诊断（严重/警告生成工单）
    diag = client.post(f"/api/v1/equipment/{eq}/diagnose", json={"create_order": True}).json()["data"]
    auto_n = len([d for d in diag["diagnoses"] if d["level"] in ("严重", "警告")])
    orders1 = _count_orders(client, eq)
    assert orders1 == orders0 + auto_n

    # 3) 若产生了工单，则走完整状态流转
    if orders1 > orders0:
        orders = client.get("/api/v1/work-orders", params={"equipment_id": eq}).json()["data"]["items"]
        for target in ("维修中", "已完成"):
            resp = client.patch(f"/api/v1/work-orders/{orders[0]['id']}/status", json={"status": target})
            assert resp.json()["data"]["status"] == target
        assert orders[0]["diagnosis"]              # 工单应含诊断建议

    # 4) 预警若未处理，则从预警生成工单闭环
    alerts = client.get("/api/v1/alerts", params={"equipment_id": eq}).json()["data"]["items"]
    unhandled = [a for a in alerts if not a["is_handled"]]
    for a in unhandled:
        client.post("/api/v1/work-orders", json={
            "alert_id": a["id"], "equipment_id": eq, "title": f"[预警]{a['alert_type']}",
        })
    alerts_final = client.get("/api/v1/alerts", params={"equipment_id": eq}).json()["data"]["items"]
    assert all(a["is_handled"] for a in alerts_final)   # 全部预警闭环处理
