import request from '@/utils/request'

export function getProducts(params) {
  return request({
    url: '/admin/products/list',
    method: 'get',
    params
  })
}

export function getProductDetail(id) {
  return request({
    url: `/admin/products/${id}`,
    method: 'get'
  })
}

export function createProduct(data) {
  return request({
    url: '/products',
    method: 'post',
    data
  })
}

export function updateProduct(id, data) {
  return request({
    url: `/admin/products/${id}`,
    method: 'put',
    data
  })
}

export function deleteProduct(id) {
  return request({
    url: `/products/${id}`,
    method: 'delete'
  })
}

export function getCategories() {
  return request({
    url: '/admin/categories/list',
    method: 'get'
  })
}

export function getProductStats(params) {
  return request({
    url: '/admin/products/stats',
    method: 'get',
    params
  })
}

export function exportProductStats(params) {
  return request({
    url: '/admin/products/stats/export',
    method: 'get',
    params
  })
}

export function getHotProducts(params) {
  return request({
    url: '/products/hot',
    method: 'get',
    params
  })
}

export function getNewProducts(params) {
  return request({
    url: '/products/new',
    method: 'get',
    params
  })
}

export function getPendingReviewProducts(params) {
  return request({
    url: '/admin/products/pending-review',
    method: 'get',
    params
  })
}

export function reviewProduct(id, data) {
  return request({
    url: `/admin/products/${id}/review`,
    method: 'post',
    data
  })
}

export function setProductOnline(id, is_online) {
  return request({
    url: `/admin/products/${id}/online`,
    method: 'post',
    data: { is_online }
  })
}

export function adminEditProduct(id, data) {
  return request({
    url: `/admin/products/${id}/admin-edit`,
    method: 'put',
    data
  })
}

export function adminDeleteProduct(id) {
  return request({
    url: `/admin/products/${id}/admin-delete`,
    method: 'delete'
  })
}
