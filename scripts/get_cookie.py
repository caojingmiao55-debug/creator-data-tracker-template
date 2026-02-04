#!/usr/bin/env python3
"""
Cookie 获取辅助工具

这个脚本会打开各平台的创作者后台，引导你获取 Cookie
"""
import webbrowser
import sys


PLATFORMS = {
    "douyin": {
        "name": "抖音创作者后台",
        "url": "https://creator.douyin.com/",
        "steps": [
            "1. 在打开的页面中登录你的抖音账号",
            "2. 登录成功后，按 F12 打开开发者工具",
            "3. 切换到 Network（网络）标签页",
            "4. 刷新页面 (Cmd+R 或 F5)",
            "5. 在左侧请求列表中，点击任意一个请求",
            "6. 在右侧找到 Request Headers（请求标头）",
            "7. 找到 Cookie: 后面的内容，完整复制",
            "8. 粘贴到 config.json 的 douyin.cookie 字段"
        ]
    },
    "xiaohongshu": {
        "name": "小红书创作者中心",
        "url": "https://creator.xiaohongshu.com/",
        "steps": [
            "1. 在打开的页面中登录你的小红书账号",
            "2. 登录成功后，按 F12 打开开发者工具",
            "3. 切换到 Network（网络）标签页",
            "4. 刷新页面 (Cmd+R 或 F5)",
            "5. 在左侧请求列表中，点击任意一个 API 请求",
            "6. 在右侧找到 Request Headers（请求标头）",
            "7. 找到 Cookie: 后面的内容，完整复制",
            "8. 粘贴到 config.json 的 xiaohongshu.cookie 字段"
        ]
    },
    "shipinhao": {
        "name": "微信视频号助手",
        "url": "https://channels.weixin.qq.com/",
        "steps": [
            "1. 在打开的页面中用微信扫码登录",
            "2. 登录成功后，按 F12 打开开发者工具",
            "3. 切换到 Network（网络）标签页",
            "4. 刷新页面 (Cmd+R 或 F5)",
            "5. 在左侧请求列表中，点击任意一个请求",
            "6. 在右侧找到 Request Headers（请求标头）",
            "7. 找到 Cookie: 后面的内容，完整复制",
            "8. 粘贴到 config.json 的 shipinhao.cookie 字段",
            "",
            "注意：视频号 Cookie 有效期较短，可能需要经常重新获取"
        ]
    }
}


def show_help(platform: str):
    """显示获取 Cookie 的帮助信息"""
    if platform not in PLATFORMS:
        print(f"未知平台: {platform}")
        print(f"可用平台: {', '.join(PLATFORMS.keys())}")
        return

    info = PLATFORMS[platform]
    print(f"\n{'=' * 50}")
    print(f"获取 {info['name']} Cookie")
    print('=' * 50)

    print(f"\n正在打开 {info['url']} ...")
    webbrowser.open(info['url'])

    print("\n获取步骤:")
    for step in info['steps']:
        print(f"  {step}")

    print("\n" + "=" * 50)


def main():
    print("Cookie 获取辅助工具")
    print("=" * 50)

    if len(sys.argv) > 1:
        platform = sys.argv[1].lower()
        show_help(platform)
        return

    print("\n请选择要获取 Cookie 的平台:")
    print("  1. 抖音 (douyin)")
    print("  2. 小红书 (xiaohongshu)")
    print("  3. 视频号 (shipinhao)")
    print("  4. 全部")
    print("  0. 退出")

    choice = input("\n请输入选项 (0-4): ").strip()

    if choice == "0":
        return
    elif choice == "1":
        show_help("douyin")
    elif choice == "2":
        show_help("xiaohongshu")
    elif choice == "3":
        show_help("shipinhao")
    elif choice == "4":
        for platform in PLATFORMS:
            show_help(platform)
            input("\n按回车继续下一个平台...")
    else:
        print("无效选项")


if __name__ == "__main__":
    main()
