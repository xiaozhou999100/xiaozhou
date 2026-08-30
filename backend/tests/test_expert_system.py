# -*- coding: utf-8 -*-
"""专家系统规则库单元测试。"""

from app.algorithms.expert_system import RULES, diagnose, rule_count

LEVELS = {"提示", "警告", "严重"}


def test_rule_count():
    assert rule_count() == 20


def test_rules_structure():
    for rule in RULES:
        assert rule.code.startswith("R")
        assert rule.name
        assert rule.level in LEVELS
        assert rule.fault_part
        assert isinstance(rule.steps, list) and len(rule.steps) >= 1
        assert rule.advice
        assert callable(rule.check)


def test_healthy_context_no_severe():
    ctx = {
        "health_score": 90.0,
        "health_grade": "健康",
        "load_rate": 50.0,
        "energy_efficiency": 90.0,
        "is_anomaly": False,
        "anomaly_score": 0.1,
        "sensors": {f"sensor_{i}": 0.3 for i in [2, 3, 4, 7, 9, 11, 12, 13, 14, 15, 17, 20, 21]},
    }
    result = diagnose(ctx)
    levels = {r["level"] for r in result}
    assert "严重" not in levels
    assert all(r["code"].startswith("R") for r in result)


def test_low_health_triggers_r001():
    ctx = {
        "health_score": 10.0,
        "health_grade": "严重",
        "load_rate": 50.0,
        "energy_efficiency": 90.0,
        "is_anomaly": True,
        "anomaly_score": 0.8,
        "sensors": {f"sensor_{i}": 0.3 for i in [2, 3, 4, 7, 9, 11, 12, 13, 14, 15, 17, 20, 21]},
    }
    result = diagnose(ctx)
    codes = {r["code"] for r in result}
    assert "R001" in codes


def test_high_sensor_triggers_rule():
    ctx = {
        "health_score": 80.0,
        "health_grade": "健康",
        "load_rate": 50.0,
        "energy_efficiency": 90.0,
        "is_anomaly": False,
        "anomaly_score": 0.1,
        "sensors": {f"sensor_{i}": 0.3 for i in [2, 3, 4, 7, 9, 11, 12, 13, 14, 15, 17, 20, 21]},
    }
    ctx["sensors"]["sensor_13"] = 0.95   # HPT 出口温度偏高 → R005
    result = diagnose(ctx)
    codes = {r["code"] for r in result}
    assert "R005" in codes


def test_multi_sensor_triggers_r014():
    ctx = {
        "health_score": 60.0,
        "health_grade": "注意",
        "load_rate": 50.0,
        "energy_efficiency": 90.0,
        "is_anomaly": False,
        "anomaly_score": 0.1,
        "sensors": {f"sensor_{i}": 0.3 for i in [2, 3, 4, 7, 9, 11, 12, 13, 14, 15, 17, 20, 21]},
    }
    for s in ["sensor_2", "sensor_11", "sensor_13", "sensor_14"]:
        ctx["sensors"][s] = 0.9
    result = diagnose(ctx)
    codes = {r["code"] for r in result}
    assert "R014" in codes


def test_result_sorted_by_severity():
    ctx = {
        "health_score": 10.0,
        "health_grade": "严重",
        "load_rate": 95.0,            # R011 提示
        "energy_efficiency": 30.0,    # R012 警告
        "is_anomaly": True,
        "anomaly_score": 0.9,         # R013 警告
        "sensors": {f"sensor_{i}": 0.3 for i in [2, 3, 4, 7, 9, 11, 12, 13, 14, 15, 17, 20, 21]},
    }
    result = diagnose(ctx)
    levels = [r["level"] for r in result]
    assert levels == sorted(levels, key=lambda l: {"严重": 0, "警告": 1, "提示": 2}[l])
