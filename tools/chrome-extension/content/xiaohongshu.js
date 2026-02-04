// 小红书创作者中心数据采集
console.log('[Creator Collector] 小红书采集脚本已加载');

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
  userInfo: null,
  noteList: null
};

// 拦截 fetch 请求
const originalFetch = window.fetch;
window.fetch = async function(...args) {
  const response = await originalFetch.apply(this, args);

  try {
    const url = args[0];
    if (typeof url === 'string') {
      // 拦截用户信息 API
      if (url.includes('/api/galaxy/creator/home/personal_info')) {
        const clone = response.clone();
        const data = await clone.json();
        if (data.code === 0 && data.data) {
          interceptedData.userInfo = data.data;
          console.log('[Creator Collector] 拦截到用户信息');
        }
      }
      // 拦截笔记分析列表 API
      if (url.includes('/api/galaxy/creator/datacenter/note/analyze/list')) {
        const clone = response.clone();
        const data = await clone.json();
        if (data.code === 0 && data.data?.note_infos) {
          interceptedData.noteList = data.data.note_infos;
          console.log('[Creator Collector] 拦截到笔记列表:', data.data.note_infos.length, '条');
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
    platform: 'xiaohongshu',
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
  const nameEl = document.querySelector('[class*="username"], [class*="nickname"], .user-name');
  if (nameEl) account.account_name = nameEl.textContent.trim();

  // 从数据分析页面获取汇总数据
  const statCards = document.querySelectorAll('[class*="data-card"], [class*="stat-item"], [class*="overview"]');
  statCards.forEach(card => {
    const text = card.textContent;
    const numEl = card.querySelector('[class*="num"], [class*="value"], [class*="count"]');
    const num = numEl ? parseNumber(numEl.textContent) : 0;

    if (text.includes('粉丝')) account.followers = num;
    if (text.includes('曝光') || text.includes('展示')) account.total_impressions = num;
    if (text.includes('观看') || text.includes('阅读')) account.total_views = num;
    if (text.includes('点赞') || text.includes('获赞')) account.total_likes = num;
    if (text.includes('收藏')) account.total_collects = num;
  });

  return account;
}

// 从拦截的数据中提取
function collectFromIntercepted() {
  const result = {
    account: {
      platform: 'xiaohongshu',
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
    result.account.account_name = user.name || user.nickname || '';
    result.account.account_id = user.red_num || user.user_id || '';
    result.account.followers = user.fans_count || user.fans || 0;
    result.account.total_likes = user.faved_count || user.note_likes || 0;
    result.account.avatar_url = user.avatar || user.head_photo || '';
  }

  // 解析笔记列表
  if (interceptedData.noteList && interceptedData.noteList.length > 0) {
    let totalViews = 0;
    let totalImpressions = 0;
    let totalLikes = 0;
    let totalCollects = 0;
    let totalShares = 0;

    interceptedData.noteList.forEach(note => {
      const work = {
        work_id: note.id || '',
        platform: 'xiaohongshu',
        title: (note.title || '').slice(0, 50),
        publish_time: note.post_time ? new Date(note.post_time).toLocaleString() : '',
        views: note.read_count || 0,
        likes: note.like_count || 0,
        comments: note.comment_count || 0,
        shares: note.share_count || 0,
        collects: note.fav_count || 0,
        impressions: note.imp_count || 0,
        click_rate: note.coverClickRate || 0,
        avg_view_time: note.view_time_avg || 0,
        new_followers: note.increase_fans_count || 0
      };

      totalViews += work.views;
      totalImpressions += work.impressions;
      totalLikes += work.likes;
      totalCollects += work.collects;
      totalShares += work.shares;

      result.works.push(work);
    });

    result.account.total_views = totalViews;
    result.account.total_impressions = totalImpressions;
    result.account.total_likes = totalLikes || result.account.total_likes;
    result.account.total_collects = totalCollects;
    result.account.total_works = result.works.length;
  }

  return result;
}

// 主采集函数
async function collect() {
  console.log('[Creator Collector] 开始采集小红书数据...');

  // 优先使用拦截的数据
  let result = collectFromIntercepted();

  // 如果没有拦截到用户信息，从 DOM 补充
  if (!result.account.account_name) {
    const domAccount = collectFromDOM();
    result.account = { ...result.account, ...domAccount };
  }

  // 如果没有作品数据，提示用户
  if (result.works.length === 0) {
    console.log('[Creator Collector] 未拦截到笔记数据，请先访问数据分析页面');
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
          error: '未能获取到数据。请：\n1. 确保已登录小红书创作者中心\n2. 访问"数据分析"页面\n3. 等待页面加载完成后重试'
        });
      }
    }).catch(error => {
      sendResponse({ success: false, error: error.message });
    });
    return true;
  }
});
