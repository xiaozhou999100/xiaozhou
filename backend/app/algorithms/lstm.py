# -*- coding: utf-8 -*-
"""深度学习模块：LSTM 时序模型 — 设备剩余寿命（RUL）预测。

学习笔记规划的四大核心技术之一：用 LSTM 直接建模传感器时间序列，
与随机森林（机器学习）形成"深度学习 vs 机器学习"的对比。

设计：
    - 输入：每台设备最近 30 个周期的归一化传感器 + 工况序列（30 x 17）；
    - 架构：单层 LSTM(hidden=64) -> 全连接(32) -> 标量 RUL；
    - 标签：与随机森林一致的 RUL（截断上限 125）；
    - 训练：按设备划分验证集选最优 epoch，测试集为官方 FD001 测试集。

FD001 测试集对比：
    随机森林（机器学习）:  MAE 10.55 cycles, R² 0.72
    LSTM（深度学习）:      MAE 9.02 cycles, R² 0.77  （更优，见模型元信息 metrics）
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import mean_absolute_error, r2_score

from ..models.sensor_data import SENSOR_COLS, OP_COLS

MODEL_DIR = Path(__file__).resolve().parent.parent / "model_files"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

LSTM_MODEL_PATH = MODEL_DIR / "lstm_rul.pt"

# 时序窗口长度（与特征工程窗口一致）
SEQ_LEN = 30
# 每时间步特征：15 个归一化传感器 + 2 个归一化工况
FEATURE_COLS = [f"{c}_norm" for c in SENSOR_COLS] + [f"{c}_norm" for c in OP_COLS]
N_FEATURES = len(FEATURE_COLS)
# RUL 截断上限（与随机森林保持一致）
RUL_CLIP = 125.0

torch.manual_seed(42)
np.random.seed(42)


class RulLSTM(nn.Module):
    """LSTM 时序 RUL 预测网络。"""

    def __init__(self, n_features: int = N_FEATURES, hidden: int = 64,
                 num_layers: int = 1, dropout: float = 0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            n_features, hidden, num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


def build_sequences(df: pd.DataFrame, seq_len: int = SEQ_LEN) -> tuple:
    """将时序数据转换为 (N, seq_len, n_features) 序列与 RUL 标签。

    每行周期 t 的输入 = [t-seq_len+1 .. t] 的归一化特征（不足窗口时用首行填充），
    标签 = 该周期 RUL（截断至 RUL_CLIP）。与随机森林"最近窗口统计"口径一致。
    """
    X, y = [], []
    for unit, grp in df.groupby("unit"):
        grp = grp.sort_values("cycle")
        feats = grp[FEATURE_COLS].values.astype(np.float32)
        rul = np.clip(grp["rul"].values, 0.0, RUL_CLIP).astype(np.float32)
        n = len(grp)
        for t in range(n):
            start = max(0, t - seq_len + 1)
            seq = feats[start:t + 1]
            if len(seq) < seq_len:
                pad = np.repeat(seq[0:1], seq_len - len(seq), axis=0)
                seq = np.concatenate([pad, seq], axis=0)
            X.append(seq)
            y.append(rul[t])
    return np.stack(X), np.array(y, dtype=np.float32)


def train_lstm(train_df: pd.DataFrame, test_df=None,
               epochs: int = 45, batch_size: int = 256,
               hidden: int = 64, lr: float = 1e-3,
               val_units: int = 20) -> dict:
    """训练 LSTM 模型。

    Args:
        train_df: 训练数据（含 FEATURE_COLS 与 rul）。
        test_df: 可选，官方测试集（含真值 rul），训练后评估。
        val_units: 末尾若干台设备作为验证集（选最优 epoch，防过拟合）。

    Returns:
        dict: model / metrics / feature_names / seq_len / state_dict。
    """
    X, y = build_sequences(train_df)
    units = sorted(train_df["unit"].unique())
    val_ids = set(units[-val_units:]) if len(units) > val_units else set()
    tr_units = [u for u in units if u not in val_ids]
    te_units = [u for u in units if u in val_ids]

    # 按设备顺序构建 X/y，便于按 unit 切分（同一设备不跨 train/val）
    X_all, y_all, unit_map = [], [], []
    for u, grp in train_df.groupby("unit"):
        grp = grp.sort_values("cycle")
        feats = grp[FEATURE_COLS].values.astype(np.float32)
        rul = np.clip(grp["rul"].values, 0.0, RUL_CLIP).astype(np.float32)
        n = len(grp)
        for t in range(n):
            start = max(0, t - SEQ_LEN + 1)
            seq = feats[start:t + 1]
            if len(seq) < SEQ_LEN:
                pad = np.repeat(seq[0:1], SEQ_LEN - len(seq), axis=0)
                seq = np.concatenate([pad, seq], axis=0)
            X_all.append(seq)
            y_all.append(rul[t])
            unit_map.append(u)
    X_all = np.stack(X_all)
    y_all = np.array(y_all, dtype=np.float32)
    unit_map = np.array(unit_map)

    tr_mask = np.isin(unit_map, tr_units)
    X_tr, y_tr = torch.tensor(X_all[tr_mask]), torch.tensor(y_all[tr_mask])
    X_va, y_va = torch.tensor(X_all[~tr_mask]), torch.tensor(y_all[~tr_mask])
    n_tr = int(len(X_tr))

    model = RulLSTM(n_features=N_FEATURES, hidden=hidden)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    best_mae, best_state = float("inf"), None
    for ep in range(1, epochs + 1):
        model.train()
        perm = torch.randperm(n_tr)
        total_loss = 0.0
        for i in range(0, n_tr, batch_size):
            idx = perm[i:i + batch_size]
            xb, yb = X_tr[idx], y_tr[idx].unsqueeze(1)
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(idx)
        # 验证集评估
        model.eval()
        with torch.no_grad():
            pv = model(X_va).squeeze(1).numpy()
        mae_v = float(mean_absolute_error(y_va.numpy(), pv))
        if mae_v < best_mae:
            best_mae, best_state = mae_v, {k: v.clone() for k, v in model.state_dict().items()}
        print(f"  epoch {ep:2d}/{epochs}  loss={total_loss/n_tr:.4f}  val_MAE={mae_v:.2f}")

    model.load_state_dict(best_state)

    metrics = {
        "val_units": len(te_units),
        "best_val_mae": round(best_mae, 3),
        "seq_len": SEQ_LEN,
        "n_features": N_FEATURES,
        "hidden": hidden,
        "train_samples": int(n_tr),
    }
    if test_df is not None:
        X_te, y_te = build_sequences(test_df)
        model.eval()
        with torch.no_grad():
            p = model(torch.tensor(X_te)).squeeze(1).numpy()
        metrics.update({
            "test_mae": float(mean_absolute_error(y_te, p)),
            "test_r2": float(r2_score(y_te, p)),
            "test_samples": int(len(y_te)),
        })

    return {
        "model": model,
        "metrics": metrics,
        "feature_names": FEATURE_COLS,
        "seq_len": SEQ_LEN,
        "state_dict": best_state,
    }


def save_model(model: nn.Module, metrics: dict, feature_names: list,
               path=LSTM_MODEL_PATH) -> Path:
    """保存模型权重与元信息。"""
    payload = {
        "state_dict": model.state_dict(),
        "metrics": metrics,
        "feature_names": feature_names,
        "seq_len": SEQ_LEN,
        "n_features": N_FEATURES,
    }
    torch.save(payload, path)
    # 同步写一份指标 JSON 便于阅读（仅默认路径）
    if Path(path).resolve() == Path(LSTM_MODEL_PATH).resolve():
        (MODEL_DIR / "lstm_metrics.json").write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_model(path=LSTM_MODEL_PATH) -> dict:
    """加载固化模型。"""
    payload = torch.load(path, map_location="cpu", weights_only=False)
    model = RulLSTM(n_features=payload["n_features"])
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return {"model": model, **payload}


def predict_single(model: nn.Module, recent_df: pd.DataFrame) -> float:
    """对单台设备的最近时序预测 RUL（供运行时可选调用）。

    Args:
        recent_df: 该设备按 cycle 升序的最近特征行（含 FEATURE_COLS）。
    Returns:
        预测 RUL（cycles）。
    """
    seq = recent_df[FEATURE_COLS].values.astype(np.float32)
    if len(seq) < SEQ_LEN:
        pad = np.repeat(seq[0:1], SEQ_LEN - len(seq), axis=0)
        seq = np.concatenate([pad, seq], axis=0)
    else:
        seq = seq[-SEQ_LEN:]
    with torch.no_grad():
        p = model(torch.tensor(seq[None, ...])).item()
    return float(np.clip(p, 0.0, RUL_CLIP))
