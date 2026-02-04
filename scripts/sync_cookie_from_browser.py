#!/usr/bin/env python3
"""
从浏览器自动读取 Cookie 并更新到 config.json

使用方法:
    python sync_cookie_from_browser.py

支持的浏览器:
    - Google Chrome (默认)
    - Chromium
    - Edge
    - Firefox
    - Safari

注意:
    - 首次运行可能需要授权访问钥匙串
    - 需要先在浏览器中登录各平台
"""
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import browser_cookie3
except ImportError:
    print("错误: 需要安装 browser_cookie3 库")
    print("请运行: pip install browser-cookie3")
    sys.exit(1)


# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
CONFIG_FILE = ROOT_DIR / "config.json"
CONFIG_EXAMPLE = ROOT_DIR / "config.example.json"

# 平台域名映射
PLATFORM_DOMAINS = {
    "douyin": [".douyin.com", "creator.douyin.com"],
    "xiaohongshu": [".xiaohongshu.com", "creator.xiaohongshu.com"],
    "shipinhao": [".weixin.qq.com", "channels.weixin.qq.com", ".qq.com"]
}

# 平台中文名
PLATFORM_NAMES = {
    "douyin": "抖音",
    "xiaohongshu": "小红书",
    "shipinhao": "视频号"
}


def get_browser_cookies(browser: str = "chrome"):
    """
    获取浏览器的 Cookie Jar

    Args:
        browser: 浏览器名称 (chrome, chromium, edge, firefox, safari)

    Returns:
        CookieJar 对象
    """
    browser_funcs = {
        "chrome": browser_cookie3.chrome,
        "chromium": browser_cookie3.chromium,
        "edge": browser_cookie3.edge,
        "firefox": browser_cookie3.firefox,
        "safari": browser_cookie3.safari,
    }

    func = browser_funcs.get(browser.lower())
    if not func:
        raise ValueError(f"不支持的浏览器: {browser}")

    return func(domain_name="")


def extract_cookies_for_platform(cookie_jar, domains: list) -> str:
    """
    从 Cookie Jar 中提取指定域名的 Cookie

    Args:
        cookie_jar: Cookie Jar 对象
        domains: 域名列表

    Returns:
        Cookie 字符串
    """
    cookies = []
    seen = set()  # 去重

    for cookie in cookie_jar:
        # 检查是否匹配任一域名
        matched = False
        for domain in domains:
            if domain in cookie.domain or cookie.domain.endswith(domain.lstrip('.')):
                matched = True
                break

        if matched and cookie.name not in seen:
            cookies.append(f"{cookie.name}={cookie.value}")
            seen.add(cookie.name)

    return "; ".join(cookies)


def load_config() -> dict:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    elif CONFIG_EXAMPLE.exists():
        with open(CONFIG_EXAMPLE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {
            "douyin": {"enabled": True},
            "xiaohongshu": {"enabled": True},
            "shipinhao": {"enabled": True},
            "settings": {}
        }


def save_config(config: dict):
    """保存配置文件"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def sync_cookies(browser: str = "chrome", platforms: list = None, validate: bool = True):
    """
    从浏览器同步 Cookie 到配置文件

    Args:
        browser: 浏览器名称
        platforms: 要同步的平台列表，None 表示全部
        validate: 是否验证 Cookie 有效性

    Returns:
        同步结果字典
    """
    if platforms is None:
        platforms = list(PLATFORM_DOMAINS.keys())

    print(f"正在从 {browser.title()} 读取 Cookie...")
    print("(如果弹出钥匙串访问请求，请点击「允许」)\n")

    try:
        cookie_jar = get_browser_cookies(browser)
    except Exception as e:
        print(f"错误: 无法读取浏览器 Cookie: {e}")
        return {}

    config = load_config()
    results = {}

    for platform in platforms:
        domains = PLATFORM_DOMAINS.get(platform)
        if not domains:
            continue

        name = PLATFORM_NAMES.get(platform, platform)
        cookie_str = extract_cookies_for_platform(cookie_jar, domains)

        if cookie_str and len(cookie_str) > 50:
            # 更新配置
            if platform not in config:
                config[platform] = {"enabled": True}

            config[platform]["cookie"] = cookie_str
            config[platform]["cookie_updated_at"] = datetime.now().isoformat()
            config[platform]["cookie_source"] = f"browser_{browser}"

            results[platform] = {
                "success": True,
                "length": len(cookie_str)
            }
            print(f"✓ {name}: 获取成功 ({len(cookie_str)} 字符)")
        else:
            results[platform] = {
                "success": False,
                "error": "未找到有效Cookie，请确保已登录"
            }
            print(f"✗ {name}: 未找到有效 Cookie")

    # 保存配置
    if any(r["success"] for r in results.values()):
        save_config(config)
        print(f"\n已保存到 {CONFIG_FILE}")

    # 验证 Cookie
    if validate and any(r["success"] for r in results.values()):
        print("\n验证 Cookie 有效性...")
        try:
            from utils.cookie_validator import CookieValidator, CookieStatus

            for platform, result in results.items():
                if not result["success"]:
                    continue

                name = PLATFORM_NAMES.get(platform, platform)
                cookie = config[platform]["cookie"]
                validator = CookieValidator(cookie, platform)
                status, msg = validator.validate()

                if status == CookieStatus.VALID:
                    print(f"  ✓ {name}: 有效")
                    results[platform]["valid"] = True
                elif status == CookieStatus.EXPIRED:
                    print(f"  ✗ {name}: 已过期 - {msg}")
                    results[platform]["valid"] = False
                else:
                    print(f"  ? {name}: {status.value} - {msg}")
                    results[platform]["valid"] = None
        except ImportError:
            print("  (跳过验证: utils.cookie_validator 未找到)")

    return results


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="从浏览器自动读取 Cookie 并更新到 config.json"
    )
    parser.add_argument(
        "-b", "--browser",
        choices=["chrome", "chromium", "edge", "firefox", "safari"],
        default="chrome",
        help="浏览器类型 (默认: chrome)"
    )
    parser.add_argument(
        "-p", "--platform",
        choices=["douyin", "xiaohongshu", "shipinhao"],
        action="append",
        help="指定要同步的平台 (可多次使用，默认全部)"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="跳过 Cookie 有效性验证"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("Cookie 自动同步工具")
    print("=" * 50)
    print()

    results = sync_cookies(
        browser=args.browser,
        platforms=args.platform,
        validate=not args.no_validate
    )

    print()
    print("=" * 50)

    success_count = sum(1 for r in results.values() if r.get("success"))
    print(f"同步完成: {success_count}/{len(results)} 个平台")

    if success_count > 0:
        print("\n现在可以运行 python main.py 采集数据了")


if __name__ == "__main__":
    main()
