# -*- coding: utf-8 -*-
"""传感器数据接口测试。"""


def test_sensor_data_series(client, sample_data):
    resp = client.get(f"/api/v1/equipment/{sample_data['eq1_id']}/sensor-data")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    items = body["data"]["items"]
    assert len(items) == 3
    # 时间正序
    cycles = [it["cycle"] for it in items]
    assert cycles == sorted(cycles)
    # 含归一化传感器字段
    assert "sensor_2_norm" in items[0]


def test_sensor_data_normalized_only(client, sample_data):
    resp = client.get(
        f"/api/v1/equipment/{sample_data['eq1_id']}/sensor-data",
        params={"normalized": "true", "limit": 2},
    )
    body = resp.json()
    items = body["data"]["items"]
    assert len(items) == 2
    assert "sensor_2" not in items[0]          # 非归一化原始列不应返回
    assert "sensor_2_norm" in items[0]
    assert "anomaly_label" in items[0]


def test_sensor_data_cycle_range(client, sample_data):
    resp = client.get(
        f"/api/v1/equipment/{sample_data['eq1_id']}/sensor-data",
        params={"start_cycle": 2, "end_cycle": 3},
    )
    items = resp.json()["data"]["items"]
    assert [it["cycle"] for it in items] == [2, 3]


def test_sensor_data_anomaly_flag(client, sample_data):
    resp = client.get(f"/api/v1/equipment/{sample_data['eq2_id']}/sensor-data")
    items = resp.json()["data"]["items"]
    assert all(it["anomaly_label"] == 1 for it in items)


def test_sensor_record_detail(client, sample_data):
    # 先取一条记录 id
    resp = client.get(f"/api/v1/equipment/{sample_data['eq1_id']}/sensor-data", params={"limit": 1})
    record_id = resp.json()["data"]["items"][0]["id"]
    detail = client.get(f"/api/v1/sensor-data/{record_id}")
    assert detail.json()["data"]["cycle"] == 3  # 最近一条


def test_sensor_data_device_not_found(client, sample_data):
    resp = client.get("/api/v1/equipment/9999/sensor-data")
    assert resp.status_code == 404
