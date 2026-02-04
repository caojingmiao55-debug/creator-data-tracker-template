#!/bin/bash
#
# Creator Data Collector - Native Messaging Host 安装脚本
#
# 用法:
#   ./setup_native_host.sh [extension_id]
#
# 参数:
#   extension_id: Chrome扩展ID（可选，安装后从chrome://extensions获取）
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NATIVE_HOST_DIR="${SCRIPT_DIR}/native_host"
MANIFEST_NAME="com.creator.datacollector.json"
HOST_SCRIPT="cookie_sync_host.py"

# Chrome Native Messaging目录
CHROME_NATIVE_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
CHROMIUM_NATIVE_DIR="$HOME/Library/Application Support/Chromium/NativeMessagingHosts"
EDGE_NATIVE_DIR="$HOME/Library/Application Support/Microsoft Edge/NativeMessagingHosts"

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Creator Data Collector${NC}"
echo -e "${GREEN}Native Messaging Host 安装脚本${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""

# 检查宿主脚本是否存在
if [ ! -f "${NATIVE_HOST_DIR}/${HOST_SCRIPT}" ]; then
    echo -e "${RED}错误: 找不到宿主脚本 ${HOST_SCRIPT}${NC}"
    exit 1
fi

# 获取扩展ID
EXTENSION_ID="${1:-YOUR_EXTENSION_ID_HERE}"
if [ "$EXTENSION_ID" = "YOUR_EXTENSION_ID_HERE" ]; then
    echo -e "${YELLOW}提示: 未指定扩展ID${NC}"
    echo ""
    echo "请按以下步骤获取扩展ID:"
    echo "1. 打开 Chrome 浏览器"
    echo "2. 访问 chrome://extensions"
    echo "3. 开启右上角的「开发者模式」"
    echo "4. 点击「加载已解压的扩展程序」"
    echo "5. 选择 ${SCRIPT_DIR}/chrome-extension 目录"
    echo "6. 找到扩展的ID（32位字母字符串）"
    echo ""
    read -p "请输入扩展ID（或按Enter跳过，稍后手动配置）: " EXTENSION_ID
    if [ -z "$EXTENSION_ID" ]; then
        EXTENSION_ID="YOUR_EXTENSION_ID_HERE"
        echo -e "${YELLOW}跳过扩展ID配置，稍后请手动编辑清单文件${NC}"
    fi
fi

# 确保宿主脚本可执行
echo "设置脚本执行权限..."
chmod +x "${NATIVE_HOST_DIR}/${HOST_SCRIPT}"

# 获取宿主脚本的绝对路径
HOST_PATH="$(cd "${NATIVE_HOST_DIR}" && pwd)/${HOST_SCRIPT}"

# 创建清单文件
echo "创建Native Messaging清单..."
cat > "${NATIVE_HOST_DIR}/${MANIFEST_NAME}" << EOF
{
  "name": "com.creator.datacollector",
  "description": "Creator Data Collector - Cookie Sync Host",
  "path": "${HOST_PATH}",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://${EXTENSION_ID}/"
  ]
}
EOF

echo -e "${GREEN}清单文件已创建${NC}"

# 安装到各浏览器
install_manifest() {
    local target_dir="$1"
    local browser_name="$2"

    if [ -d "$(dirname "$target_dir")" ]; then
        mkdir -p "$target_dir"
        cp "${NATIVE_HOST_DIR}/${MANIFEST_NAME}" "$target_dir/"
        echo -e "${GREEN}✓ 已安装到 ${browser_name}${NC}"
        return 0
    else
        echo -e "${YELLOW}✗ ${browser_name} 未安装，跳过${NC}"
        return 1
    fi
}

echo ""
echo "安装Native Messaging Host..."

# 安装到Chrome
install_manifest "$CHROME_NATIVE_DIR" "Google Chrome"

# 安装到Chromium
install_manifest "$CHROMIUM_NATIVE_DIR" "Chromium"

# 安装到Edge
install_manifest "$EDGE_NATIVE_DIR" "Microsoft Edge"

echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}安装完成！${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""

if [ "$EXTENSION_ID" = "YOUR_EXTENSION_ID_HERE" ]; then
    echo -e "${YELLOW}重要提示:${NC}"
    echo "请在获取扩展ID后，编辑以下文件中的 YOUR_EXTENSION_ID_HERE:"
    echo "  ${CHROME_NATIVE_DIR}/${MANIFEST_NAME}"
    echo ""
    echo "或重新运行此脚本并传入扩展ID:"
    echo "  ./setup_native_host.sh <extension_id>"
else
    echo "配置信息:"
    echo "  扩展ID: ${EXTENSION_ID}"
    echo "  宿主脚本: ${HOST_PATH}"
    echo ""
    echo "现在可以在扩展中使用Cookie自动同步功能了！"
fi

echo ""
echo "验证安装:"
echo "  1. 重启Chrome浏览器"
echo "  2. 打开扩展弹窗"
echo "  3. 点击「同步所有Cookie」"
echo "  4. 如果显示「已连接」表示Native Messaging配置成功"
