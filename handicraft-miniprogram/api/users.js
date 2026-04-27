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
 * 更新手作老师信息
 * @param {Object} data - 老师资料数据
 */
function updateTeacherInfo(data) {
  return put('/users/teacher/info', data);
}

/**
 * 获取地址列表
 */
function getAddressList() {
  return get('/users/address');
}

/**
 * 获取地址详情
 * @param {number} addressId
 */
function getAddressDetail(addressId) {
  return get(`/users/address/${addressId}`);
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

/**
 * 获取老师公开信息
 * @param {number} teacherId - 老师ID
 */
function getTeacherPublicInfo(teacherId) {
  return get(`/users/teacher/${teacherId}`);
}

/**
 * 获取老师公开订单统计
 * @param {number} teacherId - 老师ID
 */
function getTeacherPublicOrderStats(teacherId) {
  return get(`/users/teacher/${teacherId}/order-stats`);
}

module.exports = {
  getUserInfo,
  updateUserInfo,
  getUserRoles,
  switchRole,
  verifyTeacherIdentity,
  applyTeacher,
  getTeacherInfo,
  updateTeacherInfo,
  getTeacherPublicInfo,
  getTeacherPublicOrderStats,
  getAddressList,
  getAddressDetail,
  createAddress,
  updateAddress,
  deleteAddress,
  setDefaultAddress
};
