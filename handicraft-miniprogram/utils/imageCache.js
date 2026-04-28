const config = require('./config');
const storage = require('./storage');

const CACHE_KEY_PREFIX = 'image_cache_';
const MAX_CACHE_SIZE = 50 * 1024 * 1024;

function getImageUuid(url) {
  if (!url) return null;
  
  const baseUrl = config.baseUrl;
  const apiUrl = baseUrl.endsWith('/api') ? baseUrl : baseUrl + '/api';
  
  if (url.startsWith('/api/images/')) {
    return url.substring('/api/images/'.length);
  }
  
  if (url.startsWith(apiUrl + '/images/')) {
    return url.substring((apiUrl + '/images/').length);
  }
  
  const fullBaseUrl = baseUrl.replace('/api', '');
  if (url.startsWith(fullBaseUrl + '/api/images/')) {
    return url.substring((fullBaseUrl + '/api/images/').length);
  }
  
  const uuidPattern = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/;
  const match = url.match(uuidPattern);
  if (match) {
    return match[0];
  }
  
  return null;
}

function getCacheKey(uuid) {
  return CACHE_KEY_PREFIX + uuid;
}

function getCachedImagePath(uuid) {
  if (!uuid) return null;
  
  const cacheKey = getCacheKey(uuid);
  const cachedData = storage.getStorage(cacheKey, null);
  
  if (cachedData && cachedData.path) {
    return cachedData.path;
  }
  
  return null;
}

function setCachedImagePath(uuid, path, size = 0) {
  if (!uuid || !path) return false;
  
  const cacheKey = getCacheKey(uuid);
  const cachedData = {
    path: path,
    size: size,
    timestamp: Date.now()
  };
  
  return storage.setStorage(cacheKey, cachedData);
}

function removeCachedImage(uuid) {
  if (!uuid) return false;
  
  const cacheKey = getCacheKey(uuid);
  return storage.removeStorage(cacheKey);
}

function downloadImage(url) {
  return new Promise((resolve, reject) => {
    if (!url) {
      reject(new Error('图片 URL 为空'));
      return;
    }
    
    wx.downloadFile({
      url: url,
      success: (res) => {
        if (res.statusCode === 200) {
          const tempFilePath = res.tempFilePath;
          
          wx.saveFile({
            tempFilePath: tempFilePath,
            success: (saveRes) => {
              resolve({
                success: true,
                path: saveRes.savedFilePath
              });
            },
            fail: (saveErr) => {
              console.error('保存图片失败:', saveErr);
              resolve({
                success: true,
                path: tempFilePath
              });
            }
          });
        } else {
          reject(new Error(`下载图片失败，状态码: ${res.statusCode}`));
        }
      },
      fail: (err) => {
        console.error('下载图片失败:', err);
        reject(err);
      }
    });
  });
}

async function getImageUrlWithCache(url, forceRefresh = false) {
  if (!url) return '';
  
  const uuid = getImageUuid(url);
  
  if (!uuid) {
    return url;
  }
  
  if (!forceRefresh) {
    const cachedPath = getCachedImagePath(uuid);
    if (cachedPath) {
      console.log(`使用缓存图片: ${uuid} -> ${cachedPath}`);
      return cachedPath;
    }
  }
  
  try {
    let fullUrl = url;
    if (url.startsWith('/api/images/')) {
      const fullBaseUrl = config.baseUrl.replace('/api', '');
      fullUrl = fullBaseUrl + url;
    }
    
    console.log(`下载图片: ${fullUrl}`);
    const result = await downloadImage(fullUrl);
    
    if (result.success) {
      setCachedImagePath(uuid, result.path);
      console.log(`缓存图片成功: ${uuid} -> ${result.path}`);
      return result.path;
    }
    
    return url;
  } catch (error) {
    console.error(`下载图片失败: ${url}`, error);
    return url;
  }
}

async function cacheImages(urls, forceRefresh = false) {
  if (!urls || !Array.isArray(urls) || urls.length === 0) {
    return [];
  }
  
  const results = [];
  for (const url of urls) {
    const cachedUrl = await getImageUrlWithCache(url, forceRefresh);
    results.push(cachedUrl);
  }
  
  return results;
}

async function updateImageCache(url) {
  if (!url) return '';
  
  const uuid = getImageUuid(url);
  if (uuid) {
    removeCachedImage(uuid);
  }
  
  return await getImageUrlWithCache(url, true);
}

function clearImageCache() {
  try {
    const info = wx.getStorageInfoSync();
    const keys = info.keys || [];
    
    for (const key of keys) {
      if (key.startsWith(CACHE_KEY_PREFIX)) {
        storage.removeStorage(key);
      }
    }
    
    console.log('图片缓存已清除');
    return true;
  } catch (error) {
    console.error('清除图片缓存失败:', error);
    return false;
  }
}

module.exports = {
  getImageUuid,
  getCachedImagePath,
  setCachedImagePath,
  removeCachedImage,
  downloadImage,
  getImageUrlWithCache,
  cacheImages,
  updateImageCache,
  clearImageCache
};
