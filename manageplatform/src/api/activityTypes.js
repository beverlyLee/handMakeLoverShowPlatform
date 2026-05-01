import request from '@/utils/request'

export function getActivityTypes(params) {
  return request({
    url: '/admin/activity-types',
    method: 'get',
    params
  })
}

export function getAllActivityTypes(params) {
  return request({
    url: '/admin/activity-types/all',
    method: 'get',
    params
  })
}

export function getActivityType(id) {
  return request({
    url: `/admin/activity-types/${id}`,
    method: 'get'
  })
}

export function createActivityType(data) {
  return request({
    url: '/admin/activity-types',
    method: 'post',
    data
  })
}

export function updateActivityType(id, data) {
  return request({
    url: `/admin/activity-types/${id}`,
    method: 'put',
    data
  })
}

export function deleteActivityType(id) {
  return request({
    url: `/admin/activity-types/${id}`,
    method: 'delete'
  })
}
