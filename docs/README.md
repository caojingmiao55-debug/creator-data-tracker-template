# 创作者数据追踪系统

自动采集抖音、小红书、视频号的创作者数据，生成可视化仪表盘。

## 在线访问

**仪表盘地址**：https://creator-data-tracker.vercel.app/

## 功能特性

- 支持三大平台：抖音、小红书、视频号
- 自动采集账号数据：粉丝数、播放量、点赞数、收藏数、曝光量
- 自动采集作品数据：播放量、点赞、评论、转发、收藏
- 数据可视化仪表盘，支持周期筛选（7天/30天/全部）
- 热门内容 TOP 5 排行
- 各平台数据对比图表
- 定时任务自动采集（每天 10:00）
- 自动部署到 Vercel

## 平台支持状态

| 平台 | 自动采集 | 说明 |
|------|----------|------|
| 抖音 | ✅ 支持 | 每天自动采集 |
| 小红书 | ✅ 支持 | 每天自动采集 |
| 视频号 | ⚠️ 待更新 | Cookie 频繁过期，目前通过截图方式更新 |

## 文档

- [使用文档](使用文档.md) - 团队成员使用指南
- [配置文档](配置文档.md) - 管理员配置指南（切换账号、更新 Cookie）

## 快速开始

### 1. 安装依赖

```bash
cd ~/creator-data-tracker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. 配置 Cookie

编辑 `config.json`，填入各平台的 Cookie（详见[配置文档](配置文档.md)）

### 3. 运行采集

```bash
python collect_all.py
```

### 4. 查看仪表盘

- 在线：https://creator-data-tracker.vercel.app/
- 本地：直接打开 `dashboard.html`

## 文件结构

```
creator-data-tracker/
├── collect_all.py       # 数据采集主脚本（Playwright）
├── config.json          # 配置文件（Cookie 等）
├── dashboard.html       # 数据可视化仪表盘
├── index.html           # 默认首页（同 dashboard）
├── assets/              # 平台 Logo 图片
│   ├── 抖音.png
│   ├── 小红书.png
│   └── 视频号.jpeg
├── data/
│   ├── all_data.json    # 所有数据存储
│   └── launchd.log      # 定时任务日志
├── docs/
│   ├── README.md        # 项目说明（本文件）
│   ├── 使用文档.md       # 使用指南
│   └── 配置文档.md       # 配置指南
└── com.creator.datacollector.plist  # macOS 定时任务配置
```

## 技术栈

- **数据采集**：Python + Playwright（浏览器自动化）
- **前端**：HTML + CSS + JavaScript + Chart.js
- **部署**：Vercel（自动部署）
- **定时任务**：macOS launchd

## 切换监测账号

只需更换 `config.json` 中对应平台的 Cookie 即可切换到其他账号，详见[配置文档](配置文档.md)。

## 常见问题

### Cookie 多久会过期？

| 平台 | 过期周期 | 建议 |
|------|----------|------|
| 抖音 | 约 1-2 周 | 每周检查一次 |
| 小红书 | 约 1-2 周 | 每周检查一次 |
| 视频号 | 数小时 | 暂用截图方式 |

### 数据采集失败？

1. 检查 Cookie 是否过期
2. 查看日志：`cat data/launchd.log`
3. 手动运行测试：`python collect_all.py`

---

*最后更新：2026-01-23*
