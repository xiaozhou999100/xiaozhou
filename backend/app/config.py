# -*- coding: utf-8 -*-
"""后端配置：路径、分页、枚举常量。"""

from pathlib import Path

# 目录定位：backend/app/config.py -> backend/ -> 项目根
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"

# 数据库文件（由 seed.py 生成，可再生成，已 gitignore）
DB_PATH = DATA_DIR / "equipment.db"

# 分页默认值
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# 业务枚举（与 PROJECT_RULES.md 一致）
TWIN_STATUS = ("运行", "待机", "报警")          # 孪生设备状态
HEALTH_GRADES = ("健康", "注意", "预警", "严重") # 健康等级
ALERT_LEVELS = ("提示", "警告", "严重")          # 预警等级
ALERT_TYPES = ("传感器异常", "能耗超标", "健康度过低", "节拍异常")  # 预警类型
WORK_ORDER_STATUS = ("待处理", "维修中", "已完成") # 工单状态
