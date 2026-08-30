# -*- coding: utf-8 -*-
"""设备台账接口测试：增删改查。"""


def test_list_equipment(client, sample_data):
    resp = client.get("/api/v1/equipment")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 2
    assert len(body["data"]["items"]) == 2


def test_filter_by_health_grade(client, sample_data):
    resp = client.get("/api/v1/equipment", params={"health_grade": "严重"})
    body = resp.json()
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["health_grade"] == "严重"


def test_filter_by_keyword(client, sample_data):
    resp = client.get("/api/v1/equipment", params={"keyword": "DEV002"})
    body = resp.json()
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["device_code"] == "DEV002"


def test_create_equipment(client, sample_data):
    payload = {
        "device_code": "DEV003",
        "name": "车间设备003",
        "model": "CMAPSS-FD001",
        "station": "工位02",
        "twin_status": "待机",
        "health_grade": "注意",
    }
    resp = client.post("/api/v1/equipment", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["device_code"] == "DEV003"


def test_create_duplicate_device_code(client, sample_data):
    payload = {"device_code": "DEV001", "name": "重复设备"}
    resp = client.post("/api/v1/equipment", json=payload)
    assert resp.status_code == 400


def test_get_equipment(client, sample_data):
    resp = client.get(f"/api/v1/equipment/{sample_data['eq1_id']}")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["device_code"] == "DEV001"


def test_get_equipment_not_found(client, sample_data):
    resp = client.get("/api/v1/equipment/9999")
    assert resp.status_code == 404


def test_update_equipment(client, sample_data):
    resp = client.put(f"/api/v1/equipment/{sample_data['eq1_id']}", json={"health_grade": "预警"})
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["health_grade"] == "预警"


def test_delete_equipment(client, sample_data):
    resp = client.delete(f"/api/v1/equipment/{sample_data['eq1_id']}")
    assert resp.json()["code"] == 0
    # 删除后传感器数据应级联删除
    resp2 = client.get("/api/v1/equipment")
    assert resp2.json()["data"]["total"] == 1
