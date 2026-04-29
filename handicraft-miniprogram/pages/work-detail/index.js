const { getProductDetail } = require('../../api/products');
const { getProfile } = require('../../api/auth');
const { getProductReviews, getProductReviewStats } = require('../../api/reviews');
const { showToast, getFullImageUrl, processProductImages } = require('../../utils/util');
const { getUserInfo } = require('../../utils/storage');

Page({
  data: {
    productId: null,
    product: null,
    isLoading: true,
    currentImageIndex: 0,
    userInfo: null,
    isCustomer: true,
    isTeacher: false,
    reviewStats: null,
    reviews: [],
    reviewsLoading: false,
    reviewsPage: 1,
    reviewsPageSize: 3,
    reviewsHasMore: true
  },

  onLoad(options) {
    console.log('work-detail onLoad, options:', options);
    const productId = options.id;
    if (!productId) {
      showToast('参数错误');
      wx.navigateBack();
      return;
    }

    this.setData({ productId: parseInt(productId) });
    this.loadProductDetail();
  },

  onShow() {
    console.log('work-detail onShow, 开始加载用户信息');
    this.loadUserInfo();
  },

  onShareAppMessage() {
    const product = this.data.product;
    return {
      title: (product && product.title) || '精彩手作作品',
      path: `/pages/work-detail/index?id=${this.data.productId}`
    };
  },

  async loadUserInfo() {
    try {
      let userInfo = null;
      
      try {
        userInfo = await getProfile();
        console.log('从后端获取用户信息成功:', userInfo);
      } catch (e) {
        console.log('从后端获取用户信息失败，尝试使用本地缓存:', e);
        userInfo = getUserInfo();
      }

      if (userInfo) {
        const currentRole = userInfo.current_role || userInfo.role || 'customer';
        const isTeacher = currentRole === 'teacher';
        const isCustomer = !isTeacher;
        
        console.log('用户角色判断:', { currentRole, isTeacher, isCustomer });
        
        this.setData({
          userInfo: userInfo,
          isCustomer: isCustomer,
          isTeacher: isTeacher
        });
      } else {
        console.log('未获取到用户信息，默认作为客户');
        this.setData({
          userInfo: null,
          isCustomer: true,
          isTeacher: false
        });
      }
    } catch (error) {
      console.error('加载用户信息失败:', error);
      this.setData({
        userInfo: null,
        isCustomer: true,
        isTeacher: false
      });
    }
  },

  async loadProductDetail() {
    console.log('开始加载作品详情, productId:', this.data.productId);
    this.setData({ isLoading: true });

    try {
      const product = await getProductDetail(this.data.productId);
      console.log('加载作品详情成功:', product);
      
      const processedProduct = processProductImages(product);
      
      this.setData({
        product: processedProduct,
        isLoading: false
      });

      this.loadReviewStats();
      this.loadReviews(true);
    } catch (error) {
      console.error('加载作品详情失败:', error);
      this.setData({ isLoading: false });
      showToast('加载失败，请重试');
    }
  },

  async loadReviewStats() {
    try {
      const result = await getProductReviewStats(this.data.productId);
      if (result && result.stats) {
        const stats = result.stats;
        const mappedStats = {
          total: stats.total || 0,
          avg_rating: stats.avg_overall_rating || 0,
          goodCount: stats.good_count || 0,
          mediumCount: stats.medium_count || 0,
          badCount: stats.bad_count || 0
        };
        this.setData({ reviewStats: mappedStats });
      }
    } catch (error) {
      console.error('加载评价统计失败:', error);
    }
  },

  processReviews(reviews) {
    if (!reviews || !Array.isArray(reviews)) return [];
    
    return reviews.map(review => {
      const processed = { ...review };
      
      if (processed.user_avatar && !processed.is_anonymous) {
        processed.user_avatar = getFullImageUrl(processed.user_avatar);
      }
      
      if (processed.images && Array.isArray(processed.images)) {
        processed.images = processed.images.map(img => getFullImageUrl(img));
      }
      
      return processed;
    });
  },

  async loadReviews(append = false) {
    const { reviewsPage, reviewsPageSize, reviewsHasMore, reviewsLoading, productId } = this.data;
    
    if (reviewsLoading || !reviewsHasMore) return;

    this.setData({ reviewsLoading: true });

    try {
      const result = await getProductReviews(productId, {
        page: append ? reviewsPage : 1,
        page_size: reviewsPageSize
      });

      if (result) {
        const newReviews = this.processReviews(result.list || []);
        const total = result.total || 0;

        if (append) {
          this.setData({
            reviews: [...this.data.reviews, ...newReviews],
            reviewsHasMore: newReviews.length >= reviewsPageSize,
            reviewsPage: reviewsPage + 1,
            reviewsLoading: false
          });
        } else {
          this.setData({
            reviews: newReviews,
            reviewsHasMore: newReviews.length >= reviewsPageSize,
            reviewsPage: 2,
            reviewsLoading: false
          });
        }
      }
    } catch (error) {
      console.error('加载评价列表失败:', error);
      this.setData({ reviewsLoading: false });
    }
  },

  onImageChange(e) {
    this.setData({
      currentImageIndex: e.detail.current
    });
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
      url: `/pages/teacher-home/index?id=${teacherId}`
    });
  },

  goToTeacherProducts(e) {
    const teacherId = e.currentTarget.dataset.teacherId;
    wx.navigateTo({
      url: `/pages/teacher-home/index?id=${teacherId}&tab=products`
    });
  },

  goBackHome() {
    wx.switchTab({
      url: '/pages/home/index'
    });
  },

  addToCart() {
    if (!this.data.userInfo) {
      showToast('请先登录');
      return;
    }
    showToast('加入购物车功能开发中');
  },

  buyNow() {
    if (!this.data.userInfo) {
      showToast('请先登录后再下单');
      return;
    }

    if (this.data.isTeacher) {
      showToast('老师身份无法下单，请切换到客户身份');
      return;
    }

    const product = this.data.product;
    if (!product) return;

    wx.navigateTo({
      url: `/pages/order-confirm/index?id=${product.id}`
    });
  },

  showOrderConfirmDialog() {
    if (!this.data.userInfo) {
      showToast('请先登录后再下单');
      return;
    }

    if (this.data.isTeacher) {
      showToast('老师身份无法下单，请切换到客户身份');
      return;
    }

    wx.navigateTo({
      url: `/pages/order-confirm/index?id=${this.data.productId}`
    });
  },

  contactTeacher() {
    showToast('联系老师功能开发中');
  },

  toggleFavorite() {
    showToast('收藏功能开发中');
  },

  goToAllReviews() {
    wx.navigateTo({
      url: `/pages/reviews/index?source=product&productId=${this.data.productId}`
    });
  },

  goToReviewDetail(e) {
    const { id } = e.currentTarget.dataset;
    if (id) {
      wx.navigateTo({
        url: `/pages/review-detail/index?id=${id}`
      });
    }
  },

  previewReviewImage(e) {
    const { url, index } = e.currentTarget.dataset;
    const { reviews } = this.data;
    const review = reviews[index];
    const images = review.images || [];
    
    wx.previewImage({
      current: url,
      urls: images
    });
  },

  formatReviewTime(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`;
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }
});
