#!/usr/bin/env python3
"""
Native Messaging Host for Cookie Sync
Chrome 扩展通过 Native Messaging 调用此脚本同步 Cookie 到 config.json
"""

import json
import struct
import sys
import os
from datetime import datetime

# config.json 路径
CONFIG_PATH = os.path.expanduser("~/creator-data-tracker/config.json")
LOG_PATH = os.path.expanduser("~/creator-data-tracker/data/cookie_sync.log")

def log(message):
    """写入日志"""
    try:
        with open(LOG_PATH, "a") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except:
        pass

def read_message():
    """从 stdin 读取消息"""
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length:
        return None
    message_length = struct.unpack('=I', raw_length)[0]
    message = sys.stdin.buffer.read(message_length).decode('utf-8')
    return json.loads(message)

def send_message(message):
    """发送消息到 stdout"""
    encoded = json.dumps(message).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('=I', len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()

def update_cookie(platform, cookie):
    """更新 config.json 中的 cookie"""
    try:
        # 读取现有配置
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)

        # 更新 cookie
        if platform in config:
            old_cookie = config[platform].get('cookie', '')[:50]
            config[platform]['cookie'] = cookie

            # 写回文件
            with open(CONFIG_PATH, 'w') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            log(f"[{platform}] Cookie 已更新 (长度: {len(cookie)})")
            return True, f"Cookie 已更新"
        else:
            log(f"[{platform}] 平台不存在于配置中")
            return False, f"平台 {platform} 不存在"
    except Exception as e:
        log(f"[{platform}] 更新失败: {str(e)}")
        return False, str(e)

def main():
    log("Native Host 启动")

    while True:
        message = read_message()
        if message is None:
            break

        action = message.get('action')

        if action == 'sync_cookie':
            platform = message.get('platform')
            cookie = message.get('cookie')

            if platform and cookie:
                success, msg = update_cookie(platform, cookie)
                send_message({'success': success, 'message': msg})
            else:
                send_message({'success': False, 'message': '缺少 platform 或 cookie'})

        elif action == 'ping':
            send_message({'success': True, 'message': 'pong'})

        else:
            send_message({'success': False, 'message': f'未知 action: {action}'})

    log("Native Host 结束")

if __name__ == '__main__':
    main()
