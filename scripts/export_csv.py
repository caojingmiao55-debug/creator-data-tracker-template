#!/usr/bin/env python3
"""
导出 JSON 数据到 CSV 表格
"""
import json
import csv
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).parent
DATA_FILE = ROOT_DIR / "data" / "all_data.json"
CSV_DIR = ROOT_DIR / "data"


def export_to_csv():
    """将 JSON 数据导出为 CSV 表格"""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    today = datetime.now().strftime("%Y-%m-%d")

    # 1. 导出账号数据
    accounts_file = CSV_DIR / "accounts.csv"
    file_exists = accounts_file.exists()

    with open(accounts_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "date", "platform", "account_name", "account_id", "followers",
                "total_impressions", "total_views", "total_likes", "total_collects", "total_works"
            ])

        for platform in ["douyin", "xiaohongshu", "shipinhao"]:
            if data.get(platform) and data[platform].get("account"):
                acc = data[platform]["account"]
                writer.writerow([
                    today, platform, acc.get("account_name", ""),
                    acc.get("account_id", ""), acc.get("followers", 0),
                    acc.get("total_impressions", 0), acc.get("total_views", 0),
                    acc.get("total_likes", 0), acc.get("total_collects", 0),
                    acc.get("total_works", 0)
                ])

    # 2. 导出作品数据
    works_file = CSV_DIR / "works.csv"
    file_exists = works_file.exists()

    with open(works_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "date", "platform", "work_id", "title", "publish_time",
                "impressions", "views", "likes", "comments", "shares", "collects",
                "click_rate", "avg_view_time", "new_followers"
            ])

        for platform in ["douyin", "xiaohongshu", "shipinhao"]:
            if data.get(platform) and data[platform].get("works"):
                for work in data[platform]["works"]:
                    writer.writerow([
                        today, platform, work.get("work_id", ""),
                        work.get("title", ""), work.get("publish_time", ""),
                        work.get("impressions", 0), work.get("views", 0),
                        work.get("likes", 0), work.get("comments", 0),
                        work.get("shares", 0), work.get("collects", 0),
                        work.get("click_rate", 0), work.get("avg_view_time", 0),
                        work.get("new_followers", 0)
                    ])

    # 3. 导出每日快照
    snapshots_file = CSV_DIR / "daily_snapshots.csv"
    file_exists = snapshots_file.exists()

    with open(snapshots_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "date", "platform", "followers", "followers_change",
                "total_impressions", "impressions_change", "total_views", "views_change",
                "total_likes", "likes_change", "total_collects", "collects_change"
            ])

        for snapshot in data.get("daily_snapshots", []):
            if snapshot.get("date") == today:
                writer.writerow([
                    snapshot.get("date"), snapshot.get("platform"),
                    snapshot.get("followers", 0), snapshot.get("followers_change", 0),
                    snapshot.get("total_impressions", 0), snapshot.get("impressions_change", 0),
                    snapshot.get("total_views", 0), snapshot.get("views_change", 0),
                    snapshot.get("total_likes", 0), snapshot.get("likes_change", 0),
                    snapshot.get("total_collects", 0), snapshot.get("collects_change", 0)
                ])

    print(f"数据已导出到 CSV:")
    print(f"  - {accounts_file}")
    print(f"  - {works_file}")
    print(f"  - {snapshots_file}")


if __name__ == "__main__":
    export_to_csv()
