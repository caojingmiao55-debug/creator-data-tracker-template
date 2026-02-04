#!/usr/bin/env python3
"""
Chrome扩展Native Messaging宿主程序
接收扩展发送的Cookie并更新config.json
"""
import sys
import json
import struct
from datetime import datetime
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
CONFIG_FILE = ROOT_DIR / "config.json"
LOG_FILE = ROOT_DIR / "data" / "cookie_sync.log"


def log(message: str):
    """记录日志"""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass  # 日志写入失败不影响主流程


def read_message():
    """读取来自Chrome扩展的消息"""
    # 读取消息长度（4字节，小端序）
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length or len(raw_length) < 4:
        return None

    message_length = struct.unpack("I", raw_length)[0]

    # 读取消息内容
    message = sys.stdin.buffer.read(message_length).decode("utf-8")
    return json.loads(message)


def send_message(message: dict):
    """发送消息到Chrome扩展"""
    encoded = json.dumps(message).encode("utf-8")
    # 写入消息长度（4字节，小端序）
    sys.stdout.buffer.write(struct.pack("I", len(encoded)))
    # 写入消息内容
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def load_config() -> dict:
    """加载现有配置"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log(f"加载配置失败: {e}")
    return {}


def save_config(config: dict) -> bool:
    """保存配置"""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log(f"保存配置失败: {e}")
        return False


def update_cookie(platform: str, cookie: str, timestamp: str) -> bool:
    """更新config.json中的Cookie"""
    try:
        config = load_config()

        # 确保平台配置存在
        if platform not in config:
            config[platform] = {"enabled": True}

        # 更新Cookie相关字段
        config[platform]["cookie"] = cookie
        config[platform]["cookie_updated_at"] = timestamp
        config[platform]["cookie_source"] = "chrome_extension"

        # 设置默认过期提示
        expires_hint = {
            "douyin": 14,
            "xiaohongshu": 14,
            "shipinhao": 4  # 视频号有效期较短
        }
        config[platform]["cookie_expires_hint"] = expires_hint.get(platform, 7)

        # 保存配置
        if save_config(config):
            log(f"成功更新 {platform} 的Cookie，长度: {len(cookie)}")
            return True
        return False

    except Exception as e:
        log(f"更新 {platform} 的Cookie失败: {e}")
        return False


def handle_message(message: dict) -> dict:
    """处理接收到的消息"""
    action = message.get("action")

    if action == "updateCookie":
        platform = message.get("platform")
        cookie = message.get("cookie")
        timestamp = message.get("timestamp", datetime.now().isoformat())

        if not platform or not cookie:
            return {"success": False, "error": "缺少platform或cookie参数"}

        success = update_cookie(platform, cookie, timestamp)
        return {
            "success": success,
            "platform": platform,
            "timestamp": timestamp
        }

    elif action == "ping":
        return {"success": True, "message": "pong", "version": "2.0.0"}

    elif action == "getConfig":
        config = load_config()
        # 不返回完整cookie，只返回状态
        status = {}
        for platform in ["douyin", "xiaohongshu", "shipinhao"]:
            if platform in config:
                status[platform] = {
                    "enabled": config[platform].get("enabled", False),
                    "hasCookie": bool(config[platform].get("cookie")),
                    "updatedAt": config[platform].get("cookie_updated_at")
                }
        return {"success": True, "status": status}

    else:
        return {"success": False, "error": f"未知操作: {action}"}


def main():
    """主函数"""
    log("Native Messaging宿主程序启动")

    try:
        while True:
            message = read_message()
            if message is None:
                break

            log(f"收到消息: {message.get('action')}")
            response = handle_message(message)
            send_message(response)

    except Exception as e:
        log(f"程序异常: {e}")
    finally:
        log("Native Messaging宿主程序退出")


if __name__ == "__main__":
    main()
