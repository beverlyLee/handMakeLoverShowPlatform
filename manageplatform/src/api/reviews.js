import request from '@/utils/request'

export function getReviews(params) {
  return request({
    url: '/admin/reviews/list',
    method: 'get',
    params
  })
}

export function replyReview(id, data) {
  return request({
    url: `/admin/reviews/${id}/reply`,
    method: 'post',
    data
  })
}

export function getReviewDetail(id) {
  return request({
    url: `/reviews/${id}`,
    method: 'get'
  })
}

export function deleteReview(id) {
  return request({
    url: `/reviews/${id}`,
    method: 'delete'
  })
}
