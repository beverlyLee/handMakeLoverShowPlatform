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

module.exports = {
  getFavorites,
  addFavorite,
  removeFavorite
};
