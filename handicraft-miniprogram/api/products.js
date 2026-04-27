const { get, post, put, del } = require('../utils/request');

/**
 * 获取作品列表
 * @param {Object} params - { page, size, category, sort, keyword }
 */
function getProducts(params = {}) {
  return get('/products', params);
}

/**
 * 获取作品详情
 * @param {number} productId - 作品ID
 */
function getProductDetail(productId) {
  return get(`/products/${productId}`);
}

/**
 * 发布作品
 * @param {Object} data
 */
function createProduct(data) {
  return post('/products', data);
}

/**
 * 更新作品
 * @param {number} productId
 * @param {Object} data
 */
function updateProduct(productId, data) {
  return put(`/products/${productId}`, data);
}

/**
 * 删除作品
 * @param {number} productId
 */
function deleteProduct(productId) {
  return del(`/products/${productId}`);
}

/**
 * 获取作品分类
 */
function getCategories() {
  return get('/products/categories');
}

/**
 * 获取我的作品（老师端）
 * @param {Object} params
 */
function getMyProducts(params = {}) {
  return get('/products/my', params);
}

/**
 * 获取分类及其热门作品
 * @param {Object} params - { limit }
 */
function getCategoriesWithHotProducts(params = {}) {
  return get('/products/categories-with-hot', params);
}

module.exports = {
  getProducts,
  getProductDetail,
  createProduct,
  updateProduct,
  deleteProduct,
  getCategories,
  getMyProducts,
  getCategoriesWithHotProducts
};
