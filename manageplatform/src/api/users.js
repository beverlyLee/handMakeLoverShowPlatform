import request from '@/utils/request'

export function getUsers(params) {
  return request({
    url: '/admin/users/list',
    method: 'get',
    params
  })
}

export function getUserDetail(id) {
  return request({
    url: `/admin/users/${id}`,
    method: 'get'
  })
}

export function updateUser(id, data) {
  return request({
    url: `/admin/users/${id}`,
    method: 'put',
    data
  })
}

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

export function updateUserRoles(userId, data) {
  return request({
    url: `/admin/users/roles/${userId}`,
    method: 'put',
    data
  })
}

export function getTeacherProfile(userId) {
  return request({
    url: `/users/teacher/${userId}`,
    method: 'get'
  })
}
