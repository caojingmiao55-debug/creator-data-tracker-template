/**
 * Cookie同步模块
 * 负责从浏览器获取Cookie并同步到本地
 */

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
 * @param {string} platform - 平台名称
 * @returns {Promise<Array>} Cookie数组
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

  // 去重（基于name和domain）
  const uniqueCookies = Array.from(
    new Map(allCookies.map(c => [`${c.name}:${c.domain}`, c])).values()
  );

  return uniqueCookies;
}

/**
 * 将Cookie数组转换为字符串格式
 * @param {Array} cookies - Cookie数组
 * @returns {string} Cookie字符串
 */
function cookiesToString(cookies) {
  return cookies
    .map(c => `${c.name}=${c.value}`)
    .join('; ');
}

/**
 * 检查Cookie是否包含关键字段
 * @param {Array} cookies - Cookie数组
 * @param {string} platform - 平台名称
 * @returns {boolean} 是否包含足够的关键Cookie
 */
function hasImportantCookies(cookies, platform) {
  const important = IMPORTANT_COOKIES[platform] || [];
  if (important.length === 0) return true;

  const cookieNames = new Set(cookies.map(c => c.name));

  // 至少包含一半的关键Cookie
  const matchCount = important.filter(name => cookieNames.has(name)).length;
  return matchCount >= Math.ceil(important.length / 3); // 降低阈值，因为不同账号可能有不同的cookie
}

/**
 * 通过Native Messaging同步Cookie到本地
 * @param {string} platform - 平台名称
 * @param {string} cookieString - Cookie字符串
 * @returns {Promise<boolean>} 是否同步成功
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
    } else {
      console.error(`[Cookie Sync] Native Messaging同步失败:`, response?.error);
      return false;
    }
  } catch (e) {
    console.error(`[Cookie Sync] Native Messaging连接失败:`, e.message);
    return false;
  }
}

/**
 * 保存Cookie到扩展存储（备选方案）
 * @param {string} platform - 平台名称
 * @param {string} cookieString - Cookie字符串
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
 * @param {string} platform - 平台名称
 * @param {string} cookieString - Cookie字符串
 * @returns {Promise<Object>} 同步结果
 */
async function syncCookieToLocal(platform, cookieString) {
  // 先尝试Native Messaging
  const nativeSuccess = await syncCookieViaNativeMessaging(platform, cookieString);

  if (!nativeSuccess) {
    // 备选方案：保存到扩展存储
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

  return {
    success: true,
    nativeSync: nativeSuccess,
    timestamp: new Date().toISOString()
  };
}

/**
 * 手动触发Cookie同步
 * @param {string} platform - 平台名称
 * @returns {Promise<Object>} 同步结果
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
    timestamp: result.timestamp
  };
}

/**
 * 批量同步所有平台Cookie
 * @returns {Promise<Object>} 各平台同步结果
 */
async function syncAllPlatforms() {
  const results = {};
  const platforms = Object.keys(PLATFORM_DOMAINS);

  for (const platform of platforms) {
    results[platform] = await manualSync(platform);
    // 添加短暂延迟避免请求过快
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  return results;
}

/**
 * 获取待导出的Cookie（从扩展存储）
 * @returns {Promise<Object>} 各平台的Cookie
 */
async function getPendingCookies() {
  const data = await chrome.storage.local.get(null);
  const pending = {};

  for (const [key, value] of Object.entries(data)) {
    if (key.startsWith('pending_cookie_')) {
      const platform = key.replace('pending_cookie_', '');
      pending[platform] = value;
    }
  }

  return pending;
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

    if (removed) return; // 只关注新增/更新的Cookie

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

/**
 * 获取同步状态
 * @returns {Promise<Object>} 同步状态
 */
async function getSyncStatus() {
  const data = await chrome.storage.local.get(['syncedCookies']);
  return data.syncedCookies || {};
}

// 导出函数供background.js使用
if (typeof globalThis !== 'undefined') {
  globalThis.CookieSync = {
    startCookieWatcher,
    manualSync,
    syncAllPlatforms,
    getPlatformCookies,
    cookiesToString,
    getSyncStatus,
    getPendingCookies
  };
}
