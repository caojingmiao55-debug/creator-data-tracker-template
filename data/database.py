"""
SQLite 数据库管理模块
"""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "tracker.db"


def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表结构"""
    conn = get_connection()
    cursor = conn.cursor()

    # 每日账号数据表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            platform TEXT NOT NULL,
            account_name TEXT DEFAULT '',
            account_id TEXT DEFAULT '',
            avatar_url TEXT DEFAULT '',
            followers INTEGER DEFAULT 0,
            total_views INTEGER DEFAULT 0,
            total_likes INTEGER DEFAULT 0,
            total_comments INTEGER DEFAULT 0,
            total_shares INTEGER DEFAULT 0,
            total_collects INTEGER DEFAULT 0,
            total_works INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, platform)
        )
    """)

    # 作品表（存储最新状态）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            title TEXT DEFAULT '',
            publish_time TEXT DEFAULT '',
            cover_url TEXT DEFAULT '',
            url TEXT DEFAULT '',
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            collects INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(work_id)
        )
    """)

    # GA 每日数据表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_ga (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            active_users INTEGER DEFAULT 0,
            sessions INTEGER DEFAULT 0,
            page_views INTEGER DEFAULT 0,
            avg_session_duration REAL DEFAULT 0,
            bounce_rate REAL DEFAULT 0,
            new_users INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_accounts(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_platform ON daily_accounts(platform)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_platform_date ON daily_accounts(platform, date DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_works_platform ON works(platform)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_works_platform_time ON works(platform, publish_time DESC)")

    conn.commit()
    conn.close()


def save_daily_account(platform, account_data):
    """保存每日账号数据"""
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO daily_accounts
        (date, platform, account_name, account_id, avatar_url,
         followers, total_views, total_likes, total_comments,
         total_shares, total_collects, total_works, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        today,
        platform,
        account_data.get("account_name", ""),
        account_data.get("account_id", ""),
        account_data.get("avatar_url", ""),
        account_data.get("followers", 0),
        account_data.get("total_views", 0),
        account_data.get("total_likes", 0),
        account_data.get("total_comments", 0),
        account_data.get("total_shares", 0),
        account_data.get("total_collects", 0),
        account_data.get("total_works", 0),
        now
    ))

    conn.commit()
    conn.close()


def save_works(platform, works_list):
    """保存作品数据（更新或插入）"""
    conn = get_connection()
    cursor = conn.cursor()

    for work in works_list:
        cursor.execute("""
            INSERT OR REPLACE INTO works
            (work_id, platform, title, publish_time, cover_url, url,
             views, likes, comments, shares, collects, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            work.get("work_id", ""),
            platform,
            work.get("title", ""),
            work.get("publish_time", ""),
            work.get("cover_url", ""),
            work.get("url", ""),
            work.get("views", 0),
            work.get("likes", 0),
            work.get("comments", 0),
            work.get("shares", 0),
            work.get("collects", 0)
        ))

    conn.commit()
    conn.close()


def save_daily_ga(ga_data, target_date=None):
    """保存每日 GA 数据

    Args:
        ga_data: GA 数据字典
        target_date: 指定日期，如果不指定则使用 ga_data 中的 date 字段，
                     如果都没有则使用今天
    """
    if target_date is None:
        target_date = ga_data.get("date", datetime.now().strftime("%Y-%m-%d"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO daily_ga
        (date, active_users, sessions, page_views, avg_session_duration, bounce_rate, new_users)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        target_date,
        ga_data.get("active_users", 0),
        ga_data.get("sessions", 0),
        ga_data.get("page_views", 0),
        ga_data.get("avg_session_duration", 0),
        ga_data.get("bounce_rate", 0),
        ga_data.get("new_users", 0)
    ))

    conn.commit()
    conn.close()


def get_ga_by_date(target_date):
    """获取指定日期的 GA 数据"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM daily_ga WHERE date = ?
    """, (target_date,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def get_ga_history(days=30):
    """获取最近 N 天的 GA 历史数据"""
    conn = get_connection()
    cursor = conn.cursor()

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT * FROM daily_ga
        WHERE date >= ?
        ORDER BY date DESC
    """, (cutoff,))

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return rows


def get_latest_account(platform):
    """获取平台最新账号数据"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM daily_accounts
        WHERE platform = ?
        ORDER BY date DESC
        LIMIT 1
    """, (platform,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def get_previous_account(platform, before_date):
    """获取指定日期之前的最新数据（用于计算变化）"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM daily_accounts
        WHERE platform = ? AND date < ?
        ORDER BY date DESC
        LIMIT 1
    """, (platform, before_date))

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def get_works_by_platform(platform, limit=50):
    """获取平台的作品列表"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM works
        WHERE platform = ?
        ORDER BY publish_time DESC
        LIMIT ?
    """, (platform, limit))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_daily_data(days=30):
    """获取最近 N 天的每日数据"""
    conn = get_connection()
    cursor = conn.cursor()

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT * FROM daily_accounts
        WHERE date >= ?
        ORDER BY date DESC, platform
    """, (cutoff,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_platform_trend(platform, days=30):
    """获取平台的趋势数据"""
    conn = get_connection()
    cursor = conn.cursor()

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT date, followers, total_views, total_likes,
               total_comments, total_shares, total_collects, total_works
        FROM daily_accounts
        WHERE platform = ? AND date >= ?
        ORDER BY date ASC
    """, (platform, cutoff))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_stats_summary():
    """获取统计摘要（用于快速查询）"""
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")

    result = {}

    for platform in ["douyin", "xiaohongshu", "shipinhao"]:
        # 获取今日数据
        cursor.execute("""
            SELECT * FROM daily_accounts
            WHERE platform = ? AND date = ?
        """, (platform, today))
        current = cursor.fetchone()

        # 获取昨日数据
        cursor.execute("""
            SELECT * FROM daily_accounts
            WHERE platform = ? AND date < ?
            ORDER BY date DESC LIMIT 1
        """, (platform, today))
        previous = cursor.fetchone()

        if current:
            current = dict(current)
            if previous:
                previous = dict(previous)
                # 计算变化（如果前一天数据为0，表示缺失，不计算变化）
                def calc_change(field):
                    prev_val = previous.get(field, 0)
                    curr_val = current.get(field, 0)
                    # 前一天为0可能是数据缺失，不显示变化
                    if prev_val == 0 and curr_val > 0:
                        return None  # 表示数据缺失，不是真正的变化
                    return curr_val - prev_val

                current["followers_change"] = current["followers"] - previous["followers"]
                current["views_change"] = current["total_views"] - previous["total_views"]
                current["likes_change"] = current["total_likes"] - previous["total_likes"]
                current["comments_change"] = calc_change("total_comments")
                current["shares_change"] = calc_change("total_shares")
                current["collects_change"] = current["total_collects"] - previous["total_collects"]
                current["works_change"] = current["total_works"] - previous["total_works"]
            else:
                for key in ["followers", "views", "likes", "comments", "shares", "collects", "works"]:
                    current[f"{key}_change"] = 0

            result[platform] = current

    conn.close()
    return result


def export_for_frontend():
    """导出前端需要的 JSON 数据（优化版：单次连接，批量查询）"""
    conn = get_connection()
    cursor = conn.cursor()

    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "daily_snapshots": []
    }

    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    # 一次性获取所有每日数据（按平台和日期排序）
    cursor.execute("""
        SELECT * FROM daily_accounts
        WHERE date >= ?
        ORDER BY platform, date ASC
    """, (cutoff,))
    all_daily = [dict(row) for row in cursor.fetchall()]

    # 按平台分组，方便计算变化
    by_platform = {}
    for row in all_daily:
        platform = row["platform"]
        if platform not in by_platform:
            by_platform[platform] = []
        by_platform[platform].append(row)

    def calc_change(curr_val, prev_val, field):
        """计算变化值，前一天为0时返回0（表示数据缺失）"""
        if prev_val == 0 and curr_val > 0 and field in ["total_comments", "total_shares"]:
            return 0
        return curr_val - prev_val

    # 计算每日快照（带变化值）
    for platform, rows in by_platform.items():
        prev = None
        for row in rows:
            snapshot = {
                "date": row["date"],
                "platform": platform,
                "followers": row["followers"],
                "followers_change": row["followers"] - (prev["followers"] if prev else 0),
                "total_views": row["total_views"],
                "views_change": row["total_views"] - (prev["total_views"] if prev else 0),
                "total_likes": row["total_likes"],
                "likes_change": row["total_likes"] - (prev["total_likes"] if prev else 0),
                "total_comments": row["total_comments"],
                "comments_change": calc_change(row["total_comments"], prev["total_comments"] if prev else 0, "total_comments"),
                "total_shares": row["total_shares"],
                "shares_change": calc_change(row["total_shares"], prev["total_shares"] if prev else 0, "total_shares"),
                "total_collects": row["total_collects"],
                "collects_change": row["total_collects"] - (prev["total_collects"] if prev else 0),
                "total_works": row["total_works"],
                "works_change": row["total_works"] - (prev["total_works"] if prev else 0)
            }
            data["daily_snapshots"].append(snapshot)
            prev = row

    # 按日期降序排列
    data["daily_snapshots"].sort(key=lambda x: (x["date"], x["platform"]), reverse=True)

    # 一次性获取各平台最新数据
    for platform in ["douyin", "xiaohongshu", "shipinhao"]:
        cursor.execute("""
            SELECT * FROM daily_accounts
            WHERE platform = ?
            ORDER BY date DESC LIMIT 1
        """, (platform,))
        latest = cursor.fetchone()

        cursor.execute("""
            SELECT work_id, platform, title, publish_time, cover_url, url,
                   views, likes, comments, shares, collects
            FROM works WHERE platform = ?
            ORDER BY publish_time DESC LIMIT 50
        """, (platform,))
        works = [dict(row) for row in cursor.fetchall()]

        if latest:
            latest = dict(latest)
            data[platform] = {
                "account": {
                    "platform": platform,
                    "account_name": latest["account_name"],
                    "account_id": latest["account_id"],
                    "avatar_url": latest["avatar_url"],
                    "followers": latest["followers"],
                    "total_views": latest["total_views"],
                    "total_likes": latest["total_likes"],
                    "total_comments": latest["total_comments"],
                    "total_shares": latest["total_shares"],
                    "total_collects": latest["total_collects"],
                    "total_works": latest["total_works"],
                    "last_updated": latest.get("created_at", "")
                },
                "works": works
            }

    conn.close()
    return data


def migrate_from_json(json_data):
    """从旧的 JSON 数据迁移到 SQLite"""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # 迁移 daily_snapshots
    for snapshot in json_data.get("daily_snapshots", []):
        cursor.execute("""
            INSERT OR IGNORE INTO daily_accounts
            (date, platform, followers, total_views, total_likes,
             total_comments, total_shares, total_collects, total_works)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.get("date", ""),
            snapshot.get("platform", ""),
            snapshot.get("followers", 0),
            snapshot.get("total_views", 0),
            snapshot.get("total_likes", 0),
            snapshot.get("total_comments", 0),
            snapshot.get("total_shares", 0),
            snapshot.get("total_collects", 0),
            snapshot.get("total_works", 0)
        ))

    # 迁移各平台数据
    for platform in ["douyin", "xiaohongshu", "shipinhao"]:
        platform_data = json_data.get(platform, {})

        # 更新账号信息到最新记录
        if platform_data.get("account"):
            account = platform_data["account"]
            cursor.execute("""
                UPDATE daily_accounts
                SET account_name = ?, account_id = ?, avatar_url = ?
                WHERE platform = ? AND date = (
                    SELECT MAX(date) FROM daily_accounts WHERE platform = ?
                )
            """, (
                account.get("account_name", ""),
                account.get("account_id", ""),
                account.get("avatar_url", ""),
                platform,
                platform
            ))

        # 迁移作品
        for work in platform_data.get("works", []):
            cursor.execute("""
                INSERT OR REPLACE INTO works
                (work_id, platform, title, publish_time, cover_url, url,
                 views, likes, comments, shares, collects)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                work.get("work_id", ""),
                platform,
                work.get("title", ""),
                work.get("publish_time", ""),
                work.get("cover_url", ""),
                work.get("url", ""),
                work.get("views", 0),
                work.get("likes", 0),
                work.get("comments", 0),
                work.get("shares", 0),
                work.get("collects", 0)
            ))

    conn.commit()
    conn.close()
    print(f"数据迁移完成: {DB_PATH}")


def cleanup_old_data(keep_days=90):
    """清理超过指定天数的旧数据"""
    conn = get_connection()
    cursor = conn.cursor()

    cutoff = (datetime.now() - timedelta(days=keep_days)).strftime("%Y-%m-%d")

    cursor.execute("DELETE FROM daily_accounts WHERE date < ?", (cutoff,))
    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted


# 初始化数据库
init_db()
