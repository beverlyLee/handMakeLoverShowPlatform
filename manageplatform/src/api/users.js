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

export function updateUserStatus(userId, data) {
  return request({
    url: `/admin/users/${userId}/status`,
    method: 'put',
    data
  })
}

export function getUserLikes(userId, params) {
  return request({
    url: `/admin/users/${userId}/likes`,
    method: 'get',
    params
  })
}

export function getUserOrders(userId, params) {
  return request({
    url: `/admin/users/${userId}/orders`,
    method: 'get',
    params
  })
}

export function getUserReviews(userId, params) {
  return request({
    url: `/admin/users/${userId}/reviews`,
    method: 'get',
    params
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

export function getPendingTeachers(params) {
  return request({
    url: '/admin/teachers/pending',
    method: 'get',
    params
  })
}

export function verifyTeacher(teacherId, data) {
  return request({
    url: `/admin/teachers/${teacherId}/verify`,
    method: 'post',
    data
  })
}

export function getTeachers(params) {
  return request({
    url: '/admin/teachers/list',
    method: 'get',
    params
  })
}

export function getTeacherDetail(teacherId) {
  return request({
    url: `/admin/teachers/${teacherId}`,
    method: 'get'
  })
}

export function updateTeacher(teacherId, data) {
  return request({
    url: `/admin/teachers/${teacherId}`,
    method: 'put',
    data
  })
}

export function checkTeacherPendingOrders(teacherId) {
  return request({
    url: `/admin/teachers/${teacherId}/check-pending-orders`,
    method: 'get'
  })
}

export function updateTeacherStatus(teacherId, data) {
  return request({
    url: `/admin/teachers/${teacherId}/status`,
    method: 'put',
    data
  })
}

export function getTeacherProducts(teacherId, params) {
  return request({
    url: `/admin/teachers/${teacherId}/products`,
    method: 'get',
    params
  })
}

export function getTeacherOrders(teacherId, params) {
  return request({
    url: `/admin/teachers/${teacherId}/orders`,
    method: 'get',
    params
  })
}

export function getTeacherReviews(teacherId, params) {
  return request({
    url: `/admin/teachers/${teacherId}/reviews`,
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

export function getSpecialties() {
  return request({
    url: '/admin/specialties/all',
    method: 'get'
  })
}
