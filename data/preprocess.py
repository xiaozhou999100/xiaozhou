# -*- coding: utf-8 -*-
"""
C-MAPSS FD001 数据预处理程序
============================
课程设计：数字孪生车间智能监控与运维平台

功能说明：
1. 加载 C-MAPSS FD001 原始数据（训练集/测试集/真实RUL），补充列名；
2. 删除无变化（零方差）的传感器列，保留有效监测维度；
3. 构造健康标签（RUL / 健康度评分 / 健康等级）与异常标签；
4. 使用 MinMax 归一化（仅基于训练集拟合，保存归一化参数）；
5. 输出预处理后的数据文件、参数文件、设备台账概要；
6. 生成 SQLite 数据库，供数字孪生平台实时读取。

输入：data/raw/CMAPSS/ 下的 train_FD001.txt、test_FD001.txt、RUL_FD001.txt
输出：data/processed/ 下的预处理数据文件与参数文件、data/equipment.db
"""

import json
import os
import sqlite3
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# ----------------------------------------------------------------------------
# 路径配置
# ----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # data/
RAW_DIR = os.path.join(BASE_DIR, "raw", "CMAPSS")
PROC_DIR = os.path.join(BASE_DIR, "processed")
os.makedirs(PROC_DIR, exist_ok=True)

TRAIN_RAW = os.path.join(RAW_DIR, "train_FD001.txt")
TEST_RAW = os.path.join(RAW_DIR, "test_FD001.txt")
RUL_RAW = os.path.join(RAW_DIR, "RUL_FD001.txt")
DB_PATH = os.path.join(BASE_DIR, "equipment.db")

# ----------------------------------------------------------------------------
# 列名定义（C-MAPSS 官方：26 列 = 1 单元 + 1 周期 + 3 工况 + 21 传感器）
# ----------------------------------------------------------------------------
COLUMNS = ["unit", "cycle"] + \
          [f"op_setting_{i}" for i in range(1, 4)] + \
          [f"sensor_{i}" for i in range(1, 22)]

RANDOM_SEED = 42


def load_fd001():
    """加载 FD001 原始数据并添加列名。"""
    train = pd.read_csv(TRAIN_RAW, sep=r"\s+", header=None, names=COLUMNS)
    test = pd.read_csv(TEST_RAW, sep=r"\s+", header=None, names=COLUMNS)
    rul_true = pd.read_csv(RUL_RAW, sep=r"\s+", header=None, names=["rul_true"])
    return train, test, rul_true


def drop_constant_columns(df, exclude):
    """删除在训练集中无变化（方差为 0）的列，返回保留列列表。"""
    keep = [c for c in df.columns if c in exclude]
    for col in df.columns:
        if col in exclude:
            continue
        if df[col].nunique() <= 1 or np.isclose(df[col].std(), 0):
            print(f"  [删除] 零方差列: {col}")
            continue
        keep.append(col)
    return keep


def build_train_rul(train):
    """训练集 RUL = 该单元最大周期 - 当前周期（run-to-failure）。"""
    max_cycle = train.groupby("unit")["cycle"].transform("max")
    train["rul"] = max_cycle - train["cycle"]
    return train


def build_test_rul(test, rul_true):
    """测试集 RUL = 单元真实剩余寿命 + (单元最后周期 - 当前周期)。"""
    last_cycle = test.groupby("unit")["cycle"].transform("max")
    rul_true.index = np.arange(1, len(rul_true) + 1)  # unit 编号 1..N
    test = test.merge(rul_true, left_on="unit", right_index=True, how="left")
    test["rul"] = test["rul_true"] + (last_cycle - test["cycle"])
    return test


def add_health_labels(df):
    """
    构造健康标签：
      - health_score：基于 RUL 的 0-100 健康度评分（RUL 越大越健康）
      - health_grade：健康 / 注意 / 预警 / 严重 四级
      - anomaly_label：异常标签（0 正常，1 异常），用于孤立森林/规则训练
    """
    max_rul = df["rul"].max()
    df["health_score"] = np.clip(100 * df["rul"] / max_rul, 0, 100).round(2)

    def grade(score):
        if score >= 75:
            return "健康"
        if score >= 50:
            return "注意"
        if score >= 25:
            return "预警"
        return "严重"

    df["health_grade"] = df["health_score"].apply(grade)
    # 健康度 < 25（即 RUL 低于最大寿命的 25%）视为异常点
    df["anomaly_label"] = (df["health_score"] < 25).astype(int)
    return df


def normalize_and_export(df, scaler, cols):
    """对指定列做 MinMax 归一化，返回新增 *_norm 列。"""
    normed = scaler.transform(df[cols])
    for i, col in enumerate(cols):
        df[f"{col}_norm"] = normed[:, i].round(6)
    return df


def build_device_profile(train):
    """构建设备台账概要：每台设备的起止周期、工况均值、健康状态。"""
    profile = train.groupby("unit").agg(
        device_id=("unit", "first"),
        start_cycle=("cycle", "min"),
        end_cycle=("cycle", "max"),
        total_cycles=("cycle", "count"),
        avg_health_score=("health_score", "mean"),
        final_rul=("rul", "last"),
    ).reset_index(drop=True)

    def init_state(rul):
        if rul > 100:
            return "运行"
        if rul > 50:
            return "关注"
        return "报警"

    profile["init_state"] = profile["final_rul"].apply(init_state)
    profile["avg_health_score"] = profile["avg_health_score"].round(2)
    return profile


def export_sqlite(train, test, profile):
    """导出预处理数据到 SQLite，供数字孪生平台实时读取。"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    train.to_sql("device_sensor_data", conn, index=False, if_exists="replace")
    test.to_sql("device_sensor_test", conn, index=False, if_exists="replace")
    profile.to_sql("device_profile", conn, index=False, if_exists="replace")
    conn.commit()
    conn.close()
    print(f"  [OK] SQLite 已生成: {DB_PATH}")


def main():
    print("=" * 60)
    print("C-MAPSS FD001 数据预处理")
    print("=" * 60)

    # 1. 加载数据
    print("\n[1/6] 加载原始数据 ...")
    train, test, rul_true = load_fd001()
    print(f"  训练集: {train.shape[0]} 行 x {train.shape[1]} 列, {train['unit'].nunique()} 台设备")
    print(f"  测试集: {test.shape[0]} 行 x {test.shape[1]} 列, {test['unit'].nunique()} 台设备")

    # 2. 删除无变化列
    print("\n[2/6] 检测并删除零方差列（基于训练集）...")
    exclude_cols = ["unit", "cycle"]
    keep_cols = drop_constant_columns(train, exclude_cols)
    sensor_cols = [c for c in keep_cols if c.startswith("sensor_")]
    op_cols = [c for c in keep_cols if c.startswith("op_setting_")]
    print(f"  保留列: {keep_cols}")
    print(f"  保留传感器: {len(sensor_cols)} 个 | 工况列: {len(op_cols)} 个")
    removed_cols = [c for c in train.columns if c not in keep_cols and c not in exclude_cols]

    # 3. 构造 RUL 与健康/异常标签
    print("\n[3/6] 构造 RUL 与健康/异常标签 ...")
    train = build_train_rul(train)
    test = build_test_rul(test, rul_true)
    train = add_health_labels(train)
    test = add_health_labels(test)
    print(f"  训练集 RUL 范围: {train['rul'].min()} ~ {train['rul'].max()}")
    print(f"  训练集异常点占比: {train['anomaly_label'].mean():.2%}")

    # 4. 归一化（仅用训练集拟合）
    print("\n[4/6] MinMax 归一化（训练集拟合）...")
    norm_cols = sensor_cols + op_cols
    scaler = MinMaxScaler()
    scaler.fit(train[norm_cols])
    train = normalize_and_export(train, scaler, norm_cols)
    test = normalize_and_export(test, scaler, norm_cols)

    # 5. 保存预处理数据与参数
    print("\n[5/6] 保存预处理结果 ...")
    out_columns = ["unit", "cycle", "rul", "health_score", "health_grade",
                   "anomaly_label"] + [c for c in keep_cols if c not in ("unit", "cycle")] + \
                  [f"{c}_norm" for c in norm_cols]
    train_out = train[out_columns]
    test_out = test[out_columns]

    train_csv = os.path.join(PROC_DIR, "train_FD001_processed.csv")
    test_csv = os.path.join(PROC_DIR, "test_FD001_processed.csv")
    train_out.to_csv(train_csv, index=False)
    test_out.to_csv(test_csv, index=False)
    print(f"  [OK] {train_csv}  ({train_out.shape[0]} 行)")
    print(f"  [OK] {test_csv}  ({test_out.shape[0]} 行)")

    scaler_params = {
        "method": "MinMaxScaler",
        "fit_on": "train_FD001",
        "feature_range": [0, 1],
        "columns": norm_cols,
        "min_values": {c: round(float(v), 6) for c, v in zip(norm_cols, scaler.data_min_)},
        "max_values": {c: round(float(v), 6) for c, v in zip(norm_cols, scaler.data_max_)},
    }
    sensor_meta = {
        "dataset": "C-MAPSS FD001",
        "total_sensors": 21,
        "kept_sensors": sensor_cols,
        "removed_constant_sensors": [c for c in removed_cols if c.startswith("sensor_")],
        "kept_op_settings": op_cols,
        "label_columns": ["rul", "health_score", "health_grade", "anomaly_label"],
    }
    with open(os.path.join(PROC_DIR, "scaler_params.json"), "w", encoding="utf-8") as f:
        json.dump(scaler_params, f, ensure_ascii=False, indent=2)
    with open(os.path.join(PROC_DIR, "sensor_meta.json"), "w", encoding="utf-8") as f:
        json.dump(sensor_meta, f, ensure_ascii=False, indent=2)
    print("  [OK] scaler_params.json / sensor_meta.json")

    # 设备台账
    profile = build_device_profile(train)
    profile_csv = os.path.join(PROC_DIR, "device_profile.csv")
    profile.to_csv(profile_csv, index=False)
    print(f"  [OK] {profile_csv}  ({profile.shape[0]} 台设备)")

    # 6. 导出 SQLite
    print("\n[6/6] 导出 SQLite 数据库 ...")
    export_sqlite(train_out, test_out, profile)

    print("\n" + "=" * 60)
    print("预处理完成 ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()
