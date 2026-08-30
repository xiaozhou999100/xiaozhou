# -*- coding: utf-8 -*-
"""数据挖掘模块：孤立森林异常检测。

设计思路（关键）：
    C-MAPSS 传感器随寿命单调退化，若在全部数据（含退化末期）上训练，退化会被视为“正常”。
    因此本模块**只使用健康早期样本（每台设备前 50% 周期）建立正常基线**，
    使退化期/异常样本因偏离基线而被识别为异常，符合工业“以健康基线发现偏离”的场景。

评估标签：测试集每台设备最后 25% 周期视为“退化异常期”，评估模型的检出能力。
"""

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, precision_score, recall_score

from .features import make_feature_matrix

MODEL_DIR = Path(__file__).resolve().parent.parent / "model_files"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

IF_MODEL_PATH = MODEL_DIR / "isolation_forest.pkl"

# 健康基线占比（每台设备前 N% 周期作为正常样本）
HEALTHY_RATIO = 0.5
# 评估退化期占比（每台设备最后 N% 周期作为异常）
DEGRADE_RATIO = 0.25


def _healthy_baseline(df: pd.DataFrame, ratio: float = HEALTHY_RATIO) -> pd.DataFrame:
    """取每台设备前 ratio 比例的周期作为健康基线。"""
    last = df.groupby("unit")["cycle"].transform("max")
    return df[df["cycle"] <= last * ratio].copy()


def _degrade_label(df: pd.DataFrame, ratio: float = DEGRADE_RATIO) -> np.ndarray:
    """构造退化期标签：每台设备最后 ratio 比例周期为 1（cycle > last*(1-ratio)）。"""
    last = df.groupby("unit")["cycle"].transform("max")
    return (df["cycle"] > last * (1 - ratio)).astype(int).values


def train_isolation_forest(train_df, test_df=None, contamination=0.1, random_state=42):
    """训练孤立森林异常检测模型（基于健康基线）。

    Args:
        train_df: 训练数据（含传感器特征）。
        test_df: 可选，用于评估（按退化期标签）。
        contamination: 数据集中异常比例预估。

    Returns:
        (model, metrics, feature_names, threshold)
    """
    healthy = _healthy_baseline(train_df)
    X_train, _, feature_names = make_feature_matrix(healthy)
    print(f"  健康基线样本: {len(healthy)} 条")

    model = IsolationForest(
        n_estimators=150,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_train)

    threshold = 0.0
    metrics = {}
    if test_df is not None:
        X_test, _, _ = make_feature_matrix(test_df)
        y_true = _degrade_label(test_df)
        y_pred = (model.decision_function(X_test) < threshold).astype(int)
        metrics = {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "test_samples": int(len(y_true)),
            "degrade_rate": float(y_true.mean()),
            "healthy_ratio": HEALTHY_RATIO,
        }

    return model, metrics, feature_names, threshold


def save_model(model, feature_names, metrics, threshold, path=IF_MODEL_PATH):
    """保存模型与元信息。"""
    payload = {
        "model": model,
        "feature_names": feature_names,
        "metrics": metrics,
        "threshold": threshold,
        "healthy_ratio": HEALTHY_RATIO,
    }
    with open(path, "wb") as f:
        pickle.dump(payload, f)
    return path


def load_model(path=IF_MODEL_PATH):
    """加载固化模型。"""
    with open(path, "rb") as f:
        return pickle.load(f)


def predict_single(model, feature_vector) -> tuple:
    """对单个样本预测：返回 (is_anomaly, anomaly_score)。

    anomaly_score 由 decision_function（越高越正常）sigmoid 映射为 0~1 异常度。
    """
    score = float(model.decision_function([feature_vector])[0])
    is_anomaly = bool(score < 0.0)
    anomaly_score = float(1.0 / (1.0 + np.exp(-(-score))))
    return is_anomaly, round(anomaly_score, 4)
