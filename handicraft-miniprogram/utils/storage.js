// 存储Key常量
const STORAGE_KEYS = {
  TOKEN: 'token',
  USER_INFO: 'userInfo',
  SEARCH_HISTORY: 'searchHistory'
};

/**
 * 设置存储
 * @param {string} key - 存储键
 * @param {any} value - 存储值
 */
function setStorage(key, value) {
  try {
    wx.setStorageSync(key, value);
    return true;
  } catch (e) {
    console.error('setStorage error:', e);
    return false;
  }
}

/**
 * 获取存储
 * @param {string} key - 存储键
 * @param {any} defaultValue - 默认值
 */
function getStorage(key, defaultValue = null) {
  try {
    const value = wx.getStorageSync(key);
    return value !== '' ? value : defaultValue;
  } catch (e) {
    console.error('getStorage error:', e);
    return defaultValue;
  }
}

/**
 * 移除存储
 * @param {string} key - 存储键
 */
function removeStorage(key) {
  try {
    wx.removeStorageSync(key);
    return true;
  } catch (e) {
    console.error('removeStorage error:', e);
    return false;
  }
}

/**
 * 清空所有存储
 */
function clearStorage() {
  try {
    wx.clearStorageSync();
    return true;
  } catch (e) {
    console.error('clearStorage error:', e);
    return false;
  }
}

// Token专用方法
function setToken(token) {
  return setStorage(STORAGE_KEYS.TOKEN, token);
}

function getToken() {
  return getStorage(STORAGE_KEYS.TOKEN, '');
}

function removeToken() {
  return removeStorage(STORAGE_KEYS.TOKEN);
}

// 用户信息专用方法
function setUserInfo(userInfo) {
  return setStorage(STORAGE_KEYS.USER_INFO, userInfo);
}

function getUserInfo() {
  return getStorage(STORAGE_KEYS.USER_INFO, null);
}

function removeUserInfo() {
  return removeStorage(STORAGE_KEYS.USER_INFO);
}

module.exports = {
  STORAGE_KEYS,
  setStorage,
  getStorage,
  removeStorage,
  clearStorage,
  setToken,
  getToken,
  removeToken,
  setUserInfo,
  getUserInfo,
  removeUserInfo
};
