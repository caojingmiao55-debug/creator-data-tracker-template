#!/bin/bash
# 安装 Cookie 同步功能的 Native Messaging Host

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOST_NAME="com.creator.cookiesync"
HOST_PATH="$SCRIPT_DIR/native-host"
PYTHON_SCRIPT="$HOST_PATH/cookie_sync.py"
MANIFEST_FILE="$HOST_PATH/$HOST_NAME.json"

# Chrome Native Messaging Hosts 目录
CHROME_HOSTS_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"

echo "=== Cookie 同步功能安装 ==="
echo ""

# 1. 确保 Python 脚本可执行
chmod +x "$PYTHON_SCRIPT"
echo "[1/4] 已设置脚本执行权限"

# 2. 获取扩展 ID
echo ""
echo "[2/4] 获取扩展 ID..."
echo ""
echo "请按以下步骤操作："
echo "1. 打开 Chrome，进入 chrome://extensions/"
echo "2. 找到「创作者数据采集助手」扩展"
echo "3. 复制扩展 ID（类似：abcdefghijklmnopqrstuvwxyz123456）"
echo ""
read -p "请粘贴扩展 ID: " EXTENSION_ID

if [ -z "$EXTENSION_ID" ]; then
    echo "错误：扩展 ID 不能为空"
    exit 1
fi

# 3. 更新 manifest 文件
echo ""
echo "[3/4] 配置 Native Messaging Host..."

cat > "$MANIFEST_FILE" << EOF
{
  "name": "$HOST_NAME",
  "description": "Cookie Sync for Creator Data Tracker",
  "path": "$PYTHON_SCRIPT",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://$EXTENSION_ID/"
  ]
}
EOF

# 4. 安装到 Chrome
echo "[4/4] 安装 Native Messaging Host..."

mkdir -p "$CHROME_HOSTS_DIR"
cp "$MANIFEST_FILE" "$CHROME_HOSTS_DIR/"

echo ""
echo "=== 安装完成 ==="
echo ""
echo "配置信息："
echo "  扩展 ID: $EXTENSION_ID"
echo "  Host 名称: $HOST_NAME"
echo "  Host 路径: $PYTHON_SCRIPT"
echo "  Manifest: $CHROME_HOSTS_DIR/$HOST_NAME.json"
echo ""
echo "接下来请："
echo "1. 重新加载 Chrome 扩展（chrome://extensions/ → 点击刷新按钮）"
echo "2. 访问抖音/小红书创作者中心，Cookie 会自动同步"
echo ""
