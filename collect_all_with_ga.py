#!/usr/bin/env python3
"""
运行所有数据采集任务：平台数据 + Google Analytics
"""
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).parent
GA_DATA_FILE = ROOT_DIR / "data" / "ga_data.json"


def log(message: str):
    """带时间戳的日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def get_ga_data_timestamp() -> str | None:
    """获取 GA 数据文件的更新时间"""
    if GA_DATA_FILE.exists():
        try:
            with open(GA_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("updated_at")
        except Exception:
            pass
    return None


def run_command(cmd: list, description: str, cwd=None) -> bool:
    """运行命令并返回是否成功"""
    log(f"执行: {description}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        if result.returncode != 0:
            log(f"❌ {description} 失败 (返回码: {result.returncode})")
            if result.stderr:
                log(f"   错误: {result.stderr[:500]}")
            return False
        log(f"✅ {description} 成功")
        return True
    except subprocess.TimeoutExpired:
        log(f"❌ {description} 超时")
        return False
    except Exception as e:
        log(f"❌ {description} 异常: {e}")
        return False


def main():
    python = sys.executable
    log("=" * 50)
    log("开始数据采集任务")
    log("=" * 50)

    # 1. 采集平台数据（抖音、小红书、视频号）
    log("")
    log("【步骤 1/3】采集平台数据...")
    platform_success = run_command(
        [python, str(ROOT_DIR / "collect_all.py")],
        "平台数据采集"
    )

    # 2. 采集 Google Analytics 数据
    log("")
    log("【步骤 2/3】采集 Google Analytics 数据...")

    # 记录采集前的时间戳
    old_timestamp = get_ga_data_timestamp()

    ga_success = run_command(
        [python, str(ROOT_DIR / "scripts" / "collect_ga.py")],
        "GA 数据采集"
    )

    # 验证 GA 数据是否真正更新
    new_timestamp = get_ga_data_timestamp()
    ga_data_updated = (
        ga_success and
        new_timestamp is not None and
        new_timestamp != old_timestamp
    )

    if ga_success and not ga_data_updated:
        log("⚠️  GA 采集脚本执行完成，但数据未更新")
        ga_success = False

    # 3. 推送 GA 数据到 GitHub（仅在 GA 数据成功更新时）
    log("")
    log("【步骤 3/3】推送数据到 GitHub...")

    if ga_data_updated:
        log("GA 数据已更新，准备推送...")

        # 添加文件
        add_success = run_command(
            ["git", "add", "data/ga_data.json", "data/tracker.db"],
            "Git add"
        )

        if add_success:
            # 检查是否有变更需要提交
            diff_result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=ROOT_DIR
            )

            if diff_result.returncode != 0:  # 有变更
                commit_success = run_command(
                    ["git", "commit", "-m", f"Auto update GA data ({new_timestamp})"],
                    "Git commit"
                )

                if commit_success:
                    run_command(["git", "push"], "Git push")
            else:
                log("没有新的变更需要提交")
    else:
        log("⚠️  GA 数据采集失败，跳过推送")

    # 输出摘要
    log("")
    log("=" * 50)
    log("采集任务完成")
    log("=" * 50)
    log(f"  平台数据: {'✅ 成功' if platform_success else '❌ 失败'}")
    log(f"  GA 数据:  {'✅ 成功' if ga_data_updated else '❌ 失败'}")

    if ga_data_updated:
        log(f"  GA 更新时间: {new_timestamp}")

    # 返回退出码
    if not platform_success or not ga_data_updated:
        sys.exit(1)


if __name__ == "__main__":
    main()
