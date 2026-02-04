// 创作者数据采集助手 - 后台服务 v2.0
console.log('Creator Data Collector - Background Service v2.0 Started');

// ============== Cookie同步模块 ==============

// 平台域名映射
const PLATFORM_DOMAINS = {
  douyin: ['.douyin.com'],
  xiaohongshu: ['.xiaohongshu.com'],
  shipinhao: ['.weixin.qq.com', '.qq.com']
};

// 需要保留的关键Cookie名称
const IMPORTANT_COOKIES = {
  douyin: ['sessionid', 'sessionid_ss', 'passport_csrf_token', 'ttwid', 'msToken', 'sid_tt', 'uid_tt'],
  xiaohongshu: ['web_session', 'xsecappid', 'a1', 'webId', 'gid', 'customer-sso-sid'],
  shipinhao: ['wxuin', 'mmstat', 'pac_uid', 'uin', 'skey', 'pass_ticket']
};

// Native Messaging应用名称
const NATIVE_APP_NAME = 'com.creator.datacollector';

/**
 * 获取指定平台的所有Cookie
 */
async function getPlatformCookies(platform) {
  const domains = PLATFORM_DOMAINS[platform];
  if (!domains) return null;

  const allCookies = [];

  for (const domain of domains) {
    try {
      const cookies = await chrome.cookies.getAll({ domain });
      allCookies.push(...cookies);
    } catch (e) {
      console.error(`[Cookie Sync] 获取${platform}的Cookie失败:`, e);
    }
  }

  // 去重
  const uniqueCookies = Array.from(
    new Map(allCookies.map(c => [`${c.name}:${c.domain}`, c])).values()
  );

  return uniqueCookies;
}

/**
 * 将Cookie数组转换为字符串格式
 */
function cookiesToString(cookies) {
  return cookies.map(c => `${c.name}=${c.value}`).join('; ');
}

/**
 * 检查Cookie是否包含关键字段
 */
function hasImportantCookies(cookies, platform) {
  const important = IMPORTANT_COOKIES[platform] || [];
  if (important.length === 0) return true;

  const cookieNames = new Set(cookies.map(c => c.name));
  const matchCount = important.filter(name => cookieNames.has(name)).length;
  return matchCount >= Math.ceil(important.length / 3);
}

/**
 * 通过Native Messaging同步Cookie到本地
 */
async function syncCookieViaNativeMessaging(platform, cookieString) {
  try {
    const response = await chrome.runtime.sendNativeMessage(
      NATIVE_APP_NAME,
      {
        action: 'updateCookie',
        platform: platform,
        cookie: cookieString,
        timestamp: new Date().toISOString()
      }
    );

    if (response && response.success) {
      console.log(`[Cookie Sync] ${platform} Cookie已通过Native Messaging同步`);
      return true;
    }
    return false;
  } catch (e) {
    console.log(`[Cookie Sync] Native Messaging未配置或连接失败:`, e.message);
    return false;
  }
}

/**
 * 保存Cookie到扩展存储（备选方案）
 */
async function saveCookieToStorage(platform, cookieString) {
  const key = `pending_cookie_${platform}`;
  await chrome.storage.local.set({
    [key]: {
      cookie: cookieString,
      timestamp: new Date().toISOString()
    }
  });
  console.log(`[Cookie Sync] ${platform} Cookie已保存到扩展存储`);
}

/**
 * 同步Cookie到本地
 */
async function syncCookieToLocal(platform, cookieString) {
  const nativeSuccess = await syncCookieViaNativeMessaging(platform, cookieString);

  if (!nativeSuccess) {
    await saveCookieToStorage(platform, cookieString);
  }

  // 更新同步状态
  const data = await chrome.storage.local.get(['syncedCookies']);
  const synced = data.syncedCookies || {};
  synced[platform] = {
    lastSync: new Date().toISOString(),
    nativeSync: nativeSuccess,
    cookieLength: cookieString.length
  };
  await chrome.storage.local.set({ syncedCookies: synced });

  return { success: true, nativeSync: nativeSuccess };
}

/**
 * 手动触发Cookie同步
 */
async function manualSync(platform) {
  console.log(`[Cookie Sync] 开始手动同步 ${platform} Cookie...`);

  const cookies = await getPlatformCookies(platform);

  if (!cookies || cookies.length === 0) {
    return { success: false, error: '未找到Cookie，请确保已登录' };
  }

  if (!hasImportantCookies(cookies, platform)) {
    return { success: false, error: 'Cookie不完整，请重新登录' };
  }

  const cookieString = cookiesToString(cookies);
  const result = await syncCookieToLocal(platform, cookieString);

  return {
    success: true,
    nativeSync: result.nativeSync,
    cookieCount: cookies.length,
    timestamp: new Date().toISOString()
  };
}

/**
 * 启动Cookie变化监听
 */
function startCookieWatcher() {
  if (!chrome.cookies || !chrome.cookies.onChanged) {
    console.warn('[Cookie Sync] Cookie API不可用');
    return;
  }

  chrome.cookies.onChanged.addListener(async (changeInfo) => {
    const { cookie, removed } = changeInfo;

    if (removed) return;

    // 判断属于哪个平台
    let platform = null;
    for (const [p, domains] of Object.entries(PLATFORM_DOMAINS)) {
      if (domains.some(d => cookie.domain.includes(d.replace('.', '')))) {
        platform = p;
        break;
      }
    }

    if (!platform) return;

    // 检查是否是关键Cookie
    const important = IMPORTANT_COOKIES[platform] || [];
    if (!important.includes(cookie.name)) return;

    console.log(`[Cookie Sync] 检测到${platform}关键Cookie更新: ${cookie.name}`);

    // 获取完整Cookie并同步
    const allCookies = await getPlatformCookies(platform);
    if (allCookies && hasImportantCookies(allCookies, platform)) {
      const cookieString = cookiesToString(allCookies);
      await syncCookieToLocal(platform, cookieString);
    }
  });

  console.log('[Cookie Sync] Cookie监听器已启动');
}

// 启动Cookie监听
startCookieWatcher();

// ============== 消息处理 ==============

// 监听来自 content script 和 popup 的消息
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // 原有的保存数据逻辑
  if (message.action === 'saveData') {
    chrome.storage.local.get(['creatorData'], (result) => {
      const data = result.creatorData || {};
      data[message.platform] = message.data;
      data.updated_at = new Date().toISOString();

      chrome.storage.local.set({ creatorData: data }, () => {
        sendResponse({ success: true });
      });
    });
    return true;
  }

  if (message.action === 'getData') {
    chrome.storage.local.get(['creatorData'], (result) => {
      sendResponse({ data: result.creatorData || {} });
    });
    return true;
  }

  // Cookie同步相关消息

  // 手动同步单个平台Cookie
  if (message.action === 'syncCookie') {
    manualSync(message.platform).then(result => {
      sendResponse(result);
    });
    return true;
  }

  // 同步所有平台Cookie
  if (message.action === 'syncAllCookies') {
    (async () => {
      const results = {};
      const platforms = Object.keys(PLATFORM_DOMAINS);

      for (const platform of platforms) {
        results[platform] = await manualSync(platform);
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      sendResponse({ results });
    })();
    return true;
  }

  // 获取Cookie字符串
  if (message.action === 'getCookieString') {
    getPlatformCookies(message.platform).then(cookies => {
      if (cookies && cookies.length > 0) {
        sendResponse({
          success: true,
          cookie: cookiesToString(cookies),
          count: cookies.length
        });
      } else {
        sendResponse({ success: false, error: '获取Cookie失败' });
      }
    });
    return true;
  }

  // 获取同步状态
  if (message.action === 'getSyncStatus') {
    chrome.storage.local.get(['syncedCookies'], (result) => {
      sendResponse({ status: result.syncedCookies || {} });
    });
    return true;
  }

  // 获取待导出的Cookie
  if (message.action === 'getPendingCookies') {
    chrome.storage.local.get(null, (data) => {
      const pending = {};
      for (const [key, value] of Object.entries(data)) {
        if (key.startsWith('pending_cookie_')) {
          const platform = key.replace('pending_cookie_', '');
          pending[platform] = value;
        }
      }
      sendResponse({ pending });
    });
    return true;
  }
});

// 安装时初始化
chrome.runtime.onInstalled.addListener(() => {
  console.log('Creator Data Collector v2.0 installed successfully!');

  // 首次安装时尝试同步现有Cookie
  ['douyin', 'xiaohongshu', 'shipinhao'].forEach(async (platform) => {
    const result = await manualSync(platform);
    if (result.success) {
      console.log(`[初始化] ${platform} Cookie已自动同步`);
    }
  });
});
