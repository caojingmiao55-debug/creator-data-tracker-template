#!/usr/bin/env python3
"""
项目初始化脚本
帮助用户快速配置 creator-data-tracker
"""
import os
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent

def log(msg: str, level: str = "INFO"):
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
    }
    reset = "\033[0m"
    print(f"{colors.get(level, '')}{msg}{reset}")


def copy_if_not_exists(src: Path, dst: Path, name: str):
    """如果目标文件不存在，则复制模板文件"""
    if dst.exists():
        log(f"  ✓ {name} 已存在，跳过", "SUCCESS")
        return False

    if not src.exists():
        log(f"  ✗ 模板文件 {src.name} 不存在", "ERROR")
        return False

    shutil.copy(src, dst)
    log(f"  ✓ 已创建 {name}", "SUCCESS")
    return True


def create_directory(path: Path, name: str):
    """创建目录"""
    if path.exists():
        log(f"  ✓ {name} 目录已存在", "SUCCESS")
        return
    path.mkdir(parents=True)
    log(f"  ✓ 已创建 {name} 目录", "SUCCESS")


def main():
    print("=" * 50)
    print("创作者数据追踪器 - 项目初始化")
    print("=" * 50)
    print()

    # 1. 创建必要的目录
    log("[1/4] 创建目录结构...")
    create_directory(ROOT_DIR / "config", "config")
    create_directory(ROOT_DIR / "data", "data")
    create_directory(ROOT_DIR / "logs", "logs")
    print()

    # 2. 复制配置文件模板
    log("[2/4] 初始化配置文件...")
    copy_if_not_exists(
        ROOT_DIR / "config.example.json",
        ROOT_DIR / "config.json",
        "config.json"
    )
    copy_if_not_exists(
        ROOT_DIR / "config" / "ga_credentials.example.json",
        ROOT_DIR / "config" / "ga_credentials.json",
        "config/ga_credentials.json"
    )
    print()

    # 3. 复制数据文件模板
    log("[3/4] 初始化数据文件...")
    copy_if_not_exists(
        ROOT_DIR / "data" / "all_data.example.json",
        ROOT_DIR / "data" / "all_data.json",
        "data/all_data.json"
    )
    copy_if_not_exists(
        ROOT_DIR / "data" / "ga_data.example.json",
        ROOT_DIR / "data" / "ga_data.json",
        "data/ga_data.json"
    )
    print()

    # 4. 显示后续步骤
    log("[4/4] 初始化完成!", "SUCCESS")
    print()
    print("=" * 50)
    print("接下来请完成以下配置：")
    print("=" * 50)
    print()
    print("1. 编辑 config.json，填入各平台的 Cookie")
    print("   - 抖音：https://creator.douyin.com")
    print("   - 小红书：https://creator.xiaohongshu.com")
    print("   - 视频号：https://channels.weixin.qq.com")
    print()
    print("2. 配置 Google Analytics：")
    print("   - 编辑 config/ga_credentials.json")
    print("   - 填入 Google Cloud 服务账号密钥")
    print()
    print("3. 安装 Python 依赖：")
    print("   pip install -r requirements.txt")
    print("   playwright install chromium")
    print()
    print("4. 运行数据采集：")
    print("   python collect_all.py")
    print()
    print("详细说明请参考：docs/操作手册.md")
    print()


if __name__ == "__main__":
    main()
