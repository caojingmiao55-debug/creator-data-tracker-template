#!/usr/bin/env python3
"""
小红书登录脚本 - 只需运行一次

运行此脚本会弹出浏览器，登录后关闭浏览器即可。
之后的数据采集会自动使用保存的登录状态。
"""
import os
import time
from playwright.sync_api import sync_playwright

BROWSER_DATA_DIR = os.path.expanduser("~/.creator-data-tracker/browser-data/xiaohongshu")
LOGIN_FLAG_FILE = os.path.join(BROWSER_DATA_DIR, ".logged_in")

def main():
    os.makedirs(BROWSER_DATA_DIR, exist_ok=True)

    print("=" * 50)
    print("小红书登录")
    print("=" * 50)
    print()
    print("浏览器将打开小红书创作者中心，请登录。")
    print("登录成功后，关闭浏览器窗口即可。")
    print()

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            BROWSER_DATA_DIR,
            headless=False,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800},
            locale="zh-CN"
        )

        page = context.new_page()
        page.goto("https://creator.xiaohongshu.com/creator/home")

        print("等待登录...")

        # 等待用户关闭浏览器
        try:
            while True:
                time.sleep(1)
                # 检查是否已登录
                if 'login' not in page.url.lower() and 'creator' in page.url:
                    # 标记已登录
                    with open(LOGIN_FLAG_FILE, 'w') as f:
                        f.write("logged_in")
        except:
            pass

        context.close()

    print()
    print("登录状态已保存！之后的数据采集会自动使用此登录状态。")

if __name__ == "__main__":
    main()
