import request from '@/utils/request'

export function getSystemConfigs(params) {
  return request({
    url: '/admin/system-configs',
    method: 'get',
    params
  })
}

export function saveSystemConfigs(data) {
  return request({
    url: '/admin/system-configs/save',
    method: 'post',
    data
  })
}

export function updateSystemConfig(id, data) {
  return request({
    url: `/admin/system-configs/${id}`,
    method: 'put',
    data
  })
}
