import request from '@/utils/request'

export function login(data) {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

export function getUserInfo() {
  return request({
    url: '/auth/profile',
    method: 'get'
  })
}

export function logout() {
  return request({
    url: '/auth/logout',
    method: 'post'
  })
}

export function adminLogin(data) {
  return request({
    url: '/auth/admin/login',
    method: 'post',
    data
  })
}

export function getAdminProfile() {
  return request({
    url: '/auth/admin/profile',
    method: 'get'
  })
}

export function updateAdminProfile(data) {
  return request({
    url: '/auth/admin/profile',
    method: 'put',
    data
  })
}

export function changePassword(data) {
  return request({
    url: '/auth/admin/change-password',
    method: 'post',
    data
  })
}
