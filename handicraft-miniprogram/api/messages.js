const { get, put } = require('../utils/request');

/**
 * 获取消息列表
 * @param {Object} params - { page, size, type }
 */
function getMessages(params = {}) {
  return get('/messages', params);
}

/**
 * 获取消息详情
 * @param {number} messageId
 */
function getMessageDetail(messageId) {
  return get(`/messages/${messageId}`);
}

/**
 * 标记已读
 * @param {number} messageId
 */
function markAsRead(messageId) {
  return put(`/messages/${messageId}/read`);
}

/**
 * 获取未读数量
 */
function getUnreadCount() {
  return get('/messages/unread');
}

module.exports = {
  getMessages,
  getMessageDetail,
  markAsRead,
  getUnreadCount
};
