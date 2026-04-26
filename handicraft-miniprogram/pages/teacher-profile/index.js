const { getTeacherPublicInfo } = require('../../api/users');
const { getProducts } = require('../../api/products');
const { showToast } = require('../../utils/util');

Page({
  data: {
    teacherId: null,
    teacher: null,
    products: [],
    currentTab: 'info',
    isLoading: true,
    productsLoading: false,
    productsPage: 1,
    productsPageSize: 10,
    productsHasMore: true
  },

  onLoad(options) {
    const teacherId = options.id;
    const tab = options.tab || 'info';
    
    if (!teacherId) {
      showToast('参数错误');
      wx.navigateBack();
      return;
    }

    this.setData({ 
      teacherId: parseInt(teacherId),
      currentTab: tab
    });
    this.loadTeacherInfo();
  },

  onShareAppMessage() {
    const teacher = this.data.teacher;
    return {
      title: (teacher && teacher.real_name) || '手作老师',
      path: `/pages/teacher-profile/index?id=${this.data.teacherId}`
    };
  },

  async loadTeacherInfo() {
    this.setData({ isLoading: true });

    try {
      const teacher = await getTeacherPublicInfo(this.data.teacherId);
      this.setData({
        teacher: teacher,
        isLoading: false
      });
      
      if (this.data.currentTab === 'products') {
        this.loadTeacherProducts();
      }
    } catch (error) {
      console.error('加载老师信息失败:', error);
      this.setData({ isLoading: false });
      showToast('加载失败，请重试');
    }
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ currentTab: tab });
    
    if (tab === 'products' && this.data.products.length === 0) {
      this.loadTeacherProducts();
    }
  },

  async loadTeacherProducts(append = false) {
    if (this.data.productsLoading) return;

    this.setData({ productsLoading: true });

    try {
      const params = {
        page: append ? this.data.productsPage : 1,
        size: this.data.productsPageSize,
        teacher_id: this.data.teacherId,
        sort: 'newest'
      };

      const result = await getProducts(params);
      const newProducts = (result && result.list) || result || [];

      if (append) {
        this.setData({
          products: [...this.data.products, ...newProducts],
          productsHasMore: newProducts.length >= this.data.productsPageSize,
          productsLoading: false
        });
      } else {
        this.setData({
          products: newProducts,
          productsPage: 1,
          productsHasMore: newProducts.length >= this.data.productsPageSize,
          productsLoading: false
        });
      }
    } catch (error) {
      console.error('加载老师作品失败:', error);
      this.setData({ productsLoading: false });
      showToast('加载失败，请重试');
    }
  },

  onReachBottom() {
    if (this.data.currentTab === 'products' && this.data.productsHasMore && !this.data.productsLoading) {
      this.setData({
        productsPage: this.data.productsPage + 1
      });
      this.loadTeacherProducts(true);
    }
  },

  goToProductDetail(e) {
    const productId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/product-detail/index?id=${productId}`
    });
  },

  followTeacher() {
    showToast('关注功能开发中');
  },

  contactTeacher() {
    showToast('联系老师功能开发中');
  }
});
