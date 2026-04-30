import request from '@/utils/request'

export function getOrders(params) {
  return request({
    url: '/admin/orders/list',
    method: 'get',
    params
  })
}

export function getOrderDetail(id) {
  return request({
    url: `/admin/orders/${id}`,
    method: 'get'
  })
}

export function updateOrderStatus(id, data) {
  return request({
    url: `/admin/orders/${id}/status`,
    method: 'put',
    data
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

export function shipOrder(id, data) {
  return request({
    url: `/orders/${id}/ship`,
    method: 'post',
    data
  })
}

export function confirmOrder(id) {
  return request({
    url: `/orders/${id}/confirm`,
    method: 'post'
  })
}

export function cancelOrder(id, data) {
  return request({
    url: `/orders/${id}/cancel`,
    method: 'post',
    data
  })
}

export function deleteOrder(id) {
  return request({
    url: `/orders/${id}`,
    method: 'delete'
  })
}
