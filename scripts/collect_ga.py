#!/usr/bin/env python3
"""
Google Analytics 数据采集
"""
import json
import time
import functools
from datetime import datetime, timedelta
from pathlib import Path
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest
)

import sys
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "data"))
from database import init_db, save_daily_ga, get_ga_history
CREDENTIALS_FILE = ROOT_DIR / "config" / "ga_credentials.json"
PROPERTY_ID = "485215519"  # 从你的 GA URL 提取

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 5  # 初始延迟秒数
RETRY_BACKOFF = 2  # 指数退避倍数


def retry_on_failure(max_retries=MAX_RETRIES, delay=RETRY_DELAY, backoff=RETRY_BACKOFF):
    """重试装饰器，带指数退避"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        print(f"  ⚠️  {func.__name__} 失败 (尝试 {attempt + 1}/{max_retries + 1}): {type(e).__name__}")
                        print(f"      {current_delay} 秒后重试...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        print(f"  ❌ {func.__name__} 最终失败: {e}")

            raise last_exception
        return wrapper
    return decorator


def get_client():
    """获取 GA 客户端"""
    import os

    # 验证凭据文件存在
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(f"GA 凭据文件不存在: {CREDENTIALS_FILE}")

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CREDENTIALS_FILE)
    return BetaAnalyticsDataClient()


@retry_on_failure()
def fetch_overview(days=7):
    """获取概览数据"""
    client = get_client()

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="yesterday")],
        metrics=[
            Metric(name="activeUsers"),           # 活跃用户
            Metric(name="sessions"),              # 会话数
            Metric(name="screenPageViews"),       # 页面浏览量
            Metric(name="averageSessionDuration"),# 平均会话时长
            Metric(name="bounceRate"),            # 跳出率
            Metric(name="newUsers"),              # 新用户
        ]
    )

    response = client.run_report(request)

    if response.rows:
        row = response.rows[0]
        return {
            "active_users": int(row.metric_values[0].value),
            "sessions": int(row.metric_values[1].value),
            "page_views": int(row.metric_values[2].value),
            "avg_session_duration": float(row.metric_values[3].value),
            "bounce_rate": float(row.metric_values[4].value),
            "new_users": int(row.metric_values[5].value),
        }
    return None


@retry_on_failure()
def fetch_yesterday_data():
    """获取昨天的完整数据（用于保存到数据库历史记录）"""
    client = get_client()

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date="yesterday", end_date="yesterday")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
            Metric(name="screenPageViews"),
            Metric(name="averageSessionDuration"),
            Metric(name="bounceRate"),
            Metric(name="newUsers"),
        ]
    )

    response = client.run_report(request)

    if response.rows:
        row = response.rows[0]
        return {
            "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "active_users": int(row.metric_values[0].value),
            "sessions": int(row.metric_values[1].value),
            "page_views": int(row.metric_values[2].value),
            "avg_session_duration": float(row.metric_values[3].value),
            "bounce_rate": float(row.metric_values[4].value),
            "new_users": int(row.metric_values[5].value),
        }
    return None


@retry_on_failure()
def fetch_daily_trend(days=30):
    """获取每日趋势"""
    client = get_client()

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="yesterday")],
        dimensions=[Dimension(name="date")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
            Metric(name="screenPageViews"),
            Metric(name="newUsers"),
        ],
        order_bys=[{"dimension": {"dimension_name": "date"}}]
    )

    response = client.run_report(request)

    result = []
    for row in response.rows:
        date_str = row.dimension_values[0].value
        # 转换日期格式 YYYYMMDD -> YYYY-MM-DD
        date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        result.append({
            "date": date_formatted,
            "active_users": int(row.metric_values[0].value),
            "sessions": int(row.metric_values[1].value),
            "page_views": int(row.metric_values[2].value),
            "new_users": int(row.metric_values[3].value),
        })

    return result


@retry_on_failure()
def fetch_traffic_sources(days=30):
    """获取流量来源"""
    client = get_client()

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="yesterday")],
        dimensions=[Dimension(name="sessionSource")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="activeUsers"),
        ],
        order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        limit=10
    )

    response = client.run_report(request)

    result = []
    for row in response.rows:
        result.append({
            "source": row.dimension_values[0].value,
            "sessions": int(row.metric_values[0].value),
            "users": int(row.metric_values[1].value),
        })

    return result


@retry_on_failure()
def fetch_top_pages(days=30):
    """获取热门页面"""
    client = get_client()

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="yesterday")],
        dimensions=[Dimension(name="pagePath")],
        metrics=[
            Metric(name="screenPageViews"),
            Metric(name="activeUsers"),
        ],
        order_bys=[{"metric": {"metric_name": "screenPageViews"}, "desc": True}],
        limit=10
    )

    response = client.run_report(request)

    result = []
    for row in response.rows:
        result.append({
            "page": row.dimension_values[0].value,
            "views": int(row.metric_values[0].value),
            "users": int(row.metric_values[1].value),
        })

    return result


@retry_on_failure()
def fetch_geo(days=30):
    """获取地理位置分布"""
    client = get_client()

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="yesterday")],
        dimensions=[Dimension(name="country")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
        ],
        order_bys=[{"metric": {"metric_name": "activeUsers"}, "desc": True}],
        limit=10
    )

    response = client.run_report(request)

    result = []
    for row in response.rows:
        result.append({
            "country": row.dimension_values[0].value,
            "users": int(row.metric_values[0].value),
            "sessions": int(row.metric_values[1].value),
        })

    return result


@retry_on_failure()
def fetch_devices(days=30):
    """获取设备类型分布"""
    client = get_client()

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="yesterday")],
        dimensions=[Dimension(name="deviceCategory")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
        ],
        order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}]
    )

    response = client.run_report(request)

    result = []
    for row in response.rows:
        result.append({
            "device": row.dimension_values[0].value,
            "users": int(row.metric_values[0].value),
            "sessions": int(row.metric_values[1].value),
        })

    return result


@retry_on_failure()
def fetch_operating_systems(days=30):
    """获取操作系统分布"""
    client = get_client()

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="yesterday")],
        dimensions=[Dimension(name="operatingSystem")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
        ],
        order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        limit=10
    )

    response = client.run_report(request)

    result = []
    for row in response.rows:
        result.append({
            "os": row.dimension_values[0].value,
            "users": int(row.metric_values[0].value),
            "sessions": int(row.metric_values[1].value),
        })

    return result


@retry_on_failure()
def fetch_languages(days=30):
    """获取语言分布"""
    client = get_client()

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="yesterday")],
        dimensions=[Dimension(name="language")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
        ],
        order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        limit=10
    )

    response = client.run_report(request)

    result = []
    for row in response.rows:
        result.append({
            "language": row.dimension_values[0].value,
            "users": int(row.metric_values[0].value),
            "sessions": int(row.metric_values[1].value),
        })

    return result


@retry_on_failure()
def fetch_landing_pages(days=30):
    """获取着陆页分布"""
    client = get_client()

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="yesterday")],
        dimensions=[Dimension(name="landingPage")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="activeUsers"),
            Metric(name="bounceRate"),
        ],
        order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        limit=10
    )

    response = client.run_report(request)

    result = []
    for row in response.rows:
        result.append({
            "page": row.dimension_values[0].value,
            "sessions": int(row.metric_values[0].value),
            "users": int(row.metric_values[1].value),
            "bounce_rate": float(row.metric_values[2].value),
        })

    return result


@retry_on_failure()
def fetch_exit_pages(days=30):
    """获取退出页分布"""
    client = get_client()

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="yesterday")],
        dimensions=[Dimension(name="pagePath")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="activeUsers"),
        ],
        order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        limit=10
    )

    response = client.run_report(request)

    result = []
    for row in response.rows:
        result.append({
            "page": row.dimension_values[0].value,
            "sessions": int(row.metric_values[0].value),
            "users": int(row.metric_values[1].value),
        })

    return result


@retry_on_failure()
def fetch_signups(days=30):
    """获取注册数据"""
    client = get_client()

    # 获取注册总数
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="yesterday")],
        dimensions=[Dimension(name="eventName")],
        metrics=[
            Metric(name="eventCount"),
            Metric(name="totalUsers"),
        ],
        dimension_filter={
            "filter": {
                "field_name": "eventName",
                "string_filter": {"value": "sign_up"}
            }
        }
    )

    response = client.run_report(request)

    total_signups = 0
    total_users = 0
    if response.rows:
        total_signups = int(response.rows[0].metric_values[0].value)
        total_users = int(response.rows[0].metric_values[1].value)

    # 获取按注册方式分布（如果有 method 参数）
    method_request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="yesterday")],
        dimensions=[
            Dimension(name="eventName"),
            Dimension(name="customEvent:method"),  # 自定义参数
        ],
        metrics=[Metric(name="eventCount")],
        dimension_filter={
            "filter": {
                "field_name": "eventName",
                "string_filter": {"value": "sign_up"}
            }
        },
        order_bys=[{"metric": {"metric_name": "eventCount"}, "desc": True}]
    )

    by_method = []
    try:
        method_response = client.run_report(method_request)
        for row in method_response.rows:
            method = row.dimension_values[1].value
            if method and method != "(not set)":
                by_method.append({
                    "method": method,
                    "count": int(row.metric_values[0].value)
                })
    except Exception:
        pass  # 如果没有 method 参数，忽略

    return {
        "total": total_signups,
        "users": total_users,
        "by_method": by_method
    }


@retry_on_failure()
def fetch_signup_trend(days=30):
    """获取每日注册趋势"""
    client = get_client()

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="yesterday")],
        dimensions=[
            Dimension(name="date"),
            Dimension(name="eventName"),
        ],
        metrics=[Metric(name="eventCount")],
        dimension_filter={
            "filter": {
                "field_name": "eventName",
                "string_filter": {"value": "sign_up"}
            }
        },
        order_bys=[{"dimension": {"dimension_name": "date"}}]
    )

    response = client.run_report(request)

    result = []
    for row in response.rows:
        date_str = row.dimension_values[0].value
        date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        result.append({
            "date": date_formatted,
            "signups": int(row.metric_values[0].value)
        })

    return result


def fetch_realtime_users():
    """获取实时在线用户数"""
    from google.analytics.data_v1beta.types import RunRealtimeReportRequest

    client = get_client()

    request = RunRealtimeReportRequest(
        property=f"properties/{PROPERTY_ID}",
        metrics=[Metric(name="activeUsers")]
    )

    try:
        response = client.run_realtime_report(request)
        if response.rows:
            return int(response.rows[0].metric_values[0].value)
        return 0
    except Exception as e:
        print(f"实时数据获取失败: {e}")
        return 0


def collect_all():
    """采集所有 GA 数据"""
    print("正在采集 Google Analytics 数据...")

    # 预检查：验证凭据文件
    if not CREDENTIALS_FILE.exists():
        print(f"❌ 错误: GA 凭据文件不存在: {CREDENTIALS_FILE}")
        raise FileNotFoundError(f"GA 凭据文件不存在: {CREDENTIALS_FILE}")

    # 初始化数据库
    init_db()

    errors = []

    def safe_fetch(name, func, *args, **kwargs):
        """安全地执行 fetch 操作，记录错误但不中断"""
        try:
            print(f"  采集 {name}...")
            result = func(*args, **kwargs)
            print(f"  ✅ {name} 完成")
            return result
        except Exception as e:
            print(f"  ❌ {name} 失败: {e}")
            errors.append((name, str(e)))
            return None

    # 获取昨日完整数据（用于存储到数据库历史记录）
    # 注意：使用昨天的数据而不是今天的，因为今天的数据在采集时刻还不完整
    yesterday_data = safe_fetch("昨日数据", fetch_yesterday_data)

    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "realtime_users": safe_fetch("实时用户", fetch_realtime_users),
        "overview_7d": safe_fetch("7天概览", fetch_overview, days=7),
        "overview_30d": safe_fetch("30天概览", fetch_overview, days=30),
        "daily_trend": safe_fetch("每日趋势", fetch_daily_trend, days=30),
        "traffic_sources": safe_fetch("流量来源", fetch_traffic_sources, days=30),
        "top_pages": safe_fetch("热门页面", fetch_top_pages, days=30),
        "geo": safe_fetch("地理分布", fetch_geo, days=30),
        "devices": safe_fetch("设备类型", fetch_devices, days=30),
        "operating_systems": safe_fetch("操作系统", fetch_operating_systems, days=30),
        "languages": safe_fetch("语言分布", fetch_languages, days=30),
        "landing_pages": safe_fetch("着陆页", fetch_landing_pages, days=30),
        "exit_pages": safe_fetch("退出页", fetch_exit_pages, days=30),
        "signups_7d": safe_fetch("7天注册", fetch_signups, days=7),
        "signups_30d": safe_fetch("30天注册", fetch_signups, days=30),
        "signup_trend": safe_fetch("注册趋势", fetch_signup_trend, days=30),
    }

    # 保存昨日完整数据到数据库
    if yesterday_data:
        save_daily_ga(yesterday_data)
        print(f"昨日 ({yesterday_data.get('date')}) GA 数据已保存到数据库")

    # 获取历史数据用于对比
    ga_history = get_ga_history(days=35)
    data["history"] = ga_history

    # 检查是否有关键数据
    critical_fields = ["overview_7d", "overview_30d", "daily_trend"]
    missing_critical = [f for f in critical_fields if data.get(f) is None]

    if missing_critical:
        print(f"\n❌ 关键数据缺失: {missing_critical}")
        raise RuntimeError(f"GA 数据采集失败，关键数据缺失: {missing_critical}")

    # 保存到 JSON
    output_file = ROOT_DIR / "data" / "ga_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ GA 数据已保存到 {output_file}")

    if errors:
        print(f"⚠️  有 {len(errors)} 个非关键错误:")
        for name, err in errors:
            print(f"   - {name}: {err}")

    return data


def print_summary():
    """打印数据摘要"""
    data = collect_all()

    print("\n" + "=" * 50)
    print("Google Analytics 数据摘要")
    print("=" * 50)

    if data["overview_7d"]:
        o = data["overview_7d"]
        print(f"\n【最近 7 天】")
        print(f"  活跃用户: {o['active_users']:,}")
        print(f"  新用户: {o['new_users']:,}")
        print(f"  会话数: {o['sessions']:,}")
        print(f"  页面浏览: {o['page_views']:,}")
        print(f"  平均时长: {o['avg_session_duration']:.1f} 秒")
        print(f"  跳出率: {o['bounce_rate']*100:.1f}%")

    if data["traffic_sources"]:
        print(f"\n【流量来源 TOP 5】")
        for i, src in enumerate(data["traffic_sources"][:5], 1):
            print(f"  {i}. {src['source']}: {src['sessions']} 会话")

    if data["top_pages"]:
        print(f"\n【热门页面 TOP 5】")
        for i, page in enumerate(data["top_pages"][:5], 1):
            print(f"  {i}. {page['page'][:40]}: {page['views']} 浏览")

    if data.get("signups_7d"):
        s7 = data["signups_7d"]
        s30 = data.get("signups_30d", {})
        print(f"\n【用户注册】")
        print(f"  最近 7 天: {s7.get('total', 0)} 次注册")
        print(f"  最近 30 天: {s30.get('total', 0)} 次注册")
        if s30.get("by_method"):
            print(f"  注册方式分布:")
            for m in s30["by_method"][:5]:
                print(f"    - {m['method']}: {m['count']} 次")


if __name__ == "__main__":
    print_summary()
