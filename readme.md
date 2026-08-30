# 数字孪生车间智能监控与运维平台

> 课程设计项目 · B/S 架构 · 单机可运行

基于公开工业设备时序数据，构建车间设备数字孪生监控与智能运维系统，实现
**设备台账 → 数字孪生可视化 → 实时数据监测 → 健康/能耗评估 → 异常预警 → 智能诊断 → 运维工单**
完整业务闭环。

## 一、技术栈

| 部分 | 选型 | 说明 |
| --- | --- | --- |
| 前端 | Vue3 + Element Plus + ECharts | 后台管理、曲线图表、孪生大屏 |
| 孪生可视化 | 2D 画布 / 轻量组件 | 本机可跑，不依赖 3D 引擎 |
| 后端 | FastAPI (Python 3.10+) | 与算法同语言 |
| 数据库 | SQLite | 免服务、便携 |
| 算法 | scikit-learn（随机森林 / 孤立森林）+ 统计计算 | CPU 即可 |
| 测试 | pytest | 接口与算法测试 |
| 版本管理 | Git + GitHub | 小步提交、全程可追溯 |

## 二、目录结构

```
xiaozhou/
├── 选题说明                    # 选题与目标说明
├── 方案设计                    # 系统设计方案
├── 学习笔记.md                 # 学习计划与进度记录
├── PROJECT_RULES.md            # 项目核心规则文件（总规则，开发必读）
├── readme.md                   # 本文件
├── backend/                    # 后端（阶段2/3交付）
│   ├── app/
│   │   ├── main.py             # FastAPI 入口（挂载路由/建表/CORS）
│   │   ├── config.py           # 配置（路径/分页/枚举）
│   │   ├── database.py         # SQLAlchemy 引擎/会话
│   │   ├── models/             # ORM 模型（equipment/sensor_data/health_evaluation/alert/work_order）
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── routers/            # 路由（设备/传感器/评估/预警/工单/算法）
│   │   ├── services/           # 业务逻辑（健康评估/异常检测/专家诊断）
│   │   ├── algorithms/         # 算法模块（特征工程/随机森林/孤立森林/专家系统/训练脚本）
│   │   ├── model_files/        # 固化模型（random_forest_rul.joblib / isolation_forest.pkl）
│   │   └── seed.py             # 数据导入脚本
│   ├── tests/                  # pytest 测试（48 个用例，含闭环集成测试）
│   └── requirements.txt
├── frontend/                   # 前端（阶段4交付，Vue3+Vite）
│   ├── package.json / vite.config.js
│   └── src/
│       ├── main.js / App.vue / router / api
│       ├── layout/MainLayout.vue   # 主布局（深蓝侧栏导航）
│       └── views/                  # 六大页面（孪生/台账/监测/评估/预警/工单）
├── data/                       # 数据目录（阶段1交付）
│   ├── README.md               # 数据来源与说明
│   ├── preprocess.py           # 数据预处理程序
│   ├── equipment.db            # SQLite 数据库（由 seed.py 生成）
│   ├── raw/CMAPSS/             # 官方原始数据（FD001 核心子集）
│   └── processed/              # 预处理后数据文件与参数
└── prompt/                     # AI 提示词追溯记录（每阶段归档）
    ├── stage1_data_preparation_2026-08-30.json
    ├── stage2_project_init_backend_2026-08-30.json
    ├── stage3_algorithm_2026-08-30.json
    ├── stage4_frontend_2026-08-30.json
    └── stage5_closed_loop_testing_2026-08-30.json
```

## 三、数据说明（数据准备阶段已完成）

### 3.1 数据来源

本项目选用 **NASA C-MAPSS 涡扇发动机退化仿真数据集 FD001 子集** 作为核心实验数据，
属公开工业设备时序数据（run-to-failure 全寿命退化数据），是数字孪生与智能运维领域通用仿真数据。

- **官方有效链接**：
  - 数据集主页：https://data.nasa.gov/Aerospace/CMAPSS-Jet-Engine-Simulated-Data/ff5v-kuh6
  - 数据包直链：https://data.nasa.gov/docs/legacy/CMAPSSData.zip
  - NASA PCoE 数据仓库：https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/
- **引用**：Saxena, A., Goebel, K., Simon, D., Eklund, N. (2008). Damage Propagation Modeling for
  Aircraft Engine Run-to-Failure Simulation. PHM08.
- 数据量小，FD001 原始数据直接提交至仓库 `/data/raw/CMAPSS/`；详细说明见 `data/README.md`。

### 3.2 数据预处理

预处理程序 `data/preprocess.py` 完成：列名补充、零方差列剔除（保留 15 传感器 + 2 工况）、
RUL/健康度/健康等级/异常标签构造、MinMax 归一化、SQLite 导出。
预处理结果存放于 `/data/processed/`（训练 20,631 行 / 测试 13,096 行 / 设备台账 100 台）。
运行方式：`cd data && python preprocess.py`（依赖 pandas/numpy/scikit-learn）。

### 3.3 AI 工具提示词追溯

AI 交互记录按阶段归档至 `/prompt/` 目录（JSON 格式），每阶段同步更新。
本阶段记录：`prompt/stage1_data_preparation_2026-08-30.json`、`prompt/stage2_project_init_backend_2026-08-30.json`。

## 四、后端运行说明（阶段2/3交付）

```bash
cd backend
pip install -r requirements.txt        # 安装依赖
python -m app.seed                     # 导入预处理数据生成 equipment.db（可重复执行）
python -m app.algorithms.train         # 训练并固化模型（随机森林/孤立森林，可重复执行）
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000   # 启动服务
python -m pytest tests -v              # 运行自动化测试（48 个用例）
```

服务启动后访问 `http://127.0.0.1:8000/docs` 查看 Swagger 接口文档。
接口统一返回 `{"code": 0, "message": "success", "data": ...}`，前缀 `/api/v1`，覆盖：
设备台账 CRUD、传感器时序查询、健康评估（随机森林）、异常检测（孤立森林）、专家诊断、预警、运维工单（预警→诊断→工单闭环）。

### 4.1 算法模块说明（阶段3）

| 算法 | 方法 | 指标 |
| --- | --- | --- |
| 健康度/RUL 预测 | 随机森林回归（30 周期窗口统计特征 62 维） | 测试集 MAE 13.55 cycles，R² 0.53 |
| 异常检测 | 孤立森林（健康早期 50% 样本建基线） | 精确率 0.43，召回率 0.26 |
| 故障诊断 | 专家系统 IF-THEN 规则库（20 条，R001~R020） | 输出故障部位/排查步骤/维修建议 |

算法固化于 `backend/app/model_files/`，运行时不重新训练；`python -m app.algorithms.train` 可一键重训。

### 4.2 前端运行说明（阶段4）

```bash
cd frontend
npm install                          # 安装依赖
npm run dev                          # 启动开发服务器（默认 http://127.0.0.1:5173）
npm run build                        # 生产构建（输出 dist/）
```

开发服务器已配置 `/api` 代理到后端 `http://127.0.0.1:8000`，**需先启动后端**再访问前端。

六大页面：
| 页面 | 路由 | 功能 |
| --- | --- | --- |
| 数字孪生可视化 | `/twin` | 车间布局、设备孪生状态、统计概览、一键诊断 |
| 车间设备台账 | `/equipment` | 设备 CRUD、搜索分页 |
| 实时数据监测 | `/monitoring` | 多传感器折线、异常红点、最新周期概览 |
| 健康与能耗评估 | `/evaluation` | 随机森林评估触发、健康度仪表盘、历史记录 |
| 孪生预警中心 | `/alerts` | 预警筛选、生成工单、标记处理、一键闭环演练 |
| 运维工单管理 | `/work-orders` | 工单状态流转（待处理→维修中→已完成）、新建/详情 |

### 4.3 业务闭环与整体测试（阶段5）

**业务闭环**（核心价值，已端到端打通）：
```
设备监测 → 孤立森林异常检测 → 风险预警 → 专家系统诊断 → 运维工单生成 → 工单状态流转 → 闭环
```

**整体测试**：
- 后端自动化测试 **48 个用例全部通过**（43 个基础/算法 + 5 个闭环集成测试）
- 闭环集成测试覆盖：异常检测→预警、诊断→工单、工单状态流转、预警一键生成工单并标记处理、全链路闭环
- 前端提供「一键闭环演练」按钮（预警中心页），输入设备 ID 即可一键演示完整闭环
- 已在真实运行的前后端环境中用浏览器完整演示闭环（DEV001 末端寿命设备：检出异常→预警→诊断命中 R001 严重→自动生成工单→状态流转至已完成）

## 五、开发进度

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| 阶段 1 | 数据准备：数据来源 + 预处理 + prompt 追溯 | ✅ 完成（2026-08-30） |
| 阶段 2 | 项目初始化 + 数据库表结构 + 后端基础接口 + 自动化测试 | ✅ 完成（2026-08-30） |
| 阶段 3 | 算法模块：随机森林/孤立森林/专家系统规则库 + 服务集成 | ✅ 完成（2026-08-30） |
| 阶段 4 | 前端孪生大屏与六大页面（Vue3+Element Plus+ECharts） | ✅ 完成（2026-08-30） |
| 阶段 5 | 预警-诊断-工单闭环联调与整体测试 | ✅ 完成（2026-08-30） |

## 六、运行环境

- Python 3.10+（本机 3.13）
- Node.js LTS（前端，阶段 4 引入）
- 全部本机运行，无云端、无硬件依赖

## 七、参考文献

[1] 数字孪生与智能制造 [M]. 电子工业出版社.
[2] 工业互联网平台技术 [M]. 机械工业出版社.
[3] 数字孪生体技术白皮书 [EB/OL].
[4] Saxena A, Goebel K, Simon D, Eklund N. Damage Propagation Modeling for Aircraft Engine
Run-to-Failure Simulation [C]. PHM08, 2008.
