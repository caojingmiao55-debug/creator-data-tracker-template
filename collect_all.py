#!/usr/bin/env python3
"""
创作者数据采集工具
支持：抖音、小红书、视频号、公众号

使用方法：
  python collect_all.py              # 采集所有平台
  python collect_all.py --platform douyin  # 采集指定平台
"""
import json
import os
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

# ============================================================
# 配置
# ============================================================
ROOT_DIR = Path(__file__).parent
CONFIG_FILE = ROOT_DIR / "config.json"
DATA_FILE = ROOT_DIR / "data" / "all_data.json"
LOG_FILE = ROOT_DIR / "logs" / "collect.log"

# 导入数据库模块
import sys
sys.path.insert(0, str(ROOT_DIR / "data"))
from database import (
    init_db, save_daily_account, save_works,
    export_for_frontend, get_latest_account
)


# ============================================================
# 工具函数
# ============================================================
def log(msg):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def safe_int(val):
    """安全转换为整数"""
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def load_config():
    """加载配置"""
    if not CONFIG_FILE.exists():
        log("错误: config.json 不存在")
        return None
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_frontend_json():
    """生成前端需要的 JSON 文件"""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = export_for_frontend()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log(f"前端数据已更新: {DATA_FILE}")


def parse_cookies(cookie_str):
    """解析 Cookie 字符串为 Playwright 格式"""
    cookies = []
    for item in cookie_str.split(";"):
        item = item.strip()
        if "=" in item:
            name, value = item.split("=", 1)
            cookies.append({
                "name": name.strip(),
                "value": value.strip(),
                "path": "/",
            })
    return cookies


# ============================================================
# 数据结构：统一的账号和作品数据格式
# ============================================================
def create_empty_account(platform):
    """创建空的账号数据结构"""
    return {
        "platform": platform,
        "account_name": "",
        "account_id": "",
        "avatar_url": "",
        "followers": 0,
        "total_views": 0,
        "total_likes": 0,
        "total_comments": 0,
        "total_shares": 0,
        "total_collects": 0,
        "total_works": 0
    }


def create_work(platform, work_id="", title="", publish_time="", cover_url="", url="",
                views=0, likes=0, comments=0, shares=0, collects=0):
    """创建作品数据结构"""
    return {
        "work_id": work_id,
        "platform": platform,
        "title": title[:80] if title else "",
        "publish_time": publish_time,
        "cover_url": cover_url,
        "url": url,
        "views": safe_int(views),
        "likes": safe_int(likes),
        "comments": safe_int(comments),
        "shares": safe_int(shares),
        "collects": safe_int(collects)
    }


def calculate_account_totals(account, works):
    """从作品列表计算账号的汇总数据"""
    account["total_views"] = sum(w["views"] for w in works)
    account["total_likes"] = sum(w["likes"] for w in works)
    account["total_comments"] = sum(w["comments"] for w in works)
    account["total_shares"] = sum(w["shares"] for w in works)
    account["total_collects"] = sum(w["collects"] for w in works)
    account["total_works"] = len(works)
    return account


# ============================================================
# 采集器：小红书
# ============================================================
def collect_xiaohongshu(page, cookie_str):
    """采集小红书数据"""
    log("[小红书] 开始采集...")

    cookies = parse_cookies(cookie_str)
    for c in cookies:
        c["domain"] = ".xiaohongshu.com"
    page.context.add_cookies(cookies)

    account = create_empty_account("xiaohongshu")
    works = []
    api_data = {"user": None, "notes": None, "overview": None}

    def handle_response(response):
        try:
            url = response.url
            if "/api/galaxy/user/info" in url:
                data = response.json()
                if data.get("code") == 0:
                    api_data["user"] = data.get("data", {})
            elif "/fans/overall" in url:
                data = response.json()
                if data.get("code") == 0 and data.get("data"):
                    api_data["overview"] = data.get("data", {})
            elif "/api/galaxy/creator/datacenter/note/analyze/list" in url:
                data = response.json()
                if data.get("code") == 0:
                    api_data["notes"] = data.get("data", {}).get("note_infos", [])
        except (json.JSONDecodeError, KeyError, TypeError):
            pass  # 非目标响应，忽略

    page.on("response", handle_response)

    try:
        page.goto("https://creator.xiaohongshu.com/statistics/fans-data",
                  wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        page.goto("https://creator.xiaohongshu.com/statistics/data-analysis",
                  wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)

        # 解析用户信息
        if api_data["user"]:
            user = api_data["user"]
            account["account_name"] = user.get("userName", "") or user.get("name", "")
            account["account_id"] = user.get("redId", "") or user.get("userId", "")
            account["avatar_url"] = user.get("userAvatar", "") or user.get("avatar", "")

        # 从粉丝总览获取粉丝数
        if api_data["overview"]:
            seven_data = api_data["overview"].get("seven", {})
            account["followers"] = safe_int(seven_data.get("fans_count", 0))

        # 解析笔记数据
        if api_data["notes"]:
            for note in api_data["notes"]:
                publish_time = ""
                if note.get("post_time"):
                    try:
                        publish_time = datetime.fromtimestamp(
                            note["post_time"] / 1000
                        ).strftime("%Y-%m-%d %H:%M")
                    except (ValueError, OSError, TypeError):
                        pass

                work = create_work(
                    platform="xiaohongshu",
                    work_id=note.get("id", ""),
                    title=note.get("title", ""),
                    publish_time=publish_time,
                    cover_url=note.get("cover_url", ""),
                    url=f"https://www.xiaohongshu.com/explore/{note.get('id', '')}",
                    views=note.get("read_count", 0),
                    likes=note.get("like_count", 0),
                    comments=note.get("comment_count", 0),
                    shares=note.get("share_count", 0),
                    collects=note.get("fav_count", 0)
                )
                works.append(work)

        # 计算汇总
        calculate_account_totals(account, works)

        log(f"[小红书] 采集完成: {account['account_name']}, {len(works)} 个作品")
        return {"account": account, "works": works}

    except Exception as e:
        log(f"[小红书] 采集失败: {e}")
        return None


# ============================================================
# 采集器：抖音
# ============================================================
def collect_douyin(page, cookie_str):
    """采集抖音数据"""
    log("[抖音] 开始采集...")

    cookies = parse_cookies(cookie_str)
    for c in cookies:
        c["domain"] = ".douyin.com"
    page.context.add_cookies(cookies)

    account = create_empty_account("douyin")
    works = []
    api_data = {"works": []}

    def handle_response(response):
        try:
            url = response.url
            if "/janus/douyin/creator/pc/work_list" in url or "/work_list" in url:
                data = response.json()
                if data.get("status_code") == 0:
                    aweme_list = data.get("aweme_list", [])
                    api_data["works"].extend(aweme_list)
        except (json.JSONDecodeError, KeyError, TypeError):
            pass  # 非目标响应，忽略

    page.on("response", handle_response)

    try:
        page.goto("https://creator.douyin.com/creator-micro/home",
                  wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        page.goto("https://creator.douyin.com/creator-micro/content/manage",
                  wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)
        page.evaluate("window.scrollTo(0, 500)")
        page.wait_for_timeout(2000)

        if not api_data["works"]:
            page.goto("https://creator.douyin.com/creator/content/manage",
                      wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)

        # 解析作品数据
        for item in api_data["works"]:
            # 从第一个作品获取用户信息
            if not account["account_name"] and item.get("author"):
                author = item["author"]
                account["account_name"] = author.get("nickname", "")
                account["account_id"] = str(author.get("uid", "") or author.get("unique_id", ""))
                account["followers"] = safe_int(
                    author.get("follower_count", 0) or author.get("mplatform_followers_count", 0)
                )
                # 头像
                for key in ["avatar_thumb", "avatar_medium", "avatar_larger"]:
                    if author.get(key, {}).get("url_list"):
                        account["avatar_url"] = author[key]["url_list"][0]
                        break

            stats = item.get("statistics", {})
            publish_time = ""
            if item.get("create_time"):
                try:
                    publish_time = datetime.fromtimestamp(item["create_time"]).strftime("%Y-%m-%d %H:%M")
                except (ValueError, OSError, TypeError):
                    pass

            cover_url = ""
            if item.get("cover", {}).get("url_list"):
                cover_url = item["cover"]["url_list"][0]

            work = create_work(
                platform="douyin",
                work_id=item.get("aweme_id", ""),
                title=item.get("desc", ""),
                publish_time=publish_time,
                cover_url=cover_url,
                url=f"https://www.douyin.com/video/{item.get('aweme_id', '')}",
                views=stats.get("play_count", 0),
                likes=stats.get("digg_count", 0),
                comments=stats.get("comment_count", 0),
                shares=stats.get("share_count", 0),
                collects=stats.get("collect_count", 0)
            )
            works.append(work)

        # 计算汇总
        calculate_account_totals(account, works)

        log(f"[抖音] 采集完成: {account['account_name']}, {len(works)} 个作品")
        return {"account": account, "works": works}

    except Exception as e:
        log(f"[抖音] 采集失败: {e}")
        return None


# ============================================================
# 采集器：视频号
# ============================================================
def collect_shipinhao(page, cookie_str, playwright_instance=None, allow_interactive_login=True):
    """采集视频号数据"""
    log("[视频号] 开始采集...")

    cookies = parse_cookies(cookie_str)
    for c in cookies:
        c["domain"] = ".weixin.qq.com"
    page.context.add_cookies(cookies)

    account = create_empty_account("shipinhao")
    works = []
    api_data = {"auth": None, "posts": [], "need_login": False}
    result_status = {"status": "success", "message": ""}

    def handle_response(response):
        try:
            url = response.url
            if "/auth/auth_data" in url:
                data = response.json()
                if data.get("errCode") == 0:
                    api_data["auth"] = data.get("data", {})
                elif data.get("errCode") == 300334:
                    api_data["need_login"] = True
            elif "/post/post_list" in url:
                data = response.json()
                if data.get("errCode") == 0:
                    api_data["posts"].extend(data.get("data", {}).get("list", []))
        except (json.JSONDecodeError, KeyError, TypeError):
            pass  # 非目标响应，忽略

    page.on("response", handle_response)
    headed_browser = None

    try:
        page.goto("https://channels.weixin.qq.com/platform/post/list",
                  wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)

        need_login = "login" in page.url or api_data["need_login"] or not api_data["auth"]

        if need_login and playwright_instance and allow_interactive_login:
            log("[视频号] 需要登录，正在打开浏览器窗口...")
            page.context.close()

            headed_browser = playwright_instance.chromium.launch(headless=False)
            headed_context = headed_browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            headed_page = headed_context.new_page()

            api_data["auth"] = None
            api_data["posts"] = []
            headed_page.on("response", handle_response)

            headed_page.goto("https://channels.weixin.qq.com/platform/post/list",
                             wait_until="domcontentloaded", timeout=120000)
            log("[视频号] 请扫码登录...")

            for _ in range(120):
                headed_page.wait_for_timeout(1000)
                if "login" not in headed_page.url and api_data["auth"]:
                    log("[视频号] 登录成功！")
                    break
            else:
                log("[视频号] 登录超时")
                headed_browser.close()
                return {
                    "status": "pending_login",
                    "message": "登录超时",
                    "account": account,
                    "works": works
                }

            # 保存新 Cookie
            new_cookies = headed_context.cookies()
            cookie_parts = [f"{c['name']}={c['value']}" for c in new_cookies
                           if c["domain"].endswith("weixin.qq.com")]
            if cookie_parts:
                _save_cookie_to_config("shipinhao", "; ".join(cookie_parts))

            headed_page.wait_for_timeout(3000)
            page = headed_page

        elif need_login:
            log("[视频号] Cookie无效，需要登录")
            return {
                "status": "pending_login",
                "message": "等待登录",
                "account": account,
                "works": works
            }

        page.wait_for_timeout(5000)

        # 解析用户信息
        if api_data["auth"]:
            user = api_data["auth"].get("finderUser", {})
            account["account_name"] = user.get("nickname", "")
            account["account_id"] = user.get("uniqId", "") or user.get("finderUsername", "")
            account["followers"] = safe_int(user.get("fansCount", 0))
            account["avatar_url"] = user.get("headImgUrl", "")

        # 解析作品数据
        for item in api_data["posts"]:
            desc = item.get("desc", "")
            if isinstance(desc, dict):
                title = item.get("title", "") or "视频"
            else:
                title = str(desc)[:50] if desc else "视频"

            publish_time = ""
            if item.get("createTime"):
                try:
                    publish_time = datetime.fromtimestamp(item["createTime"]).strftime("%Y-%m-%d %H:%M")
                except (ValueError, OSError, TypeError):
                    pass

            work = create_work(
                platform="shipinhao",
                work_id=item.get("objectId", ""),
                title=title,
                publish_time=publish_time,
                cover_url=item.get("coverUrl", ""),
                url="",
                views=item.get("readCount", 0),
                likes=item.get("likeCount", 0),
                comments=item.get("commentCount", 0),
                shares=item.get("forwardCount", 0),
                collects=item.get("favCount", 0)
            )
            works.append(work)

        # 计算汇总
        calculate_account_totals(account, works)

        if headed_browser:
            headed_browser.close()

        log(f"[视频号] 采集完成: {account['account_name']}, {len(works)} 个作品")
        return {"status": "success", "message": "", "account": account, "works": works}

    except Exception as e:
        log(f"[视频号] 采集失败: {e}")
        if headed_browser:
            headed_browser.close()
        return {"status": "error", "message": str(e), "account": account, "works": works}


# ============================================================
# 采集器：公众号
# ============================================================
def collect_gongzhonghao(page, cookie_str, playwright_instance=None, allow_interactive_login=True):
    """采集公众号数据

    注意：公众号的 session 过期非常快，总是需要交互式登录。
    """
    log("[公众号] 开始采集...")

    account = create_empty_account("gongzhonghao")
    works = []
    api_data = {"articles": []}

    if not playwright_instance or not allow_interactive_login:
        log("[公众号] 需要交互式登录支持")
        return {
            "status": "pending_login",
            "message": "需要交互式登录",
            "account": account,
            "works": works
        }

    headed_browser = None

    try:
        log("[公众号] 正在打开浏览器窗口...")

        # 使用持久化上下文保存登录状态
        user_data_dir = ROOT_DIR / "data" / "browser_data" / "gongzhonghao"
        user_data_dir.mkdir(parents=True, exist_ok=True)

        headed_context = playwright_instance.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        headed_page = headed_context.new_page()
        headed_browser = None  # persistent context 不需要单独的 browser 对象

        headed_page.goto("https://mp.weixin.qq.com/", wait_until="domcontentloaded", timeout=120000)
        headed_page.wait_for_timeout(2000)

        # 检查是否已登录
        if "cgi-bin/home" not in headed_page.url and "cgi-bin/appmsg" not in headed_page.url:
            log("[公众号] 请扫码登录...")

            # 等待登录成功
            login_success = False
            for _ in range(120):
                headed_page.wait_for_timeout(1000)
                current_url = headed_page.url
                if "cgi-bin/home" in current_url or "cgi-bin/appmsg" in current_url:
                    log("[公众号] 登录成功！")
                    login_success = True
                    break

            if not login_success:
                log("[公众号] 登录超时")
                headed_context.close()
                return {
                    "status": "pending_login",
                    "message": "登录超时",
                    "account": account,
                    "works": works
                }

        # 保存新 Cookie
        new_cookies = headed_context.cookies()
        cookie_parts = [f"{c['name']}={c['value']}" for c in new_cookies
                       if c["domain"].endswith("qq.com")]
        if cookie_parts:
            _save_cookie_to_config("gongzhonghao", "; ".join(cookie_parts))

        headed_page.wait_for_timeout(2000)

        # 获取账号信息
        if "cgi-bin/home" not in headed_page.url:
            headed_page.goto("https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN",
                            wait_until="networkidle", timeout=30000)
            headed_page.wait_for_timeout(2000)

        try:
            cgi_data = headed_page.evaluate("window.wx && window.wx.cgiData")
            if cgi_data:
                account["account_name"] = cgi_data.get("nick_name", "")
                account["followers"] = safe_int(cgi_data.get("total_fans_count", 0))
                account["account_id"] = str(cgi_data.get("fakeid", "") or cgi_data.get("user_name", ""))
                log(f"[公众号] 获取账号信息: {account['account_name']}, 粉丝: {account['followers']}")
        except Exception as e:
            log(f"[公众号] 获取账号信息失败: {e}")

        # 获取 token
        import re
        token = None
        token_match = re.search(r'token=(\d+)', headed_page.url)
        if token_match:
            token = token_match.group(1)
        else:
            try:
                content = headed_page.content()
                token_match = re.search(r'token["\s:=]+(\d{8,})', content)
                if token_match:
                    token = token_match.group(1)
            except Exception:
                pass

        if token:
            log(f"[公众号] 获取 token: {token}")

            # 尝试多个 API 端点获取文章
            # 1. 已发布文章列表
            api_url = f"https://mp.weixin.qq.com/cgi-bin/appmsgpublish?sub=list&begin=0&count=20&token={token}&lang=zh_CN"
            headed_page.goto(api_url, wait_until="networkidle", timeout=15000)
            headed_page.wait_for_timeout(2000)

            try:
                json_text = headed_page.inner_text("body")
                log(f"[公众号] 已发布API响应: {len(json_text)} 字节")

                if json_text.startswith("{"):
                    data = json.loads(json_text)
                    if data.get("base_resp", {}).get("ret") == 0:
                        publish_page = data.get("publish_page", {})
                        api_data["articles"] = publish_page.get("publish_list", [])
                        total = publish_page.get("total_count", 0)
                        log(f"[公众号] 已发布文章: {len(api_data['articles'])} 条, 总数: {total}")
            except Exception as e:
                log(f"[公众号] 已发布API失败: {e}")

            # 2. 如果没有已发布文章，尝试图文消息列表 API
            if not api_data["articles"]:
                api_url2 = f"https://mp.weixin.qq.com/cgi-bin/appmsg?action=list_ex&begin=0&count=20&type=9&query=&token={token}&lang=zh_CN"
                headed_page.goto(api_url2, wait_until="networkidle", timeout=15000)
                headed_page.wait_for_timeout(2000)

                try:
                    json_text = headed_page.inner_text("body")
                    log(f"[公众号] 图文消息API响应: {len(json_text)} 字节")

                    if json_text.startswith("{"):
                        data = json.loads(json_text)
                        if data.get("base_resp", {}).get("ret") == 0:
                            app_msg_list = data.get("app_msg_list", [])
                            log(f"[公众号] 图文消息: {len(app_msg_list)} 条")

                            # 转换为统一格式
                            for msg in app_msg_list:
                                work = create_work(
                                    platform="gongzhonghao",
                                    work_id=str(msg.get("aid", "")),
                                    title=msg.get("title", ""),
                                    publish_time=datetime.fromtimestamp(msg.get("update_time", 0)).strftime("%Y-%m-%d %H:%M") if msg.get("update_time") else "",
                                    cover_url=msg.get("cover", ""),
                                    url=msg.get("link", ""),
                                    views=msg.get("read_num", 0),
                                    likes=msg.get("like_num", 0),
                                    comments=0,
                                    shares=0,
                                    collects=0
                                )
                                works.append(work)
                except Exception as e:
                    log(f"[公众号] 图文消息API失败: {e}")
        else:
            log("[公众号] 未能获取 token")

        # 等待一下让用户看到结果
        headed_page.wait_for_timeout(3000)

        headed_context.close()

        # 解析文章数据
        for item in api_data["articles"]:
            publish_info = item.get("publish_info", {})
            appmsg_info = publish_info.get("appmsgex", [])

            for article in appmsg_info:
                publish_time = ""
                if article.get("create_time"):
                    try:
                        publish_time = datetime.fromtimestamp(article["create_time"]).strftime("%Y-%m-%d %H:%M")
                    except (ValueError, OSError, TypeError):
                        pass

                appmsg_stat = article.get("appmsg_stat", {})

                work = create_work(
                    platform="gongzhonghao",
                    work_id=str(article.get("aid", "") or article.get("appmsgid", "")),
                    title=article.get("title", ""),
                    publish_time=publish_time,
                    cover_url=article.get("cover", ""),
                    url=article.get("link", ""),
                    views=appmsg_stat.get("read_num", 0),
                    likes=appmsg_stat.get("like_num", 0) + appmsg_stat.get("old_like_num", 0),
                    comments=appmsg_stat.get("comment_count", 0),
                    shares=appmsg_stat.get("share_num", 0),
                    collects=appmsg_stat.get("fav_num", 0)
                )
                works.append(work)

        calculate_account_totals(account, works)
        log(f"[公众号] 采集完成: {account['account_name']}, {len(works)} 篇文章")
        return {"status": "success", "message": "", "account": account, "works": works}

    except Exception as e:
        log(f"[公众号] 采集失败: {e}")
        try:
            headed_context.close()
        except Exception:
            pass
        return {"status": "error", "message": str(e), "account": account, "works": works}


def _save_cookie_to_config(platform, new_cookie):
    """保存新 Cookie 到配置文件"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        if platform in config:
            config[platform]["cookie"] = new_cookie
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        log(f"[{platform}] Cookie 已保存")
    except Exception as e:
        log(f"[{platform}] 保存 Cookie 失败: {e}")


# ============================================================
# 保存采集结果到数据库
# ============================================================
def save_platform_data(platform, result):
    """保存平台数据到 SQLite"""
    if not result:
        return

    account = result.get("account", {})
    works = result.get("works", [])

    # 保存每日账号数据
    save_daily_account(platform, account)

    # 保存作品数据
    if works:
        save_works(platform, works)

    log(f"[{platform}] 数据已保存到数据库")


# ============================================================
# Cookie 同步
# ============================================================
def sync_browser_cookies():
    """尝试从浏览器同步视频号 Cookie"""
    try:
        sys.path.insert(0, str(ROOT_DIR / "scripts"))
        from sync_cookie_from_browser import sync_cookies
        log("正在从浏览器同步 Cookie...")
        results = sync_cookies(browser="chrome", platforms=["shipinhao"], validate=False)
        if results.get("shipinhao", {}).get("success"):
            log("[视频号] Cookie 同步成功")
            return True
        else:
            log("[视频号] Cookie 同步失败")
            return False
    except Exception as e:
        log(f"Cookie 同步跳过: {e}")
        return False




# ============================================================
# Git 推送
# ============================================================
def push_to_github():
    """推送到 GitHub"""
    try:
        os.chdir(ROOT_DIR)
        # 只推送 JSON 文件（SQLite 数据库保留在本地）
        subprocess.run(["git", "add", "data/all_data.json"], check=True, capture_output=True)
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not result.stdout.strip():
            log("没有变更需要提交")
            return
        commit_msg = f"Auto update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
        subprocess.run(["git", "push"], check=True, capture_output=True)
        log("已推送到 GitHub")
    except Exception as e:
        log(f"Git 推送失败: {e}")


# ============================================================
# 主函数
# ============================================================
def main(target_platform=None):
    """主函数"""
    log("=" * 50)
    log(f"开始采集{'所有平台' if not target_platform else target_platform}数据")
    log("=" * 50)

    # 初始化数据库
    init_db()

    # 同步视频号 Cookie
    sync_browser_cookies()

    config = load_config()
    if not config:
        return

    # 采集器映射
    collectors = {
        "xiaohongshu": collect_xiaohongshu,
        "douyin": collect_douyin,
        "shipinhao": collect_shipinhao,
        "gongzhonghao": collect_gongzhonghao
    }

    platforms_to_collect = [target_platform] if target_platform else ["xiaohongshu", "douyin", "shipinhao", "gongzhonghao"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for platform in platforms_to_collect:
            platform_config = config.get(platform, {})

            if not platform_config.get("enabled", False):
                log(f"[{platform}] 已禁用，跳过")
                continue

            cookie = platform_config.get("cookie", "")
            if not cookie or cookie.startswith("在这里"):
                log(f"[{platform}] Cookie 未配置，跳过")
                continue

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = context.new_page()

            try:
                if platform in ["shipinhao", "gongzhonghao"]:
                    # 视频号/公众号：总是允许弹窗登录，因为 Cookie 可能随时失效
                    result = collectors[platform](page, cookie, p, allow_interactive_login=True)
                    if result:
                        status = result.get("status", "success")
                        if status == "success":
                            save_platform_data(platform, result)
                        else:
                            log(f"[{platform}] 状态: {status}")
                else:
                    result = collectors[platform](page, cookie)
                    if result:
                        save_platform_data(platform, result)

            except Exception as e:
                log(f"[{platform}] 采集异常: {e}")
            finally:
                context.close()

        browser.close()

    # 生成前端 JSON
    save_frontend_json()

    # 推送 GitHub
    if config.get("settings", {}).get("auto_push_to_github", False):
        push_to_github()

    log("=" * 50)
    log("采集完成!")
    log("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="创作者数据采集工具")
    parser.add_argument(
        "--platform",
        choices=["douyin", "xiaohongshu", "shipinhao", "gongzhonghao"],
        help="指定采集的平台，不指定则采集所有平台"
    )
    args = parser.parse_args()
    main(target_platform=args.platform)
