const { getProductDetail } = require('../../api/products');
const { showToast } = require('../../utils/util');

Page({
  data: {
    productId: null,
    product: null,
    isLoading: true,
    currentImageIndex: 0,
    showTeacherProfile: false
  },

  onLoad(options) {
    const productId = options.id;
    if (!productId) {
      showToast('参数错误');
      wx.navigateBack();
      return;
    }

    this.setData({ productId: parseInt(productId) });
    this.loadProductDetail();
  },

  onShareAppMessage() {
    const product = this.data.product;
    return {
      title: (product && product.title) || '精彩手作作品',
      path: `/pages/product-detail/index?id=${this.data.productId}`
    };
  },

  async loadProductDetail() {
    this.setData({ isLoading: true });

    try {
      const product = await getProductDetail(this.data.productId);
      this.setData({
        product: product,
        isLoading: false
      });
    } catch (error) {
      console.error('加载作品详情失败:', error);
      this.setData({ isLoading: false });
      showToast('加载失败，请重试');
    }
  },

  previewImage(e) {
    const current = e.currentTarget.dataset.url;
    const urls = (this.data.product && this.data.product.images) || [];
    
    wx.previewImage({
      current: current,
      urls: urls
    });
  },

  goToTeacherProfile(e) {
    const teacherId = e.currentTarget.dataset.teacherId;
    wx.navigateTo({
      url: `/pages/teacher-profile/index?id=${teacherId}`
    });
  },

  goToTeacherProducts(e) {
    const teacherId = e.currentTarget.dataset.teacherId;
    wx.navigateTo({
      url: `/pages/teacher-profile/index?id=${teacherId}&tab=products`
    });
  },

  addToCart() {
    showToast('加入购物车功能开发中');
  },

  buyNow() {
    showToast('立即购买功能开发中');
  },

  toggleFavorite() {
    showToast('收藏功能开发中');
  },

  contactTeacher() {
    showToast('联系老师功能开发中');
  }
});
