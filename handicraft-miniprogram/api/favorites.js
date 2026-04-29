const { get, post, del } = require('../utils/request');

/**
 * 获取收藏列表
 * @param {Object} params - { page, size }
 */
function getFavorites(params = {}) {
  return get('/favorites', params);
}

/**
 * 添加收藏
 * @param {Object} data - { product_id }
 */
function addFavorite(data) {
  return post('/favorites', data);
}

/**
 * 取消收藏
 * @param {number} productId
 */
function removeFavorite(productId) {
  return del(`/favorites/${productId}`);
}

/**
 * 点赞/取消点赞
 * @param {Object} data - { product_id }
 */
function toggleLike(data) {
  return post('/favorites/like', data);
}

/**
 * 检查点赞状态
 * @param {number} productId
 */
function checkLikeStatus(productId) {
  return get(`/favorites/like/${productId}`);
}

/**
 * 获取点赞数
 * @param {number} productId
 */
function getLikeCount(productId) {
  return get(`/favorites/like/count/${productId}`);
}

/**
 * 获取我的点赞列表
 * @param {Object} params - { page, size }
 */
function getMyLikes(params = {}) {
  return get('/favorites/like/my', params);
}

/**
 * 批量检查点赞状态
 * @param {Object} data - { product_ids: [] }
 */
function batchCheckLikeStatus(data) {
  return post('/favorites/like/batch-check', data);
}

module.exports = {
  getFavorites,
  addFavorite,
  removeFavorite,
  toggleLike,
  checkLikeStatus,
  getLikeCount,
  getMyLikes,
  batchCheckLikeStatus
};
