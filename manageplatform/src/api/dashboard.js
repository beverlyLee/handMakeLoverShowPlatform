import request from '@/utils/request'

export function getDashboardStats() {
  return request({
    url: '/admin/stats',
    method: 'get'
  })
}

export function getOrderStats() {
  return request({
    url: '/admin/orders/stats',
    method: 'get'
  })
}

export function getUserStats() {
  return request({
    url: '/admin/users/stats',
    method: 'get'
  })
}

export function getProductStats() {
  return request({
    url: '/admin/products/stats',
    method: 'get'
  })
}

export function getRecentOrders() {
  return request({
    url: '/orders/',
    method: 'get',
    params: { page: 1, size: 10, role: 'customer' }
  })
}
