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
 * @param {Object} params - { role } - 可选，角色过滤
 */
function getUnreadCount(params = {}) {
  return get('/messages/unread', params);
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

/**
 * 直接发送消息给指定用户（自动创建会话）
 * @param {number} targetUserId - 目标用户ID
 * @param {string} content - 消息内容
 * @param {Object} options - 可选参数 { message_type, related_id, related_type }
 */
function sendDirectChat(targetUserId, content, options = {}) {
  const data = {
    target_user_id: targetUserId,
    content: content,
    ...options
  };
  return post('/messages/chat/send', data);
}

/**
 * 获取与指定用户的会话
 * @param {number} targetUserId - 目标用户ID
 */
function getConversationWithUser(targetUserId) {
  return get(`/messages/conversation/with-user/${targetUserId}`);
}

/**
 * 获取与指定用户的消息记录
 * @param {number} targetUserId - 目标用户ID
 * @param {Object} params - { page, size }
 */
function getMessagesWithUser(targetUserId, params = {}) {
  return get(`/messages/conversation/with-user/${targetUserId}/messages`, params);
}

/**
 * 通过订单联系对方（创建会话或发送消息）
 * @param {string} orderId - 订单ID
 * @param {string} content - 消息内容（可选，不传则只创建会话）
 */
function contactThroughOrder(orderId, content = '') {
  const data = {};
  if (content) {
    data.content = content;
  }
  return post(`/messages/order/${orderId}/contact`, data);
}

/**
 * 删除会话
 * @param {number} conversationId - 会话ID
 */
function deleteConversation(conversationId) {
  return del(`/messages/conversations/${conversationId}`);
}

/**
 * 批量删除会话
 * @param {Array} conversationIds - 会话ID数组
 */
function batchDeleteConversations(conversationIds) {
  return del('/messages/conversations/batch-delete', { conversation_ids: conversationIds });
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
  createConversation,
  sendDirectChat,
  getConversationWithUser,
  getMessagesWithUser,
  contactThroughOrder,
  deleteConversation,
  batchDeleteConversations
};
