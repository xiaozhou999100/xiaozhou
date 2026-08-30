# 数据说明（C-MAPSS FD001）

> 课程设计：数字孪生车间智能监控与运维平台
> 本目录存放课程设计所需数据、预处理程序与预处理结果。

---

## 一、数据来源

本课程设计选用 **NASA C-MAPSS 涡扇发动机退化仿真数据集** 的 **FD001 子集** 作为核心实验数据，
该数据集为数字孪生与智能运维领域的通用公开仿真数据，可用于设备健康评估、剩余寿命（RUL）预测、
异常检测等研究。

- **数据集名称**：CMAPSS Jet Engine Simulated Data（C-MAPSS 涡扇发动机退化仿真数据集）
- **官方来源（有效链接）**：
  - NASA 开放数据门户（数据集主页）：
    https://data.nasa.gov/Aerospace/CMAPSS-Jet-Engine-Simulated-Data/ff5v-kuh6
  - 数据包直链（CMAPSSData.zip，含 FD001~FD004 全部子集）：
    https://data.nasa.gov/docs/legacy/CMAPSSData.zip
  - NASA PCoE 预测与健康管理数据仓库（项目主页）：
    https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/
- **引用文献**：A. Saxena, K. Goebel, D. Simon, and N. Eklund, "Damage Propagation Modeling for Aircraft
  Engine Run-to-Failure Simulation", in Proceedings of the 1st International Conference on Prognostics
  and Health Management (PHM08), Denver CO, Oct 2008.（论文 PDF 已随数据存放在 `raw/CMAPSS/`）
- **数据许可**：NASA 公开数据，标注来源即可用于教学科研。

> 说明：本仓库 `raw/CMAPSS/` 内直接保存了项目实际使用的 **FD001 核心子集**（数据量小，符合直接入库要求）；
> FD002~FD004 等其他子集数据量大且本项目暂不使用，可通过上述官方链接随时下载。

---

## 二、数据集介绍

FD001 子集为 **单工况（海平面）、单故障模式（高压压气机 HPC 退化）** 的 run-to-failure 全寿命退化数据：

| 项目 | 内容 |
| --- | --- |
| 训练集（train_FD001.txt） | 100 台发动机全寿命运行至故障的传感器时序数据，共 20,631 条记录 |
| 测试集（test_FD001.txt） | 100 台发动机在故障前某一时刻截断的时序数据，共 13,096 条记录 |
| 真实 RUL（RUL_FD001.txt） | 测试集每台发动机的真实剩余使用寿命（cycles） |
| 工况条件 | 1 种（海平面） |
| 故障模式 | 1 种（高压压气机退化） |
| 原始维度 | 每行 26 列：单元号 + 循环周期 + 3 个运行工况 + 21 个传感器测量值 |

数据为空格分隔文本，每行代表一次运行循环（cycle）的快照，同一台发动机（unit）按时间连续记录，
传感器数据带有噪声，模拟真实退化过程。

---

## 三、字段说明

### 3.1 原始 26 列

| 列 | 含义 |
| --- | --- |
| unit | 设备（发动机）编号 |
| cycle | 运行循环数（时间轴） |
| op_setting_1 / 2 / 3 | 运行工况设置（对性能有显著影响） |
| sensor_1 ~ sensor_21 | 21 个传感器测量值（温度、压力、转速等，含噪声） |

### 3.2 预处理后新增列

| 列 | 含义 |
| --- | --- |
| rul | 剩余使用寿命（cycles），训练集=单元最大周期-当前周期；测试集=真实RUL+(单元最后周期-当前周期) |
| health_score | 健康度评分（0~100），`clip(100 × rul / max_rul, 0, 100)` |
| health_grade | 健康等级：健康(≥75) / 注意(50~75) / 预警(25~50) / 严重(<25) |
| anomaly_label | 异常标签：0=正常，1=异常（健康度 < 25 视为异常点，供孤立森林/规则训练） |
| *_norm | 归一化列（MinMax，范围 0~1，仅基于训练集拟合） |

---

## 四、目录结构

```
data/
├── README.md                      # 本说明文件
├── preprocess.py                  # 数据预处理程序（可重复运行）
├── equipment.db                   # SQLite 数据库（预处理导出，供孪生平台读取，可再生成）
├── raw/
│   └── CMAPSS/                    # 官方原始数据（FD001 核心子集）
│       ├── train_FD001.txt        # 训练原始数据
│       ├── test_FD001.txt         # 测试原始数据
│       ├── RUL_FD001.txt          # 测试集真实 RUL
│       ├── readme.txt             # 官方数据说明
│       └── Damage Propagation Modeling.pdf   # 官方论文
└── processed/                     # 预处理结果（由 preprocess.py 生成）
    ├── train_FD001_processed.csv  # 预处理后训练数据
    ├── test_FD001_processed.csv   # 预处理后测试数据
    ├── device_profile.csv         # 设备台账概要（100 台设备，供台账页导入）
    ├── scaler_params.json         # 归一化参数（MinMax 的 min/max）
    └── sensor_meta.json           # 传感器保留/删除元信息
```

---

## 五、预处理流程说明

预处理程序 `preprocess.py` 执行以下步骤（对应《方案设计》3.3 数据集处理）：

1. **加载原始数据并补充列名**：为无表头的原始数据添加设备ID、时间、工况、传感器列名；
2. **删除无变化列**：剔除训练集中零方差的传感器列（FD001 下共剔除 6 个：sensor_1、5、10、16、18、19）与恒值工况列 op_setting_3，保留 15 个有效传感器 + 2 个工况列；
3. **构造健康/异常标签**：计算 RUL、健康度评分、四级健康等级与异常标签；
4. **归一化**：对保留的传感器与工况列做 MinMax 归一化（0~1），**仅基于训练集拟合**，参数保存为 `scaler_params.json`；
5. **导出 SQLite**：将预处理数据与设备台账写入 `equipment.db`，供数字孪生平台实时读取。

### 运行方式

```bash
cd data
python preprocess.py
```

依赖：`pandas`、`numpy`、`scikit-learn`（安装：`pip install pandas numpy scikit-learn`）

---

## 六、数据使用场景（对应系统功能）

| 系统功能 | 使用数据 |
| --- | --- |
| 车间设备台账 | `device_profile.csv` / SQLite `device_profile` 表（100 台设备） |
| 数字孪生可视化 | 训练集时序数据，映射设备状态、健康等级 |
| 实时数据监测 | 预处理后传感器时序（`*_norm` 列），异常点标红 |
| 健康与能耗评估 | 随机森林回归：基于传感器统计特征预测 RUL/健康度 |
| 异常预警 | 孤立森林 + 阈值规则：基于 `anomaly_label` 训练，识别传感器异常 |
| 专家系统诊断 | 结合异常点位与健康等级，触发 IF-THEN 规则库生成工单 |
