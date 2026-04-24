const { get } = require('../utils/request');

/**
 * 搜索作品
 * @param {Object} params - { keyword, page, size, category, sort }
 */
function searchProducts(params = {}) {
  return get('/search', params);
}

/**
 * 获取搜索历史
 */
function getSearchHistory() {
  return get('/search/history');
}

/**
 * 获取热门搜索
 */
function getHotSearch() {
  return get('/search/hot');
}

module.exports = {
  searchProducts,
  getSearchHistory,
  getHotSearch
};
