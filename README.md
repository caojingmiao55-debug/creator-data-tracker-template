# 创作者数据追踪器

多平台创作者数据采集与分析工具，支持抖音、小红书、视频号。

## 使用 Claude Code 快速配置

将本仓库链接发送给 [Claude Code](https://claude.ai/claude-code)，说：

> "帮我克隆并配置这个项目"

Claude 会自动引导你完成环境配置、Cookie 获取和首次数据采集。

## ⚠️ 开始前请阅读

### 这个项目适合谁？

✅ 需要追踪多平台创作者数据的运营人员
✅ 想要自动化采集数据、生成报表的创作者
✅ 有基本电脑操作能力，愿意花 30 分钟配置的用户

### 你需要知道的事

| 事项 | 说明 |
|------|------|
| **需要获取 Cookie** | 从浏览器开发者工具复制，不熟悉也没关系，文档有详细步骤 |
| **Cookie 会过期** | 抖音/小红书约 14 天，视频号约 4 天，过期需重新获取 |
| **需要 Python 环境** | 如果没有，Claude Code 可以帮你安装 |
| **首次配置约 30 分钟** | 主要时间花在获取各平台 Cookie |

### 推荐配置顺序

```
1. 先配置一个平台（推荐抖音或小红书，最稳定）
2. 跑通采集流程
3. 再逐步添加其他平台
4. 视频号和 GA 是可选的
```

## 功能特性

- **多平台支持**：抖音、小红书、视频号
- **自动化采集**：定时采集账号数据和作品数据
- **数据可视化**：仪表盘展示粉丝、播放、互动等核心指标
- **趋势分析**：支持 vs 昨天、7天前、30天前 对比
- **SQLite 存储**：高效本地存储，支持 SQL 查询
- **GA 集成**：可选接入 Google Analytics 网站数据

## 数据指标

| 指标 | 说明 |
|------|------|
| 粉丝 | 账号粉丝数 |
| 播放量 | 作品总播放 |
| 点赞 | 作品总点赞 |
| 评论 | 作品总评论 |
| 分享 | 作品总分享 |
| 收藏 | 作品总收藏 |
| 总互动 | 粉丝+播放+点赞+评论+分享+收藏 |

## 详细文档

**完整操作手册**：[docs/操作手册.md](docs/操作手册.md)

包含环境配置、Cookie 获取、定时任务、GA 集成、故障排查等详细说明。

## 快速开始

### 方式一：使用 Claude Code（推荐）

```
1. 克隆仓库到本地
2. 在 Claude Code 中打开项目目录
3. 告诉 Claude："帮我配置这个项目"
4. 按照 Claude 的引导完成配置
```

### 方式二：手动配置

#### 1. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
playwright install chromium
```

#### 2. 初始化配置

```bash
python scripts/init_project.py
```

#### 3. 配置 Cookie

编辑 `config.json`，填入各平台的 Cookie（从浏览器开发者工具获取）。

### 3. 运行采集

```bash
# 采集所有平台
python collect_all.py

# 采集指定平台
python collect_all.py --platform douyin
python collect_all.py --platform xiaohongshu
python collect_all.py --platform shipinhao
```

### 4. 查看数据

```bash
# 查看统计摘要
python query_db.py --stats

# 查看最近 N 天数据
python query_db.py --days 7

# 查看指定平台
python query_db.py --platform douyin

# 查看作品列表
python query_db.py --works
```

### 5. 打开仪表盘

用浏览器打开 `index.html` 查看可视化数据。

## 项目结构

```
creator-data-tracker/
├── collect_all.py          # 主采集脚本
├── query_db.py             # 数据库查询工具
├── index.html              # 数据仪表盘
├── config.json             # 配置文件（含 Cookie，不提交）
├── config.example.json     # 配置模板
├── requirements.txt        # Python 依赖
│
├── data/                   # 数据存储
│   ├── database.py         # SQLite 数据库模块
│   ├── tracker.db          # SQLite 数据库文件
│   └── all_data.json       # 前端数据（自动生成）
│
├── assets/                 # 平台图标
│
├── scripts/                # 工具脚本
│   ├── sync_cookie_from_browser.py  # Cookie 同步
│   ├── migrate_to_sqlite.py         # 数据迁移
│   ├── setup.sh                     # 环境安装
│   └── setup_cron.py                # 定时任务配置
│
├── tools/                  # 浏览器工具
│   ├── chrome-extension/   # Chrome 扩展
│   └── native_host/        # Native Host
│
├── docs/                   # 文档
└── logs/                   # 日志文件（不提交）
```

## 数据存储

### SQLite 数据库 (`data/tracker.db`)

**daily_accounts 表**：每日账号数据快照
```sql
SELECT date, platform, followers, total_views, total_likes
FROM daily_accounts
WHERE platform = 'douyin'
ORDER BY date DESC;
```

**works 表**：作品数据
```sql
SELECT title, views, likes, collects
FROM works
WHERE platform = 'xiaohongshu'
ORDER BY views DESC;
```

### 前端数据 (`data/all_data.json`)

采集完成后自动生成，供仪表盘使用。

## 定时采集

使用 crontab 设置定时任务：

```bash
# 每天早上 9 点采集
0 9 * * * cd /path/to/creator-data-tracker && python collect_all.py
```

## Google Analytics 集成（可选）

支持采集 Google Analytics 4 数据，包括：
- 实时用户、活跃用户、会话数、页面浏览量
- 流量来源、地理分布、设备分布
- 落地页、退出页分析
- 每日趋势图表

配置步骤见 [操作手册 - GA配置](docs/操作手册.md#三google-analytics-配置可选)

## 注意事项

1. **Cookie 有效期**：各平台 Cookie 会过期，视频号尤其容易失效
2. **登录弹窗**：视频号 Cookie 失效时会弹出浏览器窗口扫码登录
3. **数据安全**：`config.json` 和 `config/ga_credentials.json` 包含敏感信息，已加入 `.gitignore`

## License

MIT
