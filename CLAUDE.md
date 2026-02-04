# Creator Data Tracker - Claude Code 指南

这是一个多平台创作者数据采集与分析工具。当用户克隆此仓库后，请按以下步骤引导他们完成配置。

## ⚠️ 用户常见困难（请提前告知）

在开始配置前，**必须先告知用户以下重要信息**：

### 1. Cookie 是最大的痛点

| 问题 | 说明 |
|------|------|
| **什么是 Cookie** | 网站用来识别你登录状态的一串文字，相当于"临时通行证" |
| **为什么需要** | 采集脚本需要用你的 Cookie 来"假装"是你在访问创作者后台 |
| **会过期** | 抖音/小红书约 14 天，视频号仅 4 天左右 |
| **过期后果** | 采集失败，需要重新获取 Cookie |

**建议**：先只配置 1-2 个平台，跑通后再添加其他平台。

### 2. 获取 Cookie 的方法（需要手把手教）

很多用户不熟悉浏览器开发者工具，请详细说明：

```
1. 用 Chrome 浏览器打开创作者后台（如 creator.douyin.com）
2. 登录你的账号
3. 按 F12（Mac 按 Cmd+Option+I）打开开发者工具
4. 点击顶部的 "Network"（网络）标签
5. 按 F5 刷新页面
6. 在左侧列表中点击任意一个请求
7. 在右侧找到 "Request Headers"（请求标头）
8. 找到 "Cookie:" 开头的那一行
9. 复制 Cookie: 后面的全部内容（很长的一串）
```

**常见错误**：
- 复制了 "Cookie:" 这几个字（不要复制这个前缀）
- 只复制了部分内容（要复制完整，通常很长）
- 复制了 Response Headers 里的内容（要找 Request Headers）

### 3. 各平台后台地址

| 平台 | 创作者后台地址 | Cookie 有效期 |
|------|---------------|--------------|
| 抖音 | https://creator.douyin.com | ~14 天 |
| 小红书 | https://creator.xiaohongshu.com | ~14 天 |
| 视频号 | https://channels.weixin.qq.com | ~4 天（容易失效） |

### 4. 推荐配置顺序

```
1. 先配置抖音或小红书（最稳定）
2. 验证采集成功后再添加其他平台
3. 视频号建议最后配置（或暂时跳过）
4. GA 是可选的，不影响主功能
```

### 5. 网络环境要求

- Playwright 安装需要下载 Chromium 浏览器（约 150MB）
- 如果下载慢，可能需要配置镜像或代理
- 采集时需要能正常访问各平台网站

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

## 常见问题排查

### 问题：Playwright 安装失败

**症状**：`playwright install chromium` 下载很慢或失败

**解决**：
```bash
# 使用国内镜像
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
playwright install chromium
```

### 问题：采集时报 401 或重定向

**症状**：日志显示 `401 Unauthorized` 或跳转到登录页

**原因**：Cookie 已过期

**解决**：重新获取对应平台的 Cookie 并更新 config.json

### 问题：采集成功但数据为空

**症状**：没有报错，但 `all_data.json` 里数据都是 0

**可能原因**：
1. Cookie 格式不对（检查是否复制完整）
2. 账号没有创作者权限（需要是创作者账号）
3. 账号确实没有数据

### 问题：视频号一直失败

**现状**：视频号 Cookie 有效期极短（约 4 天），目前自动采集不稳定

**建议**：
1. 在 config.json 中设置 `"shipinhao": { "enabled": false }`
2. 或者手动截图数据，让 Claude 识别录入

### 问题：定时任务不执行

**macOS 检查**：
```bash
launchctl list | grep creator
# 如果没有输出，说明任务未加载
```

**重新加载**：
```bash
launchctl unload ~/Library/LaunchAgents/com.creator.tracker.plist
launchctl load ~/Library/LaunchAgents/com.creator.tracker.plist
```

### 问题：小红书需要 user_id

**获取方法**：
1. 打开小红书创作者中心
2. F12 打开开发者工具
3. 在 Cookie 中找到 `x-user-id-creator.xiaohongshu.com=xxx`
4. 复制 `xxx` 部分填入 config.json 的 user_id 字段

## 配置成功的标志

当你看到以下输出，说明配置成功：

```
[2026-02-04 10:00:00] 开始采集 douyin 数据...
[2026-02-04 10:00:05] ✅ douyin 采集完成: 粉丝 1234, 播放 56789
[2026-02-04 10:00:05] 数据已保存到 data/all_data.json
```

然后用浏览器打开 `index.html` 能看到数据图表，就说明全部配置成功了。
