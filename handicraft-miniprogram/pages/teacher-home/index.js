const { getTeacherPublicInfo, getTeacherPublicOrderStats, getUserInfo } = require('../../api/users');
const { getProducts } = require('../../api/products');
const { showToast } = require('../../utils/util');
const storage = require('../../utils/storage');

Page({
  data: {
    teacherId: null,
    teacher: null,
    products: [],
    orderStats: null,
    recentOrders: [],
    currentTab: 'info',
    isLoading: true,
    productsLoading: false,
    productsPage: 1,
    productsPageSize: 10,
    productsHasMore: true,
    ordersLoading: false,
    currentUser: null,
    isOwner: false
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
    this.loadAllData();
  },

  onPullDownRefresh() {
    this.setData({
      productsPage: 1,
      productsHasMore: true,
      products: [],
      isRefreshing: true
    });
    this.loadAllData().then(() => {
      wx.stopPullDownRefresh();
      this.setData({ isRefreshing: false });
    });
  },

  onReachBottom() {
    if (this.data.currentTab === 'products' && this.data.productsHasMore && !this.data.productsLoading) {
      this.setData({
        productsPage: this.data.productsPage + 1
      });
      this.loadTeacherProducts(true);
    }
  },

  onShareAppMessage() {
    const teacher = this.data.teacher;
    return {
      title: (teacher && teacher.real_name) || '手作老师',
      path: `/pages/teacher-home/index?id=${this.data.teacherId}`
    };
  },

  async loadAllData() {
    this.setData({ isLoading: true });
    
    try {
      await Promise.all([
        this.loadCurrentUser(),
        this.loadTeacherInfo(),
        this.loadTeacherProducts(),
        this.loadOrderStats()
      ]);
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      this.setData({ isLoading: false });
    }
  },

  async loadCurrentUser() {
    try {
      const token = storage.getToken();
      if (!token) {
        console.log('用户未登录，不判断是否为所有者');
        const cachedUser = storage.getUserInfo();
        if (cachedUser) {
          this.setData({ currentUser: cachedUser });
          this.checkIsOwner();
        }
        return;
      }
      
      try {
        const userInfo = await getUserInfo();
        if (userInfo) {
          this.setData({ currentUser: userInfo });
          this.checkIsOwner();
        }
      } catch (apiError) {
        console.log('API获取用户信息失败，尝试使用缓存:', apiError);
        const cachedUser = storage.getUserInfo();
        if (cachedUser) {
          this.setData({ currentUser: cachedUser });
          this.checkIsOwner();
        }
      }
    } catch (error) {
      console.log('获取当前用户信息失败:', error);
    }
  },

  checkIsOwner() {
    const teacher = this.data.teacher;
    const currentUser = this.data.currentUser;
    
    if (teacher && currentUser) {
      const isOwner = teacher.user_id === currentUser.id;
      this.setData({ isOwner: isOwner });
      console.log('判断是否为所有者:', { 
        teacherUserId: teacher.user_id, 
        currentUserId: currentUser.id, 
        isOwner: isOwner 
      });
    }
  },

  async loadTeacherInfo() {
    try {
      const teacher = await getTeacherPublicInfo(this.data.teacherId);
      this.setData({ teacher: teacher });
      this.checkIsOwner();
    } catch (error) {
      console.error('加载老师信息失败:', error);
      showToast('加载老师信息失败');
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
      showToast('加载作品失败');
    }
  },

  async loadOrderStats() {
    this.setData({ ordersLoading: true });
    
    try {
      const result = await getTeacherPublicOrderStats(this.data.teacherId);
      this.setData({
        orderStats: result.stats,
        recentOrders: result.recent_orders || [],
        statusNames: result.status_names,
        ordersLoading: false
      });
    } catch (error) {
      console.error('加载订单统计失败:', error);
      this.setData({ ordersLoading: false });
    }
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ currentTab: tab });
    
    if (tab === 'products' && this.data.products.length === 0) {
      this.loadTeacherProducts();
    }
    if (tab === 'orders' && this.data.recentOrders.length === 0 && !this.data.orderStats) {
      this.loadOrderStats();
    }
  },

  goToProductDetail(e) {
    const productId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/work-detail/index?id=${productId}`
    });
  },

  goToProductList() {
    wx.navigateTo({
      url: `/pages/products/index?teacher_id=${this.data.teacherId}`
    });
  },

  followTeacher() {
    showToast('关注功能开发中');
  },

  contactTeacher() {
    showToast('联系老师功能开发中');
  },

  goToEditProfile() {
    const teacherId = this.data.teacherId;
    if (teacherId) {
      wx.navigateTo({
        url: `/pages/teacher-profile/index?id=${teacherId}`
      });
    } else {
      showToast('获取老师信息失败');
    }
  },

  goToManage() {
    showToast('管理后台功能开发中');
  },

  getStatusColor(status) {
    const colors = {
      pending: '#999999',
      paid: '#FF9800',
      shipped: '#2196F3',
      delivered: '#9C27B0',
      completed: '#4CAF50',
      cancelled: '#F44336'
    };
    return colors[status] || '#999999';
  }
});
