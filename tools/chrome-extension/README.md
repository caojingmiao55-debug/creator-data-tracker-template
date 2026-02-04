# 创作者数据采集助手 Chrome 插件

一键采集多平台创作者数据，支持抖音、小红书、视频号，即将支持公众号、B站、Twitter。

## 安装方法

1. 打开 Chrome 浏览器，进入 `chrome://extensions/`
2. 开启右上角的 **开发者模式**
3. 点击 **加载已解压的扩展程序**
4. 选择 `chrome-extension` 文件夹

## 使用方法

### 方法一：点击采集按钮
1. 登录对应平台的创作者中心
2. 点击插件图标，打开弹窗
3. 点击 **采集当前页面** 按钮

### 方法二：直接跳转
1. 点击插件图标
2. 点击平台卡片，自动跳转到对应平台
3. 登录后点击采集按钮

## 支持的平台

| 平台 | 状态 | 采集页面 |
|------|------|----------|
| 抖音 | ✅ 已支持 | creator.douyin.com |
| 小红书 | ✅ 已支持 | creator.xiaohongshu.com/statistics/data-analysis |
| 视频号 | ✅ 已支持 | channels.weixin.qq.com/platform/post/list |
| 公众号 | 🚧 开发中 | mp.weixin.qq.com |
| B站 | 🚧 开发中 | member.bilibili.com |
| Twitter | 🚧 开发中 | x.com / analytics.twitter.com |

## 采集的数据

### 账号数据
- 账号名称、ID
- 粉丝数
- 总曝光量
- 总播放/观看量
- 总点赞数
- 总收藏数
- 作品数量

### 作品数据
- 作品标题
- 发布时间
- 曝光量（小红书）
- 播放/观看量
- 点赞、评论、分享、收藏数

## 数据导出

点击 **导出 JSON** 按钮，下载完整的 JSON 数据文件，可用于：
- 导入到数据面板
- 与 `all_data.json` 合并
- 数据分析和备份

## 技术原理

1. **API 拦截**：通过 fetch 拦截获取平台 API 返回的原始数据
2. **DOM 解析**：作为备选方案，从页面元素中提取数据
3. **本地存储**：使用 Chrome Storage API 保存采集的数据

## 注意事项

- 需要先登录对应平台
- 建议在数据分析/内容管理页面采集，数据更完整
- 数据保存在浏览器本地，清除浏览器数据会丢失
- 定期导出备份数据

## 目录结构

```
chrome-extension/
├── manifest.json       # 插件配置
├── popup.html          # 弹窗界面
├── popup.js            # 弹窗逻辑
├── background.js       # 后台服务
├── content/            # 内容脚本
│   ├── douyin.js       # 抖音采集
│   ├── xiaohongshu.js  # 小红书采集
│   ├── shipinhao.js    # 视频号采集
│   ├── weixin.js       # 公众号（开发中）
│   ├── bilibili.js     # B站（开发中）
│   └── twitter.js      # Twitter（开发中）
└── icons/              # 插件图标
```
