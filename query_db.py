#!/usr/bin/env python3
"""
SQLite 数据库查询工具

用法:
  python query_db.py                  # 显示最近7天数据
  python query_db.py --days 30        # 显示最近30天数据
  python query_db.py --platform douyin # 显示指定平台数据
  python query_db.py --stats          # 显示统计摘要
  python query_db.py --works          # 显示作品列表
"""
import argparse
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent / "data"))
from database import (
    get_daily_data, get_platform_trend, get_stats_summary,
    get_works_by_platform, get_latest_account
)


def print_daily_data(days=7, platform=None):
    """打印每日数据"""
    data = get_daily_data(days=days)

    if platform:
        data = [d for d in data if d["platform"] == platform]

    if not data:
        print("无数据")
        return

    print(f"\n{'日期':<12} {'平台':<12} {'粉丝':>8} {'播放':>10} {'点赞':>8} {'评论':>6} {'分享':>6} {'收藏':>8}")
    print("-" * 80)

    for row in data:
        print(f"{row['date']:<12} {row['platform']:<12} "
              f"{row['followers']:>8} {row['total_views']:>10} "
              f"{row['total_likes']:>8} {row['total_comments']:>6} "
              f"{row['total_shares']:>6} {row['total_collects']:>8}")


def print_stats():
    """打印统计摘要"""
    stats = get_stats_summary()

    if not stats:
        print("无数据")
        return

    print("\n今日数据摘要:")
    print("-" * 60)

    def fmt_change(val):
        """格式化变化值，None 表示数据缺失"""
        if val is None:
            return "(无历史数据)"
        return f"({val:+,})"

    for platform, data in stats.items():
        # 计算总互动量 = 粉丝 + 播放 + 点赞 + 评论 + 分享 + 收藏
        total_interactions = (data['followers'] + data['total_views'] +
                              data['total_likes'] + data['total_comments'] +
                              data['total_shares'] + data['total_collects'])
        # 互动变化（如果评论或分享缺失历史数据则不计算）
        if data.get('comments_change') is None or data.get('shares_change') is None:
            interactions_change = None
        else:
            interactions_change = (data.get('followers_change', 0) + data.get('views_change', 0) +
                                   data.get('likes_change', 0) + data.get('comments_change', 0) +
                                   data.get('shares_change', 0) + data.get('collects_change', 0))

        print(f"\n【{platform}】")
        print(f"  总互动: {total_interactions:,} {fmt_change(interactions_change)}")
        print(f"    ├ 粉丝: {data['followers']:,} {fmt_change(data.get('followers_change'))}")
        print(f"    ├ 播放: {data['total_views']:,} {fmt_change(data.get('views_change'))}")
        print(f"    ├ 点赞: {data['total_likes']:,} {fmt_change(data.get('likes_change'))}")
        print(f"    ├ 评论: {data['total_comments']:,} {fmt_change(data.get('comments_change'))}")
        print(f"    ├ 分享: {data['total_shares']:,} {fmt_change(data.get('shares_change'))}")
        print(f"    └ 收藏: {data['total_collects']:,} {fmt_change(data.get('collects_change'))}")


def print_works(platform=None):
    """打印作品列表"""
    platforms = [platform] if platform else ["douyin", "xiaohongshu", "shipinhao"]

    for p in platforms:
        works = get_works_by_platform(p, limit=10)
        if not works:
            continue

        print(f"\n【{p}】作品列表:")
        print("-" * 60)

        for i, w in enumerate(works, 1):
            title = w['title'][:30] + "..." if len(w['title']) > 30 else w['title']
            print(f"{i}. {title}")
            print(f"   播放:{w['views']:,} 点赞:{w['likes']:,} 评论:{w['comments']:,} "
                  f"分享:{w['shares']:,} 收藏:{w['collects']:,}")


def main():
    parser = argparse.ArgumentParser(description="SQLite 数据库查询工具")
    parser.add_argument("--days", type=int, default=7, help="查询天数（默认7天）")
    parser.add_argument("--platform", choices=["douyin", "xiaohongshu", "shipinhao"],
                        help="指定平台")
    parser.add_argument("--stats", action="store_true", help="显示统计摘要")
    parser.add_argument("--works", action="store_true", help="显示作品列表")

    args = parser.parse_args()

    if args.stats:
        print_stats()
    elif args.works:
        print_works(args.platform)
    else:
        print_daily_data(args.days, args.platform)


if __name__ == "__main__":
    main()
