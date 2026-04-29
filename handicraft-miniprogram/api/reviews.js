const { get, post, put, del } = require('../utils/request');

function getReviewDetailItems() {
  return get('/reviews/detail-items');
}

function getReviews(params = {}) {
  return get('/reviews', params);
}

function getReviewById(reviewId) {
  return get(`/reviews/${reviewId}`);
}

function getOrderReview(orderId) {
  return get(`/reviews/order/${orderId}`);
}

function createReview(data) {
  return post('/reviews', data);
}

function replyReview(reviewId, content) {
  return post(`/reviews/${reviewId}/reply`, { content });
}

function appendReview(reviewId, content, images) {
  return post(`/reviews/${reviewId}/append`, { content, images });
}

function deleteAppendReview(appendReviewId) {
  return del(`/reviews/append/${appendReviewId}`);
}

function updateReview(reviewId, data) {
  return put(`/reviews/${reviewId}`, data);
}

function deleteReview(reviewId) {
  return del(`/reviews/${reviewId}`);
}

function likeReview(reviewId) {
  return post(`/reviews/${reviewId}/like`);
}

function getProductReviews(productId, params = {}) {
  return get(`/reviews/product/${productId}`, params);
}

function getProductReviewStats(productId) {
  return get(`/reviews/product/${productId}/stats`);
}

function getTeacherReviews(teacherUserId, params = {}) {
  return get(`/reviews/teacher/${teacherUserId}`, params);
}

function getTeacherReviewStats(teacherUserId) {
  return get(`/reviews/teacher/${teacherUserId}/stats`);
}

function calculateRating(data) {
  return post('/reviews/calculate-rating', data);
}

function markReviewRead(reviewId) {
  return post(`/reviews/${reviewId}/read`);
}

function markReviewsBatchRead(reviewIds) {
  return post('/reviews/batch-read', { review_ids: reviewIds });
}

function getTeacherUnreadStats(teacherUserId) {
  return get(`/reviews/teacher/${teacherUserId}/unread-stats`);
}

function updateReviewReply(reviewId, content) {
  return put(`/reviews/${reviewId}/reply`, { content });
}

function getTeacherTrendStats(teacherUserId, params = {}) {
  return get(`/reviews/teacher/${teacherUserId}/trend-stats`, params);
}

module.exports = {
  getReviewDetailItems,
  getReviews,
  getReviewById,
  getOrderReview,
  createReview,
  updateReview,
  deleteReview,
  replyReview,
  appendReview,
  deleteAppendReview,
  likeReview,
  getProductReviews,
  getProductReviewStats,
  getTeacherReviews,
  getTeacherReviewStats,
  calculateRating,
  markReviewRead,
  markReviewsBatchRead,
  getTeacherUnreadStats,
  updateReviewReply,
  getTeacherTrendStats
};
