import request from '@/utils/request'

export function getUserStats(params) {
  return request({
    url: '/admin/users/stats',
    method: 'get',
    params
  })
}

export function exportUserStats(params) {
  return request({
    url: '/admin/users/stats/export',
    method: 'get',
    params
  })
}

export function getTeacherStats(params) {
  return request({
    url: '/admin/teachers/stats',
    method: 'get',
    params
  })
}

export function exportTeacherStats(params) {
  return request({
    url: '/admin/teachers/stats/export',
    method: 'get',
    params
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

export function getOrderStats(params) {
  return request({
    url: '/admin/orders/stats',
    method: 'get',
    params
  })
}

export function exportOrderStats(params) {
  return request({
    url: '/admin/orders/stats/export',
    method: 'get',
    params
  })
}

export function getActivityStats(params) {
  return request({
    url: '/admin/activities/stats',
    method: 'get',
    params
  })
}

export function exportActivityStats(params) {
  return request({
    url: '/admin/activities/stats/export',
    method: 'get',
    params
  })
}
