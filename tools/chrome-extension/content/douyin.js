// 抖音创作者中心数据采集
console.log('[Creator Collector] 抖音采集脚本已加载');

// 解析数字（处理 "1.2w" 格式）
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

// 等待元素出现
function waitForElement(selector, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const el = document.querySelector(selector);
    if (el) return resolve(el);

    const observer = new MutationObserver(() => {
      const el = document.querySelector(selector);
      if (el) {
        observer.disconnect();
        resolve(el);
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });

    setTimeout(() => {
      observer.disconnect();
      reject(new Error('Element not found: ' + selector));
    }, timeout);
  });
}

// 采集账号信息（从页面 DOM）
function collectAccountFromDOM() {
  const account = {
    platform: 'douyin',
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

  // 尝试获取账号名称
  const nameEl = document.querySelector('.account-info .name') ||
                 document.querySelector('[class*="userName"]') ||
                 document.querySelector('[class*="nickname"]');
  if (nameEl) account.account_name = nameEl.textContent.trim();

  // 尝试获取粉丝数
  const statsEls = document.querySelectorAll('[class*="stat"]');
  statsEls.forEach(el => {
    const text = el.textContent;
    if (text.includes('粉丝')) {
      const num = el.querySelector('[class*="num"], [class*="value"]');
      if (num) account.followers = parseNumber(num.textContent);
    }
    if (text.includes('获赞')) {
      const num = el.querySelector('[class*="num"], [class*="value"]');
      if (num) account.total_likes = parseNumber(num.textContent);
    }
  });

  return account;
}

// 采集作品列表（从页面 DOM）
function collectWorksFromDOM() {
  const works = [];
  const workItems = document.querySelectorAll('[class*="video-card"], [class*="post-item"], [class*="aweme-item"]');

  workItems.forEach((item, index) => {
    try {
      const work = {
        work_id: String(index + 1),
        platform: 'douyin',
        title: '',
        publish_time: '',
        views: 0,
        likes: 0,
        comments: 0,
        shares: 0,
        collects: 0,
        impressions: 0
      };

      // 标题
      const titleEl = item.querySelector('[class*="title"], [class*="desc"]');
      if (titleEl) work.title = titleEl.textContent.trim().slice(0, 50);

      // 统计数据
      const statsText = item.textContent;
      const viewMatch = statsText.match(/(\d+(?:\.\d+)?[wWkK万千]?)\s*(?:播放|次播放)/);
      const likeMatch = statsText.match(/(\d+(?:\.\d+)?[wWkK万千]?)\s*(?:赞|点赞)/);
      const commentMatch = statsText.match(/(\d+(?:\.\d+)?[wWkK万千]?)\s*(?:评论)/);

      if (viewMatch) work.views = parseNumber(viewMatch[1]);
      if (likeMatch) work.likes = parseNumber(likeMatch[1]);
      if (commentMatch) work.comments = parseNumber(commentMatch[1]);

      if (work.title || work.views > 0) {
        works.push(work);
      }
    } catch (e) {
      console.error('[Creator Collector] 解析作品失败:', e);
    }
  });

  return works;
}

// 尝试从网络请求中拦截数据
let interceptedData = null;

// 拦截 fetch 请求
const originalFetch = window.fetch;
window.fetch = async function(...args) {
  const response = await originalFetch.apply(this, args);

  try {
    const url = args[0];
    if (typeof url === 'string') {
      // 拦截用户信息 API
      if (url.includes('/web/api/media/user/info')) {
        const clone = response.clone();
        const data = await clone.json();
        if (data.user) {
          interceptedData = interceptedData || {};
          interceptedData.userInfo = data.user;
        }
      }
      // 拦截作品列表 API
      if (url.includes('/web/api/media/aweme/post')) {
        const clone = response.clone();
        const data = await clone.json();
        if (data.aweme_list) {
          interceptedData = interceptedData || {};
          interceptedData.works = interceptedData.works || [];
          interceptedData.works = interceptedData.works.concat(data.aweme_list);
        }
      }
    }
  } catch (e) {
    // 忽略解析错误
  }

  return response;
};

// 从拦截的数据中提取信息
function collectFromIntercepted() {
  if (!interceptedData) return null;

  const result = {
    account: {
      platform: 'douyin',
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
  if (interceptedData.userInfo) {
    const user = interceptedData.userInfo;
    result.account.account_name = user.nickname || '';
    result.account.account_id = user.uid || user.sec_uid || '';
    result.account.followers = user.follower_count || user.mplatform_followers_count || 0;
    result.account.total_likes = user.total_favorited || 0;
    result.account.total_works = user.aweme_count || 0;
    if (user.avatar_medium?.url_list?.[0]) {
      result.account.avatar_url = user.avatar_medium.url_list[0];
    }
  }

  // 解析作品列表
  if (interceptedData.works) {
    let totalViews = 0;
    let totalShares = 0;
    let totalCollects = 0;

    interceptedData.works.forEach(item => {
      const stats = item.statistics || {};
      const work = {
        work_id: item.aweme_id || '',
        platform: 'douyin',
        title: (item.desc || '').slice(0, 50),
        publish_time: item.create_time ? new Date(item.create_time * 1000).toLocaleString() : '',
        views: stats.play_count || 0,
        likes: stats.digg_count || 0,
        comments: stats.comment_count || 0,
        shares: stats.share_count || 0,
        collects: stats.collect_count || 0,
        impressions: 0
      };

      totalViews += work.views;
      totalShares += work.shares;
      totalCollects += work.collects;
      result.works.push(work);
    });

    result.account.total_views = totalViews;
    result.account.total_collects = totalCollects;
    // 曝光量 = 播放 + 分享 + 点赞 + 收藏
    result.account.total_impressions = totalViews + totalShares + result.account.total_likes + totalCollects;
  }

  return result;
}

// 主采集函数
async function collect() {
  console.log('[Creator Collector] 开始采集抖音数据...');

  // 优先使用拦截的数据
  let result = collectFromIntercepted();

  // 如果没有拦截到数据，从 DOM 采集
  if (!result || !result.account.account_name) {
    console.log('[Creator Collector] 从页面 DOM 采集...');
    const account = collectAccountFromDOM();
    const works = collectWorksFromDOM();

    // 计算汇总
    let totalViews = 0, totalShares = 0, totalCollects = 0;
    works.forEach(w => {
      totalViews += w.views;
      totalShares += w.shares;
      totalCollects += w.collects;
    });

    account.total_views = totalViews;
    account.total_works = works.length;
    account.total_collects = totalCollects;
    account.total_impressions = totalViews + totalShares + account.total_likes + totalCollects;

    result = { account, works };
  }

  console.log('[Creator Collector] 采集完成:', result);
  return result;
}

// 监听来自 popup 的消息
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'collect') {
    collect().then(data => {
      if (data && data.account && data.account.account_name) {
        sendResponse({ success: true, data });
      } else {
        sendResponse({ success: false, error: '未能获取到有效数据，请确保已登录并在正确的页面' });
      }
    }).catch(error => {
      sendResponse({ success: false, error: error.message });
    });
    return true; // 保持消息通道开启
  }
});
