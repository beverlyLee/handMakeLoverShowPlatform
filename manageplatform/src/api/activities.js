import request from '@/utils/request'

export function getActivities(params) {
  return request({
    url: '/admin/activities/list',
    method: 'get',
    params
  })
}

export function getActivityDetail(id) {
  return request({
    url: `/admin/activities/${id}`,
    method: 'get'
  })
}

export function createActivity(data) {
  return request({
    url: '/activities',
    method: 'post',
    data
  })
}

export function updateActivity(id, data) {
  return request({
    url: `/admin/activities/${id}`,
    method: 'put',
    data
  })
}

export function deleteActivity(id) {
  return request({
    url: `/activities/${id}`,
    method: 'delete'
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

export function getActivityTypes() {
  return request({
    url: '/activities/types',
    method: 'get'
  })
}

export function getPendingReviewActivities(params) {
  return request({
    url: '/admin/activities/pending-review',
    method: 'get',
    params
  })
}

export function reviewActivity(id, data) {
  return request({
    url: `/admin/activities/${id}/review`,
    method: 'post',
    data
  })
}

export function createOfficialActivity(data) {
  return request({
    url: '/admin/activities/official-create',
    method: 'post',
    data
  })
}

export function adminEditActivity(id, data) {
  return request({
    url: `/admin/activities/${id}/admin-edit`,
    method: 'put',
    data
  })
}

export function adminDeleteActivity(id) {
  return request({
    url: `/admin/activities/${id}/admin-delete`,
    method: 'delete'
  })
}

export function getActivityDetailStats(id) {
  return request({
    url: `/admin/activities/${id}/stats`,
    method: 'get'
  })
}
