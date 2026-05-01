import request from '@/utils/request'

export function getMessages(params) {
  return request({
    url: '/admin/messages/list',
    method: 'get',
    params
  })
}

export function getMessageDetail(id) {
  return request({
    url: `/admin/messages/${id}`,
    method: 'get'
  })
}

export function createAnnouncement(data) {
  return request({
    url: '/admin/messages/announcements',
    method: 'post',
    data
  })
}

export function deleteMessage(id) {
  return request({
    url: `/admin/messages/${id}/delete`,
    method: 'post'
  })
}

export function batchDeleteMessages(data) {
  return request({
    url: '/admin/messages/batch-delete',
    method: 'post',
    data
  })
}

export function getMessageStats(params) {
  return request({
    url: '/admin/messages/stats',
    method: 'get',
    params
  })
}

export function exportMessageStats(params) {
  return request({
    url: '/admin/messages/stats/export',
    method: 'get',
    params
  })
}

export function getConversations(params) {
  return request({
    url: '/admin/messages/conversations',
    method: 'get',
    params
  })
}
