const { getOrders, payOrder, cancelOrder, confirmOrder, getTeacherOrders, updateOrderStatus } = require('../../api/orders');
const { showToast } = require('../../utils/util');
const storage = require('../../utils/storage');

const CUSTOMER_TABS = [
  { label: '全部', value: '' },
  { label: '待付款', value: 'pending' },
  { label: '待发货', value: 'paid' },
  { label: '待收货', value: 'shipped' },
  { label: '已完成', value: 'completed' }
];

const TEACHER_TABS = [
  { label: '全部', value: '' },
  { label: '待发货', value: 'paid' },
  { label: '待收货', value: 'shipped' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' }
];

Page({
  data: {
    orderTabs: CUSTOMER_TABS,
    currentTab: '',
    orders: [],
    page: 1,
    pageSize: 10,
    hasMore: true,
    isLoading: false,

    currentRole: 'customer',
    isTeacher: false,
    userInfo: null,
    teacherInfo: null,

    showShipDialog: false,
    selectedOrder: null
  },

  onLoad(options) {
    console.log('订单页面加载');
    this.initTestToken();

    if (options.status) {
      this.setData({
        currentTab: options.status
      });
    }

    this.loadUserRoleAndOrders();
  },

  initTestToken() {
    const currentToken = storage.getToken();
    if (!currentToken) {
      storage.setToken('test_token');
      console.log('已设置测试 Token');
    }
  },

  onShow() {
    console.log('订单页面显示');
    this.loadUserRoleAndOrders();
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setSelected(2)
    }
  },

  onPullDownRefresh() {
    this.setData({
      page: 1,
      orders: [],
      hasMore: true
    });
    this.loadOrders().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.isLoading) {
      this.setData({
        page: this.data.page + 1
      });
      this.loadOrders(true);
    }
  },

  async loadUserRoleAndOrders() {
    const userInfo = storage.getUserInfo();
    console.log('从 storage 获取用户信息:', userInfo);

    if (userInfo) {
      const currentRole = userInfo.current_role || userInfo.role || 'customer';
      const roles = userInfo.roles || ['customer'];
      const isTeacher = roles.includes('teacher');
      const teacherInfo = userInfo.teacher_info || null;

      const orderTabs = currentRole === 'teacher' ? TEACHER_TABS : CUSTOMER_TABS;

      this.setData({
        userInfo: userInfo,
        currentRole: currentRole,
        isTeacher: isTeacher,
        teacherInfo: teacherInfo,
        orderTabs: orderTabs,
        page: 1,
        orders: [],
        hasMore: true
      });

      await this.loadOrders();
    } else {
      console.log('用户信息为空，使用默认角色');
      this.setData({
        currentRole: 'customer',
        isTeacher: false,
        orderTabs: CUSTOMER_TABS,
        page: 1,
        orders: [],
        hasMore: true
      });

      await this.loadOrders();
    }
  },

  async loadOrders(append = false) {
    if (this.data.isLoading) return;

    this.setData({ isLoading: true });

    try {
      const params = {
        page: this.data.page,
        size: this.data.pageSize,
        role: this.data.currentRole
      };

      if (this.data.currentTab) {
        params.status = this.data.currentTab;
      }

      const userId = this.data.userInfo?.id;
      const teacherInfo = this.data.teacherInfo;
      const teacherId = teacherInfo?.teacher_id ? parseInt(teacherInfo.teacher_id.replace(/[^0-9]/g, '').slice(-8)) : 2;

      if (this.data.currentRole === 'customer' && userId) {
        params.user_id = userId;
      }

      if (this.data.currentRole === 'teacher') {
        params.teacher_id = teacherId;
      }

      console.log('加载订单参数:', params);

      let result;
      if (this.data.currentRole === 'teacher') {
        result = await getTeacherOrders(params);
      } else {
        result = await getOrders(params);
      }

      console.log('订单数据结果:', result);

      const newOrders = result?.list || result?.orders || [];

      if (append) {
        this.setData({
          orders: [...this.data.orders, ...newOrders],
          hasMore: newOrders.length >= this.data.pageSize,
          isLoading: false
        });
      } else {
        this.setData({
          orders: newOrders,
          hasMore: newOrders.length >= this.data.pageSize,
          isLoading: false
        });
      }
    } catch (error) {
      console.error('加载订单列表失败:', error);
      this.setData({ isLoading: false });
      showToast('加载失败，请重试');
    }
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({
      currentTab: tab,
      page: 1,
      orders: [],
      hasMore: true
    });
    this.loadOrders();
  },

  getStatusText(status) {
    const statusMap = {
      'pending': '待付款',
      'paid': '待发货',
      'shipped': '待收货',
      'delivered': '已送达',
      'completed': '已完成',
      'cancelled': '已取消'
    };
    return statusMap[status] || status;
  },

  getTeacherStatusText(status) {
    const statusMap = {
      'paid': '待发货',
      'shipped': '待收货',
      'delivered': '已送达',
      'completed': '已完成',
      'cancelled': '已取消'
    };
    return statusMap[status] || status;
  },

  goToOrderDetail(e) {
    const orderId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/order-detail/index?id=${orderId}`
    });
  },

  stopPropagation() {
    return;
  },

  async payOrder(e) {
    const orderId = e.currentTarget.dataset.id;
    wx.showLoading({ title: '支付中...', mask: true });

    try {
      await payOrder(orderId);
      wx.hideLoading();
      showToast('支付成功', 'success');
      this.setData({ page: 1, orders: [], hasMore: true });
      this.loadOrders();
    } catch (error) {
      console.error('支付失败:', error);
      wx.hideLoading();
      showToast('支付失败，请重试');
    }
  },

  async cancelOrder(e) {
    const orderId = e.currentTarget.dataset.id;
    wx.showModal({
      title: '提示',
      content: '确定要取消订单吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await cancelOrder(orderId, { cancel_reason: '用户主动取消' });
            showToast('订单已取消', 'success');
            this.setData({ page: 1, orders: [], hasMore: true });
            this.loadOrders();
          } catch (error) {
            console.error('取消订单失败:', error);
            showToast('取消失败，请重试');
          }
        }
      }
    });
  },

  async confirmOrder(e) {
    const orderId = e.currentTarget.dataset.id;
    wx.showModal({
      title: '提示',
      content: '确认收货后将无法退换，确定吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await confirmOrder(orderId);
            showToast('确认收货成功', 'success');
            this.setData({ page: 1, orders: [], hasMore: true });
            this.loadOrders();
          } catch (error) {
            console.error('确认收货失败:', error);
            showToast('操作失败，请重试');
          }
        }
      }
    });
  },

  showShipOrderDialog(e) {
    const orderId = e.currentTarget.dataset.id;
    const order = this.data.orders.find(o => o.id === orderId);

    if (order) {
      this.setData({
        selectedOrder: order,
        showShipDialog: true
      });
    }
  },

  closeShipDialog() {
    this.setData({
      showShipDialog: false,
      selectedOrder: null
    });
  },

  async shipOrder() {
    if (!this.data.selectedOrder) return;

    wx.showLoading({ title: '操作中...', mask: true });

    try {
      await updateOrderStatus(this.data.selectedOrder.id, {
        status: 'shipped'
      });

      wx.hideLoading();
      showToast('发货成功', 'success');
      this.closeShipDialog();

      this.setData({ page: 1, orders: [], hasMore: true });
      this.loadOrders();
    } catch (error) {
      console.error('发货失败:', error);
      wx.hideLoading();
      showToast('操作失败，请重试');
    }
  },

  goToReview(e) {
    const orderId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/order-review/index?id=${orderId}`
    });
  },

  async deleteOrder(e) {
    const orderId = e.currentTarget.dataset.id;
    wx.showModal({
      title: '提示',
      content: '确定要删除该订单吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            const newOrders = this.data.orders.filter(order => order.id !== orderId);
            this.setData({ orders: newOrders });
            showToast('删除成功', 'success');
          } catch (error) {
            console.error('删除订单失败:', error);
            showToast('删除失败，请重试');
          }
        }
      }
    });
  },

  goToProducts() {
    wx.switchTab({
      url: '/pages/products/index'
    });
  }
});
