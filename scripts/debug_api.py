#!/usr/bin/env python3
"""
调试脚本 - 查看各平台 API 实际返回的数据结构
"""
import json
import requests


def load_config():
    with open("config.json", "r") as f:
        return json.load(f)


def debug_douyin(cookie: str):
    print("\n" + "=" * 50)
    print("调试抖音 API")
    print("=" * 50)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Cookie": cookie,
        "Referer": "https://creator.douyin.com/creator/home",
    })

    # 用户信息
    url = "https://creator.douyin.com/web/api/media/user/info/"
    print(f"\n请求: {url}")
    resp = session.get(url)
    print(f"状态码: {resp.status_code}")
    data = resp.json()
    print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)[:2000]}")


def debug_xiaohongshu(cookie: str):
    print("\n" + "=" * 50)
    print("调试小红书 API")
    print("=" * 50)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Cookie": cookie,
        "Referer": "https://creator.xiaohongshu.com/publish/publish",
        "Origin": "https://creator.xiaohongshu.com",
    })

    # 尝试不同的 API 端点
    endpoints = [
        "/api/galaxy/creator/home/personal_info",
        "/api/galaxy/creator/user/info",
        "/api/cas/customer/web/customer/info",
        "/web/api/sns/v2/note/user/posted",
    ]

    for endpoint in endpoints:
        url = f"https://creator.xiaohongshu.com{endpoint}"
        print(f"\n请求: {url}")
        try:
            resp = session.get(url)
            print(f"状态码: {resp.status_code}")
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)[:1500]}")
                except:
                    print(f"响应: {resp.text[:500]}")
        except Exception as e:
            print(f"错误: {e}")


def debug_shipinhao(cookie: str):
    print("\n" + "=" * 50)
    print("调试视频号 API")
    print("=" * 50)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Cookie": cookie,
        "Referer": "https://channels.weixin.qq.com/platform",
        "Origin": "https://channels.weixin.qq.com",
        "Content-Type": "application/json",
    })

    # 用户信息
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/auth/auth_data"
    print(f"\n请求: {url}")
    resp = session.post(url, json={})
    print(f"状态码: {resp.status_code}")
    data = resp.json()
    print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)[:2000]}")

    # 作品列表
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/post/post_list"
    print(f"\n请求: {url}")
    resp = session.post(url, json={"pageIndex": 0, "pageSize": 5, "status": 0})
    print(f"状态码: {resp.status_code}")
    data = resp.json()
    print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)[:3000]}")


if __name__ == "__main__":
    config = load_config()

    if config.get("douyin", {}).get("enabled"):
        debug_douyin(config["douyin"]["cookie"])

    if config.get("xiaohongshu", {}).get("enabled"):
        debug_xiaohongshu(config["xiaohongshu"]["cookie"])

    if config.get("shipinhao", {}).get("enabled"):
        debug_shipinhao(config["shipinhao"]["cookie"])
