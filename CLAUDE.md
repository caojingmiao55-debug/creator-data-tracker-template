# Creator Data Tracker - Claude Code 指南

这是一个多平台创作者数据采集与分析工具。当用户克隆此仓库后，请按以下步骤引导他们完成配置。

## 项目概述

- **功能**：自动采集抖音、小红书、视频号、公众号的创作者数据，可选集成 Google Analytics
- **技术栈**：Python + Playwright + SQLite + Chart.js
- **部署方式**：本地运行采集脚本，数据仪表盘可部署到 Vercel/GitHub Pages

## 首次配置流程

当用户说"帮我配置这个项目"或类似请求时，按以下顺序执行：

### 第一步：环境检查

```bash
# 检查 Python 版本（需要 3.10+）
python3 --version

# 检查是否有虚拟环境
ls -la .venv 2>/dev/null || echo "需要创建虚拟环境"
```

### 第二步：创建虚拟环境并安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 第三步：初始化配置文件

```bash
python scripts/init_project.py
```

这会创建：
- `config.json` - 平台配置（需要用户填入 Cookie）
- `config/ga_credentials.json` - GA 凭证（可选）
- `data/all_data.json` - 数据文件
- `data/ga_data.json` - GA 数据文件

### 第四步：引导用户获取 Cookie

告诉用户：

1. **抖音**：打开 https://creator.douyin.com 并登录
2. **小红书**：打开 https://creator.xiaohongshu.com 并登录
3. **视频号**：打开 https://channels.weixin.qq.com 并登录

然后在浏览器中按 F12 → Network → 刷新页面 → 点击任意请求 → Headers → 复制 Cookie 值

### 第五步：更新配置

帮用户编辑 `config.json`，将获取的 Cookie 填入对应平台。

### 第六步：测试采集

```bash
source .venv/bin/activate
python collect_all.py
```

### 第七步：配置定时任务（可选）

macOS:
```bash
python scripts/setup_cron.py
```

## 常见任务

### 用户说"采集数据"
```bash
source .venv/bin/activate && python collect_all.py
```

### 用户说"查看数据"
```bash
python query_db.py --stats
```

### 用户说"Cookie 过期了"
引导用户重新获取对应平台的 Cookie，然后更新 `config.json`

### 用户说"配置 GA"
1. 需要 Google Cloud 服务账号
2. 编辑 `config/ga_credentials.json` 填入密钥
3. 在 `config.json` 中启用 GA 并填入属性 ID

### 用户说"部署仪表盘"
推荐 Vercel：
1. 将仓库推送到 GitHub
2. 在 vercel.com 导入仓库
3. 直接部署即可

## 关键文件说明

| 文件 | 用途 |
|------|------|
| `config.json` | 平台 Cookie 配置（敏感，不要提交到 Git） |
| `config/ga_credentials.json` | GA 服务账号密钥（敏感） |
| `collect_all.py` | 主采集脚本 |
| `collect_all_with_ga.py` | 包含 GA 的完整采集 |
| `index.html` | 数据仪表盘 |
| `data/tracker.db` | SQLite 数据库 |
| `data/all_data.json` | 前端数据文件 |

## 注意事项

1. **Cookie 有效期**：抖音/小红书约 14 天，视频号约 4 天
2. **敏感文件**：`config.json` 和凭证文件已在 `.gitignore` 中，不会被提交
3. **视频号**：Cookie 容易失效，建议先禁用（`"enabled": false`）
4. **错误排查**：查看 `logs/collect.log` 和 `logs/collect.error.log`

## 数据库查询示例

```bash
# 查看统计
python query_db.py --stats

# 最近 7 天数据
python query_db.py --days 7

# 指定平台
python query_db.py --platform douyin

# 作品列表
python query_db.py --works
```
