const { getProductDetail } = require('../../api/products');
const { createOrder } = require('../../api/orders');
const { getProfile } = require('../../api/auth');
const { showToast } = require('../../utils/util');
const { getUserInfo } = require('../../utils/storage');

const DEFAULT_IMAGE = 'https://picsum.photos/seed/handmade-craft-default/400/400';

Page({
  data: {
    productId: null,
    product: null,
    isLoading: true,
    currentImageIndex: 0,
    userInfo: null,
    isCustomer: true,
    isTeacher: false,
    showOrderConfirm: false,
    orderQuantity: 1
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
      
      if (product) {
        if (!product.images || product.images.length === 0) {
          if (product.cover_image) {
            product.images = [product.cover_image];
          } else {
            product.images = [DEFAULT_IMAGE];
          }
        }
        
        if (!product.cover_image && product.images && product.images.length > 0) {
          product.cover_image = product.images[0];
        }
      }
      
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
      url: `/pages/teacher-profile/index?id=${teacherId}`
    });
  },

  goToTeacherProducts(e) {
    const teacherId = e.currentTarget.dataset.teacherId;
    wx.navigateTo({
      url: `/pages/teacher-profile/index?id=${teacherId}&tab=products`
    });
  },

  goBackHome() {
    wx.switchTab({
      url: '/pages/home/index'
    });
  },

  showOrderConfirmDialog() {
    if (this.data.isTeacher) {
      showToast('老师身份无法下单，请切换到客户身份');
      return;
    }

    if (!this.data.userInfo) {
      showToast('请先登录后再下单');
      return;
    }

    this.setData({
      showOrderConfirm: true,
      orderQuantity: 1
    });
  },

  hideOrderConfirmDialog() {
    this.setData({
      showOrderConfirm: false
    });
  },

  decreaseQuantity() {
    if (this.data.orderQuantity > 1) {
      this.setData({
        orderQuantity: this.data.orderQuantity - 1
      });
    }
  },

  increaseQuantity() {
    const product = this.data.product;
    const stock = product ? (product.stock || 999) : 999;
    
    if (this.data.orderQuantity < stock) {
      this.setData({
        orderQuantity: this.data.orderQuantity + 1
      });
    } else {
      showToast('已达库存上限');
    }
  },

  async confirmOrder() {
    const product = this.data.product;
    if (!product) return;

    wx.showLoading({
      title: '创建订单中...',
      mask: true
    });

    try {
      const orderData = {
        teacher_id: product.teacher_id,
        items: [{
          product_id: product.id,
          product_title: product.title,
          product_image: product.cover_image || (product.images && product.images[0]),
          price: product.price,
          original_price: product.original_price || product.price,
          quantity: this.data.orderQuantity
        }]
      };

      const result = await createOrder(orderData);
      
      wx.hideLoading();
      this.hideOrderConfirmDialog();
      
      showToast('下单成功');
      
      setTimeout(() => {
        wx.navigateTo({
          url: `/pages/orders/index`
        });
      }, 1500);
    } catch (error) {
      wx.hideLoading();
      console.error('创建订单失败:', error);
      showToast(error.msg || '下单失败，请重试');
    }
  },

  contactTeacher() {
    showToast('联系老师功能开发中');
  },

  toggleFavorite() {
    showToast('收藏功能开发中');
  }
});
