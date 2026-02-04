// 视频号助手数据采集
console.log('[Creator Collector] 视频号采集脚本已加载');

// 解析数字
function parseNumber(str) {
  if (!str) return 0;
  str = String(str).trim().toLowerCase();
  if (str.includes('w') || str.includes('万')) {
    return Math.round(parseFloat(str) * 10000);
  }
  if (str.includes('k') || str.includes('千')) {
    return Math.round(parseFloat(str) * 1000);
  }
  return parseInt(str.replace(/[,，]/g, '')) || 0;
}

// 拦截的数据存储
let interceptedData = {
  authData: null,
  postList: null
};

// 拦截 fetch 请求
const originalFetch = window.fetch;
window.fetch = async function(...args) {
  const response = await originalFetch.apply(this, args);

  try {
    const url = args[0];
    if (typeof url === 'string') {
      // 拦截认证数据 API
      if (url.includes('/auth/auth_data')) {
        const clone = response.clone();
        const data = await clone.json();
        if (data.errCode === 0 && data.data) {
          interceptedData.authData = data.data;
          console.log('[Creator Collector] 拦截到用户信息');
        }
      }
      // 拦截作品列表 API
      if (url.includes('/post/post_list')) {
        const clone = response.clone();
        const data = await clone.json();
        if (data.errCode === 0 && data.data?.list) {
          interceptedData.postList = interceptedData.postList || [];
          interceptedData.postList = interceptedData.postList.concat(data.data.list);
          console.log('[Creator Collector] 拦截到作品列表:', data.data.list.length, '条');
        }
      }
    }
  } catch (e) {
    // 忽略解析错误
  }

  return response;
};

// 从页面 DOM 采集
function collectFromDOM() {
  const account = {
    platform: 'shipinhao',
    account_name: '',
    account_id: '',
    followers: 0,
    total_views: 0,
    total_likes: 0,
    total_works: 0,
    total_impressions: 0,
    total_collects: 0,
    avatar_url: ''
  };

  // 尝试获取账号名
  const nameEl = document.querySelector('[class*="nickname"], [class*="user-name"], .finder-nickname');
  if (nameEl) account.account_name = nameEl.textContent.trim();

  // 从页面获取统计数据
  const statItems = document.querySelectorAll('[class*="stat"], [class*="data-item"], [class*="overview"]');
  statItems.forEach(item => {
    const text = item.textContent;
    const numMatch = text.match(/(\d+(?:\.\d+)?[wWkK万千]?)/);
    const num = numMatch ? parseNumber(numMatch[1]) : 0;

    if (text.includes('粉丝') || text.includes('关注者')) account.followers = num;
    if (text.includes('播放') || text.includes('观看')) account.total_views = num;
    if (text.includes('点赞') || text.includes('喜欢')) account.total_likes = num;
  });

  return account;
}

// 从拦截的数据中提取
function collectFromIntercepted() {
  const result = {
    account: {
      platform: 'shipinhao',
      account_name: '',
      account_id: '',
      followers: 0,
      total_views: 0,
      total_likes: 0,
      total_works: 0,
      total_impressions: 0,
      total_collects: 0,
      avatar_url: ''
    },
    works: []
  };

  // 解析用户信息
  if (interceptedData.authData) {
    const user = interceptedData.authData.finderUser || {};
    result.account.account_name = user.nickname || '';
    result.account.account_id = user.uniqId || user.finderUsername || '';
    result.account.followers = user.fansCount || 0;
    result.account.total_works = user.feedsCount || 0;
    result.account.avatar_url = user.headImgUrl || user.headUrl || '';
  }

  // 解析作品列表
  if (interceptedData.postList && interceptedData.postList.length > 0) {
    let totalViews = 0;
    let totalLikes = 0;
    let totalShares = 0;
    let totalCollects = 0;

    interceptedData.postList.forEach(item => {
      // 处理标题
      let title = '';
      const desc = item.desc;
      if (typeof desc === 'string') {
        title = desc.slice(0, 50);
      } else if (typeof desc === 'object') {
        title = item.title || `视频 ${(item.objectId || '').slice(0, 8)}`;
      }

      const work = {
        work_id: item.objectId || '',
        platform: 'shipinhao',
        title: title,
        publish_time: item.createTime ? new Date(item.createTime * 1000).toLocaleString() : '',
        views: item.readCount || 0,
        likes: item.likeCount || 0,
        comments: item.commentCount || 0,
        shares: item.forwardCount || 0,
        collects: item.favCount || 0,
        impressions: 0
      };

      totalViews += work.views;
      totalLikes += work.likes;
      totalShares += work.shares;
      totalCollects += work.collects;

      result.works.push(work);
    });

    result.account.total_views = totalViews;
    result.account.total_likes = totalLikes;
    result.account.total_collects = totalCollects;
    result.account.total_works = result.works.length;
    // 曝光量 = 播放 + 分享 + 点赞 + 收藏
    result.account.total_impressions = totalViews + totalShares + totalLikes + totalCollects;
  }

  return result;
}

// 主采集函数
async function collect() {
  console.log('[Creator Collector] 开始采集视频号数据...');

  // 优先使用拦截的数据
  let result = collectFromIntercepted();

  // 如果没有拦截到用户信息，从 DOM 补充
  if (!result.account.account_name) {
    const domAccount = collectFromDOM();
    result.account = { ...result.account, ...domAccount };
  }

  console.log('[Creator Collector] 采集完成:', result);
  return result;
}

// 监听来自 popup 的消息
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'collect') {
    collect().then(data => {
      if (data && (data.account.account_name || data.works.length > 0)) {
        sendResponse({ success: true, data });
      } else {
        sendResponse({
          success: false,
          error: '未能获取到数据。请：\n1. 确保已登录视频号助手\n2. 访问"内容管理"页面\n3. 等待页面加载完成后重试'
        });
      }
    }).catch(error => {
      sendResponse({ success: false, error: error.message });
    });
    return true;
  }
});
