# -*- coding: utf-8 -*-
"""机器学习模块：随机森林回归 — 设备健康度 / RUL 预测。

基于传感器窗口统计特征（均值/标准差/最小/最大/斜率，共 77 维）训练随机森林回归模型，
预测设备剩余使用寿命（RUL），并映射为 0~100 健康度评分。模型训练后固化（pickle），
运行时仅调用预测。

FD001 测试集指标（含斜率特征）：MAE 10.5 cycles，R² 0.72。
"""

import joblib
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

from .features import make_feature_matrix

MODEL_DIR = Path(__file__).resolve().parent.parent / "model_files"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

RF_MODEL_PATH = MODEL_DIR / "random_forest_rul.joblib"

# RUL 截断上限（C-MAPSS 惯例：RUL 超过 125 视为同一起点，聚焦退化阶段）
RUL_CLIP = 125.0


def train_random_forest(train_df, test_df=None, n_estimators=150, random_state=42):
    """训练随机森林 RUL 预测模型。

    Args:
        train_df: 含 unit/cycle/传感器/rul 的训练数据。
        test_df: 可选，含 rul 的测试数据，用于评估。
        n_estimators: 随机森林树数量。

    Returns:
        (model, metrics, feature_names)
    """
    X_train, y_train, feature_names = make_feature_matrix(train_df)
    y_train = np.clip(y_train, 0, RUL_CLIP)

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=-1,
        min_samples_leaf=2,     # 控制树规模，避免模型文件过大
        min_samples_split=5,
    )
    model.fit(X_train, y_train)

    metrics = {}
    if test_df is not None:
        X_test, y_test, _ = make_feature_matrix(test_df)
        y_test_clip = np.clip(y_test, 0, RUL_CLIP)
        y_pred = model.predict(X_test)
        metrics = {
            "mae": float(mean_absolute_error(y_test_clip, y_pred)),
            "r2": float(r2_score(y_test_clip, y_pred)),
            "test_samples": int(len(y_test)),
        }

    return model, metrics, feature_names


def save_model(model, feature_names, metrics, path=RF_MODEL_PATH):
    """保存模型与元信息（joblib 压缩，控制体积）。"""
    payload = {
        "model": model,
        "feature_names": feature_names,
        "metrics": metrics,
        "rul_clip": RUL_CLIP,
    }
    joblib.dump(payload, path, compress=3)
    return path


def load_model(path=RF_MODEL_PATH):
    """加载固化模型。"""
    return joblib.load(path)


def rul_to_health_score(rul: float) -> float:
    """将 RUL 映射为 0~100 健康度评分（RUL 越大越健康）。"""
    return float(np.clip(100.0 * rul / RUL_CLIP, 0, 100))
