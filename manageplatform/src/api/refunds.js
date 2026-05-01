import request from '@/utils/request'

export function getRefunds(params) {
  return request({
    url: '/admin/refunds/list',
    method: 'get',
    params
  })
}

export function getPendingRefunds(params) {
  return request({
    url: '/admin/refunds/pending',
    method: 'get',
    params
  })
}

export function getAbnormalRefunds(params) {
  return request({
    url: '/admin/refunds/abnormal',
    method: 'get',
    params
  })
}

export function auditRefund(id, data) {
  return request({
    url: `/admin/refunds/${id}/audit`,
    method: 'post',
    data
  })
}

export function forceHandleRefund(id, data) {
  return request({
    url: `/admin/refunds/${id}/force-handle`,
    method: 'post',
    data
  })
}

export function markAsAbnormal(id, data) {
  return request({
    url: `/admin/refunds/${id}/mark-abnormal`,
    method: 'post',
    data
  })
}

export function getRefundStats(params) {
  return request({
    url: '/admin/refunds/stats',
    method: 'get',
    params
  })
}

export function exportRefundStats(params) {
  return request({
    url: '/admin/refunds/stats/export',
    method: 'get',
    params
  })
}
