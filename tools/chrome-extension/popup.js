// 平台配置
const PLATFORMS = {
  douyin: { name: '抖音', ready: true },
  xiaohongshu: { name: '小红书', ready: true },
  shipinhao: { name: '视频号', ready: true }
};

// 格式化数字
function formatNumber(num) {
  if (num === undefined || num === null) return '0';
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w';
  return num.toLocaleString();
}

// 加载已保存的数据
async function loadSavedData() {
  const result = await chrome.storage.local.get(['creatorData']);
  return result.creatorData || {};
}

// 保存数据
async function saveData(data) {
  await chrome.storage.local.set({ creatorData: data });
}

// 更新平台状态显示
async function updatePlatformStatus() {
  const data = await loadSavedData();

  for (const [platform, config] of Object.entries(PLATFORMS)) {
    const statsEl = document.getElementById(`${platform}-stats`);
    const cardEl = document.querySelector(`[data-platform="${platform}"]`);

    if (!config.ready) {
      statsEl.textContent = '开发中';
      cardEl.classList.add('coming-soon');
      continue;
    }

    const platformData = data[platform];
    if (platformData && platformData.account) {
      const acc = platformData.account;
      statsEl.textContent = `${formatNumber(acc.followers)} 粉丝 · ${formatNumber(acc.total_views)} 播放`;
      statsEl.classList.add('has-data');
      cardEl.classList.add('ready');
    } else {
      statsEl.textContent = '未采集';
      statsEl.classList.remove('has-data');
      cardEl.classList.remove('ready');
    }
  }
}

// 采集当前页面数据
async function collectCurrentPage() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  if (!tab) {
    alert('无法获取当前标签页');
    return;
  }

  const url = tab.url;
  let platform = null;

  if (url.includes('creator.douyin.com')) platform = 'douyin';
  else if (url.includes('creator.xiaohongshu.com')) platform = 'xiaohongshu';
  else if (url.includes('channels.weixin.qq.com')) platform = 'shipinhao';
  else if (url.includes('mp.weixin.qq.com')) platform = 'weixin';
  else if (url.includes('member.bilibili.com')) platform = 'bilibili';
  else if (url.includes('x.com') || url.includes('twitter.com')) platform = 'twitter';

  if (!platform) {
    alert('当前页面不是支持的创作者平台');
    return;
  }

  if (!PLATFORMS[platform].ready) {
    alert(`${PLATFORMS[platform].name} 采集功能开发中，敬请期待`);
    return;
  }

  // 先尝试注入 content script
  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: [`content/${platform}.js`]
    });
  } catch (e) {
    // 可能已经注入过了，忽略错误
    console.log('Script injection:', e.message);
  }

  // 等待一下让脚本加载
  await new Promise(resolve => setTimeout(resolve, 500));

  // 发送消息给 content script
  try {
    const response = await chrome.tabs.sendMessage(tab.id, { action: 'collect' });

    if (response && response.success) {
      const data = await loadSavedData();
      data[platform] = response.data;
      data.updated_at = new Date().toISOString();
      await saveData(data);
      await updatePlatformStatus();
      alert(`${PLATFORMS[platform].name} 数据采集成功！`);
    } else {
      alert(`采集失败: ${response?.error || '未知错误'}`);
    }
  } catch (error) {
    alert(`采集失败: ${error.message}\n\n请刷新页面后重试。`);
  }
}

// 导出 JSON 数据
async function exportJSON() {
  const data = await loadSavedData();

  if (Object.keys(data).length === 0) {
    alert('暂无数据可导出');
    return;
  }

  // 转换为标准格式
  const exportData = {
    updated_at: data.updated_at || new Date().toISOString(),
    ...data
  };
  delete exportData.updated_at;
  exportData.updated_at = data.updated_at || new Date().toISOString();

  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = `creator_data_${new Date().toISOString().split('T')[0]}.json`;
  a.click();

  URL.revokeObjectURL(url);
}

// 预览数据
async function showPreview() {
  const data = await loadSavedData();
  const previewEl = document.getElementById('dataPreview');
  const contentEl = document.getElementById('previewContent');

  if (Object.keys(data).length === 0) {
    contentEl.innerHTML = '<div style="color: #666; text-align: center;">暂无数据</div>';
  } else {
    let html = '';

    for (const [platform, config] of Object.entries(PLATFORMS)) {
      if (!data[platform] || !data[platform].account) continue;

      const acc = data[platform].account;
      const worksCount = data[platform].works?.length || 0;

      html += `
        <div class="data-section">
          <div class="data-section-title">
            <span class="platform-icon ${platform}" style="width:16px;height:16px;font-size:9px;">
              ${platform === 'douyin' ? 'D' : platform === 'xiaohongshu' ? '小' : platform === 'shipinhao' ? '视' : platform === 'bilibili' ? 'B' : platform === 'weixin' ? '公' : 'X'}
            </span>
            ${config.name}
          </div>
          <div class="data-row"><span class="data-label">账号</span><span class="data-value">${acc.account_name}</span></div>
          <div class="data-row"><span class="data-label">粉丝</span><span class="data-value">${formatNumber(acc.followers)}</span></div>
          <div class="data-row"><span class="data-label">曝光</span><span class="data-value">${formatNumber(acc.total_impressions)}</span></div>
          <div class="data-row"><span class="data-label">播放</span><span class="data-value">${formatNumber(acc.total_views)}</span></div>
          <div class="data-row"><span class="data-label">点赞</span><span class="data-value">${formatNumber(acc.total_likes)}</span></div>
          <div class="data-row"><span class="data-label">作品</span><span class="data-value">${worksCount} 个</span></div>
        </div>
      `;
    }

    if (data.updated_at) {
      html += `<div style="color:#666;font-size:10px;text-align:center;margin-top:8px;">更新于 ${new Date(data.updated_at).toLocaleString()}</div>`;
    }

    contentEl.innerHTML = html || '<div style="color: #666; text-align: center;">暂无数据</div>';
  }

  previewEl.classList.toggle('show');
}

// 清空数据
async function clearData() {
  if (confirm('确定要清空所有已采集的数据吗？')) {
    await chrome.storage.local.remove(['creatorData']);
    await updatePlatformStatus();
    document.getElementById('dataPreview').classList.remove('show');
    alert('数据已清空');
  }
}

// ============== Cookie同步功能 ==============

// 更新同步状态显示
async function updateSyncStatus() {
  const response = await chrome.runtime.sendMessage({ action: 'getSyncStatus' });
  const statusEl = document.getElementById('syncStatus');
  const badgeEl = document.getElementById('syncBadge');

  if (!response.status || Object.keys(response.status).length === 0) {
    statusEl.innerHTML = '<div class="sync-hint">登录平台后自动同步Cookie到本地配置</div>';
    badgeEl.textContent = '未同步';
    badgeEl.className = 'sync-status-badge';
    return;
  }

  let html = '';
  let hasNativeSync = false;
  let hasPendingSync = false;

  for (const [platform, info] of Object.entries(response.status)) {
    const platformName = PLATFORMS[platform]?.name || platform;
    const time = new Date(info.lastSync).toLocaleString('zh-CN', {
      month: 'numeric',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric'
    });

    const syncType = info.nativeSync
      ? '<span class="sync-native">本地同步</span>'
      : '<span class="sync-storage">待导出</span>';

    if (info.nativeSync) hasNativeSync = true;
    else hasPendingSync = true;

    html += `
      <div class="sync-item">
        <span class="sync-platform">${platformName}</span>
        <span class="sync-time">${time} ${syncType}</span>
      </div>
    `;
  }

  statusEl.innerHTML = html;

  // 更新状态徽章
  if (hasNativeSync) {
    badgeEl.textContent = '已连接';
    badgeEl.className = 'sync-status-badge connected';
  } else if (hasPendingSync) {
    badgeEl.textContent = '待导出';
    badgeEl.className = 'sync-status-badge pending';
  }
}

// 同步所有Cookie
async function syncAllCookies() {
  const btn = document.getElementById('syncAllBtn');
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = '同步中...';

  try {
    const response = await chrome.runtime.sendMessage({ action: 'syncAllCookies' });

    const results = response.results || {};
    const successCount = Object.values(results).filter(r => r.success).length;
    const nativeCount = Object.values(results).filter(r => r.success && r.nativeSync).length;

    let message = `同步完成: ${successCount}/3 个平台`;
    if (nativeCount > 0) {
      message += `\n${nativeCount} 个已同步到本地配置`;
    }
    if (successCount > nativeCount) {
      message += `\n${successCount - nativeCount} 个已保存到扩展（需手动导出）`;
    }

    alert(message);
    await updateSyncStatus();
  } catch (error) {
    alert(`同步失败: ${error.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
  }
}

// 导出Cookie
async function exportCookies() {
  const platforms = ['douyin', 'xiaohongshu', 'shipinhao'];
  const cookies = {};

  for (const platform of platforms) {
    try {
      const response = await chrome.runtime.sendMessage({
        action: 'getCookieString',
        platform
      });

      if (response.success) {
        cookies[platform] = {
          enabled: true,
          cookie: response.cookie,
          cookie_updated_at: new Date().toISOString(),
          cookie_expires_hint: platform === 'shipinhao' ? 4 : 14
        };
      }
    } catch (e) {
      console.error(`获取${platform} Cookie失败:`, e);
    }
  }

  if (Object.keys(cookies).length === 0) {
    alert('未找到任何Cookie，请先登录各平台');
    return;
  }

  // 构建完整配置
  const config = {
    ...cookies,
    settings: {
      works_limit: 50,
      auto_push_to_github: false,
      notifications: {
        macos: true
      }
    }
  };

  const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `config_${new Date().toISOString().split('T')[0]}.json`;
  a.click();
  URL.revokeObjectURL(url);

  alert(`已导出 ${Object.keys(cookies).length} 个平台的Cookie\n请将文件重命名为 config.json 并放到项目目录`);
}

// ============== 初始化 ==============

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
  await updatePlatformStatus();
  await updateSyncStatus();

  // 平台卡片点击 - 跳转到对应平台
  document.querySelectorAll('.platform-card').forEach(card => {
    card.addEventListener('click', () => {
      const url = card.dataset.url;
      if (url) {
        chrome.tabs.create({ url });
      }
    });
  });

  // 按钮事件
  document.getElementById('collectBtn').addEventListener('click', collectCurrentPage);
  document.getElementById('exportBtn').addEventListener('click', exportJSON);
  document.getElementById('previewBtn').addEventListener('click', showPreview);
  document.getElementById('clearBtn').addEventListener('click', clearData);
  document.getElementById('closePreview').addEventListener('click', () => {
    document.getElementById('dataPreview').classList.remove('show');
  });

  // Cookie同步按钮事件
  document.getElementById('syncAllBtn').addEventListener('click', syncAllCookies);
  document.getElementById('exportCookieBtn').addEventListener('click', exportCookies);
});
