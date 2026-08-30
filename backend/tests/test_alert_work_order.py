# -*- coding: utf-8 -*-
"""预警与运维工单接口测试（预警→工单闭环）。"""


def test_list_alerts(client, sample_data):
    resp = client.get("/api/v1/alerts")
    body = resp.json()
    assert body["code"] == 0
    assert len(body["data"]["items"]) == 1


def test_filter_alerts_by_level(client, sample_data):
    resp = client.get("/api/v1/alerts", params={"level": "严重"})
    assert len(resp.json()["data"]["items"]) == 1
    resp2 = client.get("/api/v1/alerts", params={"level": "提示"})
    assert len(resp2.json()["data"]["items"]) == 0


def test_create_alert(client, sample_data):
    payload = {
        "equipment_id": sample_data["eq1_id"],
        "alert_type": "传感器异常",
        "level": "警告",
        "message": "sensor_11 漂移",
        "sensor_point": "sensor_11",
    }
    resp = client.post("/api/v1/alerts", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["data"]["alert_type"] == "传感器异常"
    assert body["data"]["is_handled"] is False


def test_create_alert_invalid_level(client, sample_data):
    payload = {"equipment_id": sample_data["eq1_id"], "alert_type": "传感器异常", "level": "未知级别"}
    resp = client.post("/api/v1/alerts", json=payload)
    assert resp.status_code == 400


def test_handle_alert(client, sample_data):
    resp = client.patch(f"/api/v1/alerts/{sample_data['alert_id']}/handle")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["is_handled"] is True


def test_create_work_order_from_alert(client, sample_data):
    payload = {
        "alert_id": sample_data["alert_id"],
        "equipment_id": sample_data["eq2_id"],
        "title": "健康度过低-严重",
    }
    resp = client.post("/api/v1/work-orders", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["data"]["alert_id"] == sample_data["alert_id"]
    assert body["data"]["status"] == "待处理"
    # 关联预警应被标记处理
    alert = client.get("/api/v1/alerts", params={"level": "严重"}).json()["data"]["items"]
    handled = [a for a in alert if a["id"] == sample_data["alert_id"]][0]
    assert handled["is_handled"] is True


def test_list_work_orders(client, sample_data):
    resp = client.get("/api/v1/work-orders")
    body = resp.json()
    assert body["data"]["items"][0]["title"] == "健康度过低-严重"


def test_update_work_order_status(client, sample_data):
    order_id = sample_data["order_id"]
    resp = client.patch(f"/api/v1/work-orders/{order_id}/status", json={"status": "维修中"})
    assert resp.json()["data"]["status"] == "维修中"
    resp2 = client.patch(f"/api/v1/work-orders/{order_id}/status", json={"status": "已完成"})
    assert resp2.json()["data"]["status"] == "已完成"


def test_update_work_order_invalid_status(client, sample_data):
    resp = client.patch(
        f"/api/v1/work-orders/{sample_data['order_id']}/status", json={"status": "未知"})
    assert resp.status_code == 400


def test_work_order_not_found(client, sample_data):
    resp = client.patch("/api/v1/work-orders/9999/status", json={"status": "已完成"})
    assert resp.status_code == 404
