# -*- coding: utf-8 -*-
"""特征工程模块：将设备传感器时序转换为机器学习可用的统计特征。

思路：对每台设备的传感器时序，以滑动窗口（默认 30 个周期）计算统计特征
（均值 / 标准差 / 最小值 / 最大值），刻画设备退化趋势；叠加当前工况（op_setting）。
随机森林 / 孤立森林均基于该特征输入。
"""

import numpy as np
import pandas as pd

from ..models.sensor_data import SENSOR_COLS, OP_COLS

# 滑动窗口大小（C-MAPSS 常用 30 周期窗口）
DEFAULT_WINDOW = 30

# 统计特征算子
STAT_OPS = ["mean", "std", "min", "max"]


def build_window_features(df: pd.DataFrame, window: int = DEFAULT_WINDOW) -> pd.DataFrame:
    """为时序数据构建窗口统计特征，返回新增特征列后的 DataFrame。

    Args:
        df: 需包含 unit、cycle、SENSOR_COLS、OP_COLS 列。
        window: 滑动窗口大小（至少覆盖当前周期）。

    Returns:
        原 DataFrame 副本 + 新增特征列 *_mean / *_std / *_min / *_max。
    """
    out = df.copy()
    win = max(window, 1)

    for col in SENSOR_COLS:
        grouped = out.groupby("unit")[col]
        out[f"{col}_mean"] = grouped.transform(lambda s: s.rolling(win, min_periods=1).mean())
        out[f"{col}_std"] = grouped.transform(lambda s: s.rolling(win, min_periods=1).std().fillna(0.0))
        out[f"{col}_min"] = grouped.transform(lambda s: s.rolling(win, min_periods=1).min())
        out[f"{col}_max"] = grouped.transform(lambda s: s.rolling(win, min_periods=1).max())

    return out


def feature_columns(sensors=SENSOR_COLS, ops=OP_COLS, window=None):
    """返回模型特征列名列表。"""
    cols = [f"{s}_{op}" for s in sensors for op in STAT_OPS]
    cols += list(ops)
    return cols


def make_feature_matrix(df: pd.DataFrame, window: int = DEFAULT_WINDOW) -> tuple:
    """构建特征矩阵 X 与标签 y（若存在 rul 列）。

    Returns:
        (X: ndarray, y: ndarray|None, feature_names: list[str])
    """
    feats = build_window_features(df, window)
    cols = feature_columns()
    X = feats[cols].values.astype(np.float64)
    y = feats["rul"].values.astype(np.float64) if "rul" in feats.columns else None
    return X, y, cols


def device_feature_vector(rows, window: int = DEFAULT_WINDOW):
    """运行时：由设备历史时序行构造特征向量（与训练特征对齐）。

    Args:
        rows: 该设备的 SensorData ORM 行（按 cycle 升序），取自目标周期为止。
        window: 滑动窗口大小。

    Returns:
        np.ndarray 特征向量（长度与 feature_columns() 一致），无数据时返回 None。
    """
    if not rows:
        return None
    win = max(window, 1)
    recent = rows[-win:]

    def _vals(attr):
        return np.array([getattr(r, attr) for r in recent], dtype=np.float64)

    vec = []
    for sensor in SENSOR_COLS:
        v = _vals(sensor)
        vec += [float(v.mean()),
                float(v.std()) if len(v) > 1 else 0.0,
                float(v.min()),
                float(v.max())]

    last = rows[-1]
    vec += [float(last.op_setting_1), float(last.op_setting_2)]
    return np.array(vec, dtype=np.float64)
