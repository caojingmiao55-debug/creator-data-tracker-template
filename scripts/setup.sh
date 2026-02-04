#!/bin/bash
#
# 创作者数据追踪系统 - 安装脚本
#

set -e

echo "========================================"
echo "创作者数据追踪系统 - 安装向导"
echo "========================================"
echo ""

# 项目目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# 检查 Python
echo "检查 Python..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装"
    exit 1
fi
echo "  Python: $(python3 --version)"

# 安装依赖
echo ""
echo "安装 Python 依赖..."
pip3 install -r requirements.txt -q
echo "  依赖安装完成"

# 创建配置文件
echo ""
if [ ! -f "config.json" ]; then
    echo "创建配置文件..."
    cp config.example.json config.json
    echo "  已创建 config.json"
    echo "  请编辑 config.json 填入各平台的 Cookie"
else
    echo "配置文件已存在"
fi

# 初始化 Git
echo ""
echo "初始化 Git 仓库..."
if [ ! -d ".git" ]; then
    git init -q
    git add .
    git commit -m "Initial commit" -q
    echo "  Git 仓库已初始化"
else
    echo "  Git 仓库已存在"
fi

# GitHub 设置
echo ""
echo "========================================"
echo "GitHub Pages 设置"
echo "========================================"
echo ""
echo "要将数据面板发布到 GitHub Pages，请执行以下步骤："
echo ""
echo "1. 登录 GitHub CLI（如果还没有）:"
echo "   gh auth login"
echo ""
echo "2. 创建 GitHub 仓库:"
echo "   gh repo create creator-data-tracker --public --source=. --push"
echo ""
echo "3. 启用 GitHub Pages:"
echo "   - 打开仓库设置 Settings -> Pages"
echo "   - Source 选择 'Deploy from a branch'"
echo "   - Branch 选择 'main' 和 '/ (root)'"
echo "   - 点击 Save"
echo ""
echo "4. 访问你的数据面板:"
echo "   https://你的用户名.github.io/creator-data-tracker/"
echo ""

# 定时任务设置
echo "========================================"
echo "定时任务设置（可选）"
echo "========================================"
echo ""
echo "要设置每天自动采集数据，请运行:"
echo "   python3 setup_cron.py"
echo ""

echo "========================================"
echo "安装完成!"
echo "========================================"
echo ""
echo "下一步操作:"
echo "1. 编辑 config.json 填入 Cookie"
echo "   运行 'python3 get_cookie.py' 获取 Cookie 引导"
echo ""
echo "2. 运行数据采集:"
echo "   python3 main.py"
echo ""
echo "3. 本地预览面板:"
echo "   open index.html"
echo ""
