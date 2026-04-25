const { get, post, put } = require('../utils/request');

/**
 * 微信登录
 * @param {Object} data - { code, nickname, avatar }
 */
function login(data) {
  return post('/auth/login', data);
}

/**
 * 用户注册
 * @param {Object} data
 */
function register(data) {
  return post('/auth/register', data);
}

/**
 * 登出
 */
function logout() {
  return post('/auth/logout');
}

/**
 * 获取当前用户信息
 */
function getProfile() {
  return get('/auth/profile');
}

/**
 * 更新用户信息
 * @param {Object} data
 */
function updateProfile(data) {
  return put('/auth/profile', data);
}

module.exports = {
  login,
  register,
  logout,
  getProfile,
  updateProfile
};
