# -*- coding: utf-8 -*-
"""深度学习模块（LSTM）单元测试：序列构建 / 训练 / 固化 / 单点预测。

使用小型模拟退化数据集（不依赖真实 CMAPSS 文件），保证测试快速且独立。
"""

import numpy as np
import pandas as pd

from app.algorithms.lstm import (
    RUL_CLIP,
    SEQ_LEN,
    FEATURE_COLS,
    build_sequences,
    train_lstm,
    save_model,
    load_model,
    predict_single,
)


def _fake_df(n_units=4, cycles=60):
    """构造模拟退化设备数据：传感器单调退化 + RUL 线性下降。"""
    rows = []
    for u in range(1, n_units + 1):
        for t in range(1, cycles + 1):
            row = {"unit": u, "cycle": t, "rul": float(cycles - t)}
            for c in FEATURE_COLS:
                row[c] = 0.2 + 0.01 * t + (u % 3) * 0.01
            rows.append(row)
    return pd.DataFrame(rows)


def test_build_sequences_shape():
    df = _fake_df()
    X, y = build_sequences(df)
    assert X.ndim == 3
    assert X.shape[1] == SEQ_LEN
    assert X.shape[2] == len(FEATURE_COLS)
    assert X.shape[0] == len(df)
    assert np.all(y <= RUL_CLIP + 1e-6)


def test_train_lstm_quick():
    df = _fake_df(n_units=4, cycles=40)
    result = train_lstm(df, epochs=2, val_units=1)
    assert "model" in result
    assert result["metrics"]["train_samples"] > 0
    assert result["seq_len"] == SEQ_LEN


def test_save_load_roundtrip(tmp_path):
    df = _fake_df()
    result = train_lstm(df, epochs=2, val_units=1)
    path = save_model(result["model"], result["metrics"],
                      result["feature_names"], tmp_path / "lstm.pt")
    loaded = load_model(path)
    assert loaded["seq_len"] == SEQ_LEN
    assert loaded["n_features"] == len(FEATURE_COLS)
    assert "model" in loaded


def test_predict_single():
    df = _fake_df()
    result = train_lstm(df, epochs=2, val_units=1)
    recent = df[df["unit"] == 1].sort_values("cycle").tail(SEQ_LEN)
    rul = predict_single(result["model"], recent)
    assert 0.0 <= rul <= RUL_CLIP + 1e-6
