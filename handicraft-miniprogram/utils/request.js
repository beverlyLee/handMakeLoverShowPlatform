const config = require('./config');
const storage = require('./storage');
const { showToast } = require('./util');

/**
 * 发起网络请求
 * @param {Object} options - 请求配置
 * @param {string} options.url - 请求路径（不含baseUrl）
 * @param {string} options.method - 请求方法：GET/POST/PUT/DELETE
 * @param {Object} options.data - 请求数据
 * @param {Object} options.header - 自定义请求头
 * @param {boolean} options.showLoading - 是否显示加载中
 * @param {boolean} options.showError - 出错时是否显示toast
 * @returns {Promise} Promise对象
 */
function request(options) {
  const {
    url,
    method = 'GET',
    data = {},
    header = {},
    showLoading = false,
    showError = true
  } = options;

  // 显示加载中
  if (showLoading) {
    wx.showLoading({
      title: '加载中...',
      mask: true
    });
  }

  // 构建请求头
  const requestHeader = {
    'Content-Type': 'application/json',
    ...header
  };

  // 添加Token
  const token = storage.getToken();
  if (token) {
    requestHeader['Authorization'] = `Bearer ${token}`;
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: config.baseUrl + url,
      method: method.toUpperCase(),
      data: data,
      header: requestHeader,
      timeout: config.timeout,
      
      success: (res) => {
        if (showLoading) {
          wx.hideLoading();
        }

        const response = res.data;
        
        if (response && response.code !== undefined) {
          if (response.code === 0) {
            resolve(response.data);
          } else {
            if (showError) {
              showToast(response.msg || '请求失败');
            }
            
            if (response.code === 2002 || response.code === 2003) {
              storage.removeToken();
              storage.removeUserInfo();
            }
            
            reject(response);
          }
          return;
        }

        if (res.statusCode !== 200) {
          const errorMsg = `HTTP错误: ${res.statusCode}`;
          if (showError) {
            showToast(errorMsg);
          }
          reject({ code: res.statusCode, msg: errorMsg, data: null });
          return;
        }

        resolve(response);
      },
      
      fail: (err) => {
        if (showLoading) {
          wx.hideLoading();
        }
        
        const errorMsg = err.errMsg || '网络请求失败';
        if (showError) {
          showToast('网络错误，请稍后重试');
        }
        
        reject({ code: -1, msg: errorMsg, data: null });
      }
    });
  });
}

/**
 * GET请求
 * @param {string} url - 请求路径
 * @param {Object} data - 请求参数
 * @param {Object} options - 其他配置
 */
function get(url, data = {}, options = {}) {
  return request({
    url,
    method: 'GET',
    data,
    ...options
  });
}

/**
 * POST请求
 * @param {string} url - 请求路径
 * @param {Object} data - 请求参数
 * @param {Object} options - 其他配置
 */
function post(url, data = {}, options = {}) {
  return request({
    url,
    method: 'POST',
    data,
    ...options
  });
}

/**
 * PUT请求
 * @param {string} url - 请求路径
 * @param {Object} data - 请求参数
 * @param {Object} options - 其他配置
 */
function put(url, data = {}, options = {}) {
  return request({
    url,
    method: 'PUT',
    data,
    ...options
  });
}

/**
 * DELETE请求
 * @param {string} url - 请求路径
 * @param {Object} data - 请求参数
 * @param {Object} options - 其他配置
 */
function del(url, data = {}, options = {}) {
  return request({
    url,
    method: 'DELETE',
    data,
    ...options
  });
}

module.exports = {
  request,
  get,
  post,
  put,
  del
};
