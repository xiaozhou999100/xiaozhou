# PROJECT_RULES.md — 项目核心规则文件

> 课程设计：数字孪生车间智能监控与运维平台
> 本文件是项目开发的**总规则文件**。所有 AI 代码修改、功能开发必须**优先读取本文件 + 现有项目代码**，
> 禁止 AI 凭空重写代码；任何代码变更不得违反本文件约定。

---

## 1. 技术栈（锁定，不随意更换）

| 层 | 选型 | 版本/约束 |
| --- | --- | --- |
| 前端 | Vue3 + Element Plus + ECharts | Node.js LTS |
| 后端 | FastAPI | Python 3.10+（本机 3.13） |
| ORM | SQLAlchemy | 2.x，声明式 |
| 数据库 | SQLite | 单文件，免服务 |
| 算法 | scikit-learn（随机森林/孤立森林）+ pandas/numpy | CPU 即可 |
| 测试 | pytest + httpx TestClient | 无外部依赖 |
| 版本管理 | Git + GitHub | main 分支，小步提交 |

## 2. 目录结构规范

```
backend/                 # 后端（FastAPI）
  app/
    main.py              # 应用入口：创建 app、挂载路由
    config.py            # 配置（数据库路径等）
    database.py          # SQLAlchemy engine / Session / Base
    models/              # ORM 模型（每表一个模块）
    schemas/             # Pydantic 请求/响应模型
    routers/             # 路由（按业务模块拆分）
    services/            # 业务逻辑与算法调用层
    seed.py              # 数据导入脚本（processed CSV → SQLite）
  tests/                 # pytest 测试
  requirements.txt
data/                    # 数据（阶段1交付，见 data/README.md）
prompt/                  # AI 提示词追溯记录
readme.md
PROJECT_RULES.md         # 本文件
```

## 3. 命名规则

- **表名**：小写下划线复数，如 `equipment`、`sensor_data`、`work_order`
- **模型类**：PascalCase 单数，与表对应，如 `Equipment`、`SensorData`、`WorkOrder`
- **路由文件**：小写下划线，按业务命名，如 `equipment.py`、`work_orders.py`
- **API 前缀**：统一 `/api/v1`；资源名词复数，如 `/api/v1/equipment`
- **JSON 字段**：小写下划线（snake_case）
- **数据库文件**：`data/equipment.db`（已 gitignore，可再生成）

## 4. 接口返回格式（统一规范）

所有接口统一返回以下结构（列表接口 data 为数组，详情接口 data 为对象）：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

- `code=0` 表示成功；非 0 为业务错误码（4xx/5xx 用 HTTP 状态码 + code 区分）
- 分页参数统一 `page`（从 1 起）+ `page_size`（默认 20，最大 100），返回 `{total, items}`

## 5. 数据库表设计约定（阶段2 已落地）

| 表 | 说明 | 关键字段 |
| --- | --- | --- |
| `equipment` | 车间设备台账 | device_code(唯一)、name、model、station、install_date、twin_status、health_grade |
| `sensor_data` | 设备传感器时序数据 | equipment_id(FK)、cycle、op_setting_1/2、sensor_2..21、rul、health_score、health_grade、anomaly_label、*_norm |
| `health_evaluation` | 健康/能耗评估记录 | equipment_id(FK)、health_score、energy_efficiency、load_rate、detail |
| `alert` | 预警记录 | equipment_id(FK)、alert_type、level(提示/警告/严重)、message、sensor_point、is_handled |
| `work_order` | 运维工单 | alert_id(FK 可空)、equipment_id(FK)、title、description、diagnosis、status(待处理/维修中/已完成) |

业务闭环：台账 → 孪生可视化 → 数据监测 → 评估 → 预警 → 工单。

## 6. 代码规范

- 后端统一使用类型注解；路由只做参数校验与编排，业务逻辑放 `services/`
- 禁止在路由中直接拼 SQL；统一走 SQLAlchemy ORM
- 时间字段统一 `datetime`，入库用 `datetime.now()`（本地时区）
- 预警等级枚举：`提示/警告/严重`；工单状态枚举：`待处理/维修中/已完成`；孪生状态枚举：`运行/待机/报警`

## 7. 测试标准

- 每次功能改动必须跑通 `pytest`（`cd backend && python -m pytest`）
- 测试使用独立临时数据库（不污染 `data/equipment.db`）
- 新增功能必须配套对应测试用例（接口 200 校验 + 关键业务断言）

## 8. Git 提交规范

- 小步提交、精准备注，格式统一：`「功能模块-完成内容」`，如 `后端-设备台账-新增增删改查接口`
- AI 生成代码必须经过：人工读懂 → 本地运行 → 自动化测试 三重验证后方可提交

## 9. 过程留痕

- 每个阶段的 AI 交互记录归档到 `prompt/`（JSON），上下文压缩前先备份
- Git 提交记录 + prompt 记录 + 测试结果共同构成过程考核证据链
