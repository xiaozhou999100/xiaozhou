# -*- coding: utf-8 -*-
"""专家系统模块：IF-THEN 规则引擎。

基于设备实时状态（健康度、关键传感器归一化值、负载、能耗、异常分数），
通过 20 条左右可解释的 IF-THEN 规则进行故障诊断，输出故障部位、排查步骤与维修建议。

规则输入（context）字段：
    health_score / health_grade / load_rate / energy_efficiency
    is_anomaly / anomaly_score（孤立森林异常度 0~1）
    sensors: {sensor_xx: 归一化值 0~1}
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List

# 关键传感器阈值（归一化值）
SENSOR_HIGH = 0.85


@dataclass
class Rule:
    """一条 IF-THEN 诊断规则。"""

    code: str
    name: str
    level: str                      # 提示/警告/严重
    fault_part: str                 # 故障部位
    steps: List[str]                # 排查步骤
    advice: str                     # 维修建议
    check: Callable[[dict], bool]   # 条件函数


def _sensor(ctx: dict, name: str, default: float = 0.0) -> float:
    return float(ctx.get("sensors", {}).get(name, default))


def _count_high_sensors(ctx: dict, names: List[str], threshold: float = SENSOR_HIGH) -> int:
    return sum(1 for n in names if _sensor(ctx, n) >= threshold)


# ----------------------------------------------------------------------------
# 规则库（20 条）
# ----------------------------------------------------------------------------
RULES: List[Rule] = [
    Rule(
        code="R001", name="健康度严重不足", level="严重", fault_part="高压压气机(HPC)/整机",
        steps=["查看健康度与 RUL 趋势曲线", "核对最近 30 周期关键传感器均值", "确认是否进入快速退化阶段"],
        advice="建议停机检修，重点检查 HPC 退化情况，必要时更换相关部件",
        check=lambda c: c.get("health_score", 100) < 25,
    ),
    Rule(
        code="R002", name="健康度预警", level="警告", fault_part="整机",
        steps=["对比健康度下降速率", "查看异常传感器点位", "缩短巡检周期"],
        advice="加强监控并安排计划性检修，密切观察退化趋势",
        check=lambda c: 25 <= c.get("health_score", 100) < 50,
    ),
    Rule(
        code="R003", name="健康度关注", level="提示", fault_part="整机",
        steps=["记录当前健康基线", "关注传感器波动"],
        advice="维持常规巡检，暂无需停机",
        check=lambda c: 50 <= c.get("health_score", 100) < 75,
    ),
    Rule(
        code="R004", name="HPT出口静压异常", level="警告", fault_part="高压涡轮(HPT)",
        steps=["核对 sensor_11 时序", "对比同工位设备", "检查 HPT 叶片磨损"],
        advice="检查高压涡轮出口静压传感器与 HPT 叶片状态",
        check=lambda c: _sensor(c, "sensor_11") >= SENSOR_HIGH,
    ),
    Rule(
        code="R005", name="HPT出口温度偏高", level="严重", fault_part="高压涡轮(HPT)/燃烧室",
        steps=["查看 sensor_13 温度趋势", "检查燃油供给", "评估燃烧效率"],
        advice="警惕涡轮过热，立即排查燃烧室与燃油系统",
        check=lambda c: _sensor(c, "sensor_13") >= SENSOR_HIGH,
    ),
    Rule(
        code="R006", name="LPT出口温度偏高", level="警告", fault_part="低压涡轮(LPT)",
        steps=["核对 sensor_14 时序", "检查排气路径"],
        advice="检查低压涡轮出口温度传感器与排气系统",
        check=lambda c: _sensor(c, "sensor_14") >= SENSOR_HIGH,
    ),
    Rule(
        code="R007", name="LPT出口温度异常", level="警告", fault_part="低压涡轮(LPT)",
        steps=["对比 sensor_2 与 sensor_14", "检查热电偶"],
        advice="复核低压涡轮出口温度测量值",
        check=lambda c: _sensor(c, "sensor_2") >= SENSOR_HIGH,
    ),
    Rule(
        code="R008", name="冷却剂温度异常", level="警告", fault_part="冷却系统",
        steps=["查看 sensor_7 冷却剂温度", "检查冷却回路流量"],
        advice="检查冷却系统流量与温度传感器",
        check=lambda c: _sensor(c, "sensor_7") >= SENSOR_HIGH,
    ),
    Rule(
        code="R009", name="风扇转速异常", level="警告", fault_part="风扇/进气系统",
        steps=["核对 sensor_9 转速", "检查风扇叶片", "检查进气阻力"],
        advice="检查风扇转速传感器与进气系统状态",
        check=lambda c: _sensor(c, "sensor_9") >= SENSOR_HIGH,
    ),
    Rule(
        code="R010", name="核心机转速异常", level="警告", fault_part="核心机转子",
        steps=["查看 sensor_12 转速", "检查轴承状态"],
        advice="检查核心机转速与轴承润滑状态",
        check=lambda c: _sensor(c, "sensor_12") >= SENSOR_HIGH,
    ),
    Rule(
        code="R011", name="设备高负载运行", level="提示", fault_part="整机",
        steps=["核对负载率", "评估工况合理性", "确认生产节拍"],
        advice="高负载运行需加强冷却与润滑，避免长时间超载",
        check=lambda c: c.get("load_rate", 0) > 85,
    ),
    Rule(
        code="R012", name="能耗效率偏低", level="警告", fault_part="整机",
        steps=["核算能耗效率", "对比历史基线", "检查是否存在无效损耗"],
        advice="排查能耗异常环节，优化运行参数以提升能效",
        check=lambda c: c.get("energy_efficiency", 100) < 40,
    ),
    Rule(
        code="R013", name="数据挖掘检出异常", level="警告", fault_part="待定位",
        steps=["查看孤立森林异常分数", "定位异常传感器点位", "核对异常时间点"],
        advice="结合异常分数定位可疑传感器，安排针对性检查",
        check=lambda c: bool(c.get("is_anomaly")) and c.get("anomaly_score", 0) > 0.7,
    ),
    Rule(
        code="R014", name="多重传感器异常", level="严重", fault_part="多部件",
        steps=["统计高值传感器数量", "检查是否系统性退化", "区分单一故障与多重故障"],
        advice="疑似多重/系统性故障，建议停机全面排查",
        check=lambda c: _count_high_sensors(c, [
            "sensor_2", "sensor_7", "sensor_9", "sensor_11",
            "sensor_12", "sensor_13", "sensor_14"]) >= 3,
    ),
    Rule(
        code="R015", name="LPT出口压力异常", level="提示", fault_part="低压涡轮(LPT)",
        steps=["核对 sensor_3 压力", "检查排气系统"],
        advice="检查低压涡轮出口压力传感器",
        check=lambda c: _sensor(c, "sensor_3") >= SENSOR_HIGH,
    ),
    Rule(
        code="R016", name="HPC出口压力异常", level="警告", fault_part="高压压气机(HPC)",
        steps=["查看 sensor_4 压力", "评估压气机效率"],
        advice="检查高压压气机出口压力与压气机状态",
        check=lambda c: _sensor(c, "sensor_4") >= SENSOR_HIGH,
    ),
    Rule(
        code="R017", name="旁通比异常", level="提示", fault_part="旁通系统",
        steps=["核对 sensor_15 旁通比", "检查旁通阀"],
        advice="检查旁通比与旁通阀工作状态",
        check=lambda c: _sensor(c, "sensor_15") >= SENSOR_HIGH,
    ),
    Rule(
        code="R018", name="HPT冷却剂出口温度异常", level="警告", fault_part="高压涡轮(HPT)冷却",
        steps=["查看 sensor_17", "检查冷却剂流量"],
        advice="检查 HPT 冷却剂回路",
        check=lambda c: _sensor(c, "sensor_17") >= SENSOR_HIGH,
    ),
    Rule(
        code="R019", name="LPT冷却剂出口温度异常", level="警告", fault_part="低压涡轮(LPT)冷却",
        steps=["查看 sensor_20", "检查冷却剂流量"],
        advice="检查 LPT 冷却剂回路",
        check=lambda c: _sensor(c, "sensor_20") >= SENSOR_HIGH,
    ),
    Rule(
        code="R020", name="燃油流量异常", level="警告", fault_part="燃油系统",
        steps=["核对 sensor_21 燃油流量", "检查油路与喷嘴"],
        advice="检查燃油供给系统与喷嘴状态",
        check=lambda c: _sensor(c, "sensor_21") >= SENSOR_HIGH,
    ),
]


def diagnose(ctx: dict) -> List[dict]:
    """对设备状态执行规则匹配，返回命中的诊断结论列表（按严重级别排序）。

    Returns:
        [{"code", "name", "level", "fault_part", "steps", "advice"}, ...]
    """
    matched = [rule for rule in RULES if rule.check(ctx)]
    matched.sort(key=lambda r: {"严重": 0, "警告": 1, "提示": 2}.get(r.level, 3))
    return [
        {
            "code": r.code,
            "name": r.name,
            "level": r.level,
            "fault_part": r.fault_part,
            "steps": r.steps,
            "advice": r.advice,
        }
        for r in matched
    ]


def rule_count() -> int:
    """规则库规模。"""
    return len(RULES)
