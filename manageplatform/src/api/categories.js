import request from '@/utils/request'

export function getCategories(params) {
  return request({
    url: '/admin/categories',
    method: 'get',
    params
  })
}

export function getAllCategories() {
  return request({
    url: '/admin/categories/all',
    method: 'get'
  })
}

export function getCategory(id) {
  return request({
    url: `/admin/categories/${id}`,
    method: 'get'
  })
}

export function createCategory(data) {
  return request({
    url: '/admin/categories',
    method: 'post',
    data
  })
}

export function updateCategory(id, data) {
  return request({
    url: `/admin/categories/${id}`,
    method: 'put',
    data
  })
}

export function deleteCategory(id) {
  return request({
    url: `/admin/categories/${id}`,
    method: 'delete'
  })
}
