# -*- coding: utf-8 -*-
"""模型训练脚本：一键训练并固化随机森林与孤立森林模型。

用法（backend/ 目录下）：
    python -m app.algorithms.train

数据来源：data/processed/train_FD001_processed.csv（训练）、test_FD001_processed.csv（测试评估）。
产物：backend/app/model_files/random_forest_rul.pkl、isolation_forest.pkl
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pandas as pd

from app.config import PROCESSED_DIR
from app.algorithms.expert_system import rule_count
from app.algorithms.random_forest import train_random_forest, save_model as save_rf
from app.algorithms.isolation_forest import train_isolation_forest, save_model as save_if


def main() -> None:
    print("=" * 60)
    print("算法模型训练")
    print("=" * 60)

    train = pd.read_csv(PROCESSED_DIR / "train_FD001_processed.csv")
    test = pd.read_csv(PROCESSED_DIR / "test_FD001_processed.csv")
    print(f"[数据] 训练集 {len(train)} 行, 测试集 {len(test)} 行")

    print("\n[1/3] 随机森林 RUL/健康度预测 ...")
    rf_model, rf_metrics, rf_feats = train_random_forest(train, test)
    print(f"  测试集 MAE = {rf_metrics['mae']:.2f} (cycles), R² = {rf_metrics['r2']:.4f}, 样本 {rf_metrics['test_samples']}")
    rf_path = save_rf(rf_model, rf_feats, rf_metrics)
    print(f"  [OK] 模型已保存: {rf_path.name}")

    print("\n[2/3] 孤立森林异常检测 ...")
    if_model, if_metrics, if_feats, threshold = train_isolation_forest(train, test)
    print(f"  测试集准确率 = {if_metrics['accuracy']:.4f}, 精确率 = {if_metrics['precision']:.4f}, "
          f"召回率 = {if_metrics['recall']:.4f}")
    if_path = save_if(if_model, if_feats, if_metrics, threshold)
    print(f"  [OK] 模型已保存: {if_path.name}")

    print(f"\n[3/3] 专家系统规则库 ...")
    print(f"  规则条数: {rule_count()} 条")

    print("\n" + "=" * 60)
    print("模型训练完成 ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()
