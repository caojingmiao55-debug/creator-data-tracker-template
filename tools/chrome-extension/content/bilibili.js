// B站创作中心数据采集 - 开发中
console.log('[Creator Collector] B站采集脚本已加载 (开发中)');

// TODO: 实现B站数据采集
// 主要 API:
// - 个人信息: /x/space/myinfo
// - 视频列表: /x/space/arc/search
// - 数据统计: /x/creator/data/overview

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'collect') {
    sendResponse({
      success: false,
      error: 'B站采集功能开发中，敬请期待'
    });
    return true;
  }
});
