const { get, put, post, del } = require('../utils/request');

/**
 * 获取消息列表
 * @param {Object} params - { page, size, type }
 * type: system=系统通知, order=订单消息, activity=活动消息, chat=点对点消息
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
 * 批量标记已读
 * @param {Array} messageIds
 */
function batchMarkAsRead(messageIds) {
  return put('/messages/batch-read', { message_ids: messageIds });
}

/**
 * 删除消息
 * @param {number} messageId
 */
function deleteMessage(messageId) {
  return del(`/messages/${messageId}`);
}

/**
 * 批量删除消息
 * @param {Array} messageIds
 */
function batchDeleteMessages(messageIds) {
  return del('/messages/batch-delete', { message_ids: messageIds });
}

/**
 * 获取未读数量
 */
function getUnreadCount() {
  return get('/messages/unread');
}

/**
 * 获取会话列表（点对点聊天）
 * @param {Object} params - { page, size }
 */
function getConversations(params = {}) {
  return get('/messages/conversations', params);
}

/**
 * 获取会话详情（聊天记录）
 * @param {number} conversationId
 * @param {Object} params - { page, size }
 */
function getConversationMessages(conversationId, params = {}) {
  return get(`/messages/conversations/${conversationId}/messages`, params);
}

/**
 * 发送消息（点对点回复）
 * @param {number} conversationId
 * @param {string} content
 */
function sendMessage(conversationId, content) {
  return post(`/messages/conversations/${conversationId}/send`, { content });
}

/**
 * 创建新会话（发起聊天）
 * @param {number} targetUserId - 目标用户ID
 */
function createConversation(targetUserId) {
  return post('/messages/conversations', { target_user_id: targetUserId });
}

module.exports = {
  getMessages,
  getMessageDetail,
  markAsRead,
  batchMarkAsRead,
  deleteMessage,
  batchDeleteMessages,
  getUnreadCount,
  getConversations,
  getConversationMessages,
  sendMessage,
  createConversation
};
