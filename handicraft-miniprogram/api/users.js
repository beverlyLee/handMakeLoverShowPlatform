const { get, post, put, del } = require('../utils/request');

/**
 * 获取用户信息
 */
function getUserInfo() {
  return get('/users/profile');
}

/**
 * 更新用户信息
 * @param {Object} data
 */
function updateUserInfo(data) {
  return put('/users/profile', data);
}

/**
 * 获取用户角色信息
 */
function getUserRoles() {
  return get('/users/roles');
}

/**
 * 切换角色
 * @param {Object} data - { role: 'customer' | 'teacher' }
 */
function switchRole(data) {
  return put('/users/role', data);
}

/**
 * 验证手作老师身份
 * @param {Object} data
 */
function verifyTeacherIdentity(data) {
  return post('/users/teacher/verify', data);
}

/**
 * 申请成为手作老师（入驻）
 * @param {Object} data
 */
function applyTeacher(data) {
  return post('/users/teacher/apply', data);
}

/**
 * 获取手作老师信息
 */
function getTeacherInfo() {
  return get('/users/teacher/info');
}

/**
 * 获取地址列表
 */
function getAddressList() {
  return get('/users/address');
}

/**
 * 新增地址
 * @param {Object} data
 */
function createAddress(data) {
  return post('/users/address', data);
}

/**
 * 更新地址
 * @param {number} addressId
 * @param {Object} data
 */
function updateAddress(addressId, data) {
  return put(`/users/address/${addressId}`, data);
}

/**
 * 删除地址
 * @param {number} addressId
 */
function deleteAddress(addressId) {
  return del(`/users/address/${addressId}`);
}

/**
 * 设为默认地址
 * @param {number} addressId
 */
function setDefaultAddress(addressId) {
  return put(`/users/address/${addressId}/default`);
}

module.exports = {
  getUserInfo,
  updateUserInfo,
  getUserRoles,
  switchRole,
  verifyTeacherIdentity,
  applyTeacher,
  getTeacherInfo,
  getAddressList,
  createAddress,
  updateAddress,
  deleteAddress,
  setDefaultAddress
};
