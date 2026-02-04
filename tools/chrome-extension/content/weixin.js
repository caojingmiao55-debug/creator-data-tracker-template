// 微信公众号后台数据采集 - 开发中
console.log('[Creator Collector] 公众号采集脚本已加载 (开发中)');

// TODO: 实现公众号数据采集
// 主要 API:
// - 图文分析: /misc/appmsganalysis
// - 用户分析: /misc/useranalysis
// - 消息分析: /misc/msganalysis

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'collect') {
    sendResponse({
      success: false,
      error: '公众号采集功能开发中，敬请期待'
    });
    return true;
  }
});
