const { get, post, put, del } = require('../utils/request');

/**
 * 获取订单列表
 * @param {Object} params - { page, size, status }
 */
function getOrders(params = {}) {
  return get('/orders', params);
}

/**
 * 获取订单详情
 * @param {string} orderId - 订单ID
 */
function getOrderDetail(orderId) {
  return get(`/orders/${orderId}`);
}

/**
 * 创建订单
 * @param {Object} data - { product_id, quantity, address_id, remark }
 */
function createOrder(data) {
  return post('/orders', data);
}

/**
 * 取消订单
 * @param {string} orderId
 * @param {Object} data - { cancel_reason }
 */
function cancelOrder(orderId, data = {}) {
  return post(`/orders/${orderId}/cancel`, data);
}

/**
 * 支付订单
 * @param {string} orderId
 */
function payOrder(orderId) {
  return post(`/orders/${orderId}/pay`);
}

/**
 * 确认收货
 * @param {string} orderId
 */
function confirmOrder(orderId) {
  return post(`/orders/${orderId}/confirm`);
}

/**
 * 评价订单
 * @param {string} orderId
 * @param {Object} data - { rating, content, images }
 */
function reviewOrder(orderId, data) {
  return post(`/orders/${orderId}/review`, data);
}

/**
 * 更新订单状态（老师端）
 * @param {string} orderId
 * @param {Object} data - { status }
 */
function updateOrderStatus(orderId, data) {
  return put(`/orders/${orderId}/status`, data);
}

/**
 * 获取老师订单列表
 * @param {Object} params
 */
function getTeacherOrders(params = {}) {
  return get('/orders/teacher', params);
}

/**
 * 获取老师订单统计数据
 * @param {Object} params
 */
function getTeacherOrderStats(params = {}) {
  return get('/orders/teacher/stats', params);
}

/**
 * 删除订单
 * @param {string} orderId - 订单ID
 */
function deleteOrder(orderId) {
  return del(`/orders/${orderId}`);
}

/**
 * 接单（老师端）
 * @param {string} orderId - 订单ID
 */
function acceptOrder(orderId) {
  return post(`/orders/${orderId}/accept`);
}

/**
 * 拒单（老师端）
 * @param {string} orderId - 订单ID
 * @param {Object} data - { reject_reason }
 */
function rejectOrder(orderId, data) {
  return post(`/orders/${orderId}/reject`, data);
}

/**
 * 发货（老师端）
 * @param {string} orderId - 订单ID
 * @param {Object} data - { shipping_company, tracking_number, shipping_method, estimated_arrival_days }
 */
function shipOrder(orderId, data) {
  return post(`/orders/${orderId}/ship`, data);
}

/**
 * 获取订单物流信息
 * @param {string} orderId - 订单ID
 */
function getOrderLogistics(orderId) {
  return get(`/orders/${orderId}/logistics`);
}

module.exports = {
  getOrders,
  getOrderDetail,
  createOrder,
  cancelOrder,
  payOrder,
  confirmOrder,
  reviewOrder,
  updateOrderStatus,
  getTeacherOrders,
  getTeacherOrderStats,
  deleteOrder,
  acceptOrder,
  rejectOrder,
  shipOrder,
  getOrderLogistics
};
