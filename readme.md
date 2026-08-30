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
├── backend/                    # 后端（阶段2交付）
│   ├── app/
│   │   ├── main.py             # FastAPI 入口（挂载路由/建表/CORS）
│   │   ├── config.py           # 配置（路径/分页/枚举）
│   │   ├── database.py         # SQLAlchemy 引擎/会话
│   │   ├── models/             # ORM 模型（equipment/sensor_data/health_evaluation/alert/work_order）
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── routers/            # 路由（设备台账/传感器/评估/预警/工单）
│   │   ├── services/           # 业务逻辑（健康评估等）
│   │   └── seed.py             # 数据导入脚本
│   ├── tests/                  # pytest 测试（30 个用例）
│   └── requirements.txt
├── data/                       # 数据目录（阶段1交付）
│   ├── README.md               # 数据来源与说明
│   ├── preprocess.py           # 数据预处理程序
│   ├── equipment.db            # SQLite 数据库（由 seed.py 生成）
│   ├── raw/CMAPSS/             # 官方原始数据（FD001 核心子集）
│   └── processed/              # 预处理后数据文件与参数
└── prompt/                     # AI 提示词追溯记录（每阶段归档）
    ├── stage1_data_preparation_2026-08-30.json
    └── stage2_project_init_backend_2026-08-30.json
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

## 四、后端运行说明（阶段2交付）

```bash
cd backend
pip install -r requirements.txt        # 安装依赖
python -m app.seed                     # 导入预处理数据生成 equipment.db（可重复执行）
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000   # 启动服务
python -m pytest tests -v              # 运行自动化测试（30 个用例）
```

服务启动后访问 `http://127.0.0.1:8000/docs` 查看 Swagger 接口文档。
接口统一返回 `{"code": 0, "message": "success", "data": ...}`，前缀 `/api/v1`，覆盖：
设备台账 CRUD、传感器时序查询（支持归一化/异常标红）、健康评估、预警中心、运维工单（预警→工单闭环）。

## 五、开发进度

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| 阶段 1 | 数据准备：数据来源 + 预处理 + prompt 追溯 | ✅ 完成（2026-08-30） |
| 阶段 2 | 项目初始化 + 数据库表结构 + 后端基础接口 + 自动化测试 | ✅ 完成（2026-08-30） |
| 阶段 3 | 算法模块：随机森林/孤立森林/专家系统规则库 | ⏳ 待开始 |
| 阶段 4 | 前端孪生大屏与六大页面（Vue3+Element Plus+ECharts） | ⏳ 待开始 |
| 阶段 5 | 预警-诊断-工单闭环联调与整体测试 | ⏳ 待开始 |

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
