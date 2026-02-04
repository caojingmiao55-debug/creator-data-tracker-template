#!/usr/bin/env python3
"""
将现有 JSON 数据迁移到 SQLite
"""
import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent  # 项目根目录
JSON_FILE = ROOT_DIR / "data" / "all_data.json"

import sys
sys.path.insert(0, str(ROOT_DIR / "data"))
from database import migrate_from_json, init_db, get_daily_data, get_works_by_platform

def main():
    print("开始迁移数据到 SQLite...")

    # 初始化数据库
    init_db()

    # 读取 JSON 数据
    if not JSON_FILE.exists():
        print("JSON 文件不存在，跳过迁移")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # 执行迁移
    migrate_from_json(json_data)

    # 验证迁移结果
    print("\n迁移结果验证:")
    daily_data = get_daily_data(days=90)
    print(f"- 每日记录数: {len(daily_data)}")

    for platform in ["douyin", "xiaohongshu", "shipinhao"]:
        works = get_works_by_platform(platform)
        print(f"- {platform} 作品数: {len(works)}")

    print("\n迁移完成!")
    print(f"数据库位置: {ROOT_DIR / 'data' / 'tracker.db'}")

if __name__ == "__main__":
    main()
