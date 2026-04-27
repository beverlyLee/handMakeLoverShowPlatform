const { get, post } = require('../utils/request');

function getCoupons(params = {}) {
  return get('/promotions/coupons', params);
}

function getCouponDetail(couponId) {
  return get(`/promotions/coupons/${couponId}`);
}

function receiveCoupon(couponId) {
  return post(`/promotions/coupons/${couponId}/receive`);
}

function getMyCoupons(params = {}) {
  return get('/promotions/my-coupons', params);
}

function getMyCouponDetail(userCouponId) {
  return get(`/promotions/my-coupons/${userCouponId}`);
}

function calculateDiscount(data) {
  return post('/promotions/coupons/calculate', data);
}

const SHIPPING_METHODS = [
  { key: 'standard', name: '标准快递', estimatedDays: 3, fee: 0 },
  { key: 'express', name: '特快专递', estimatedDays: 2, fee: 5 },
  { key: 'sf', name: '顺丰速运', estimatedDays: 2, fee: 10 },
  { key: 'jd', name: '京东物流', estimatedDays: 1, fee: 8 },
  { key: 'zt', name: '中通快递', estimatedDays: 3, fee: 0 },
  { key: 'yt', name: '圆通速递', estimatedDays: 3, fee: 0 }
];

const PAY_METHODS = [
  { key: 'wechat', name: '微信支付', icon: 'wechat' },
  { key: 'alipay', name: '支付宝', icon: 'alipay' },
  { key: 'balance', name: '余额支付', icon: 'balance' }
];

function getShippingMethod(key) {
  return SHIPPING_METHODS.find(m => m.key === key) || SHIPPING_METHODS[0];
}

function getPayMethod(key) {
  return PAY_METHODS.find(m => m.key === key) || PAY_METHODS[0];
}

module.exports = {
  getCoupons,
  getCouponDetail,
  receiveCoupon,
  getMyCoupons,
  getMyCouponDetail,
  calculateDiscount,
  SHIPPING_METHODS,
  PAY_METHODS,
  getShippingMethod,
  getPayMethod
};
