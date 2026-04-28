const { 
  getOrders, 
  payOrder, 
  cancelOrder, 
  confirmOrder, 
  getTeacherOrders, 
  updateOrderStatus, 
  deleteOrder,
  acceptOrder,
  rejectOrder,
  shipOrder,
  getTeacherOrderStats
} = require('../../api/orders');
const { showToast } = require('../../utils/util');
const storage = require('../../utils/storage');

const CUSTOMER_TABS = [
  { label: '全部', value: '' },
  { label: '待付款', value: 'pending' },
  { label: '待接单', value: 'pending_accept' },
  { label: '待发货', value: 'paid' },
  { label: '待收货', value: 'shipped' },
  { label: '已完成', value: 'completed' }
];

const TEACHER_TABS = [
  { label: '全部', value: '' },
  { label: '待接单', value: 'pending_accept' },
  { label: '待发货', value: 'accepted,paid' },
  { label: '待收货', value: 'shipped' },
  { label: '已完成', value: 'completed' }
];

const SHIPPING_COMPANIES = [
  { label: '顺丰速运', value: 'sf' },
  { label: '京东物流', value: 'jd' },
  { label: '中通快递', value: 'zt' },
  { label: '圆通速递', value: 'yt' },
  { label: '韵达快递', value: 'yd' },
  { label: 'EMS', value: 'ems' },
  { label: '其他', value: 'other' }
];

const STATUS_TEXT_MAP = {
  'pending': '待付款',
  'pending_accept': '待接单',
  'accepted': '已接单',
  'paid': '待发货',
  'shipped': '待收货',
  'delivered': '已送达',
  'completed': '已完成',
  'cancelled': '已取消',
  'rejected': '已拒绝',
  'deleted': '已删除'
};

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

    orderStats: null,
    statsLoading: false,

    showAcceptDialog: false,
    showRejectDialog: false,
    showShipDialog: false,
    selectedOrder: null,

    rejectReason: '',
    shippingCompany: 'sf',
    shippingCompanyIndex: 0,
    trackingNumber: '',
    shippingCompanies: SHIPPING_COMPANIES,

    searchKeyword: '',
    showSearch: false,

    expandedOrders: {},
    formattedOrders: []
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
    Promise.all([
      this.loadOrders(),
      this.loadOrderStats()
    ]).then(() => {
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

      await Promise.all([
        this.loadOrders(),
        isTeacher ? this.loadOrderStats() : Promise.resolve()
      ]);
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

  async loadOrderStats() {
    if (!this.data.isTeacher) return;
    
    this.setData({ statsLoading: true });
    
    try {
      const userId = this.data.userInfo?.id;
      const teacherInfo = this.data.teacherInfo;
      const teacherId = userId || (teacherInfo?.user_id) || 2;
      
      const result = await getTeacherOrderStats({ teacher_id: teacherId });
      this.setData({
        orderStats: result.stats,
        statsLoading: false
      });
    } catch (error) {
      console.error('加载订单统计失败:', error);
      this.setData({ statsLoading: false });
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

      if (this.data.searchKeyword) {
        params.keyword = this.data.searchKeyword;
      }

      const userId = this.data.userInfo?.id;
      const teacherInfo = this.data.teacherInfo;
      const teacherId = userId || (teacherInfo?.user_id) || 2;

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
      const formattedOrders = this.formatOrders(newOrders);

      if (append) {
        this.setData({
          orders: [...this.data.orders, ...newOrders],
          formattedOrders: [...this.data.formattedOrders, ...formattedOrders],
          hasMore: newOrders.length >= this.data.pageSize,
          isLoading: false
        });
      } else {
        this.setData({
          orders: newOrders,
          formattedOrders: formattedOrders,
          expandedOrders: {},
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

  toggleSearch() {
    this.setData({
      showSearch: !this.data.showSearch,
      searchKeyword: ''
    });
  },

  onSearchInput(e) {
    this.setData({
      searchKeyword: e.detail.value
    });
  },

  doSearch() {
    this.setData({
      page: 1,
      orders: [],
      hasMore: true
    });
    this.loadOrders();
  },

  clearSearch() {
    this.setData({
      searchKeyword: '',
      page: 1,
      orders: [],
      hasMore: true
    });
    this.loadOrders();
  },

  getStatusText(status) {
    return STATUS_TEXT_MAP[status] || status;
  },

  getTeacherStatusText(status) {
    return STATUS_TEXT_MAP[status] || status;
  },

  isPendingAccept(status) {
    return status === 'pending_accept';
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

  showAcceptDialog(e) {
    const orderId = e.currentTarget.dataset.id;
    const order = this.data.orders.find(o => o.id === orderId);

    if (order) {
      this.setData({
        selectedOrder: order,
        showAcceptDialog: true
      });
    }
  },

  closeAcceptDialog() {
    this.setData({
      showAcceptDialog: false,
      selectedOrder: null
    });
  },

  async confirmAccept() {
    if (!this.data.selectedOrder) return;

    wx.showLoading({ title: '接单中...', mask: true });

    try {
      await acceptOrder(this.data.selectedOrder.id);
      wx.hideLoading();
      showToast('接单成功', 'success');
      this.closeAcceptDialog();

      this.setData({ page: 1, orders: [], hasMore: true });
      await Promise.all([
        this.loadOrders(),
        this.loadOrderStats()
      ]);
    } catch (error) {
      console.error('接单失败:', error);
      wx.hideLoading();
      showToast(error.msg || '接单失败，请重试');
    }
  },

  showRejectDialog(e) {
    const orderId = e.currentTarget.dataset.id;
    const order = this.data.orders.find(o => o.id === orderId);

    if (order) {
      this.setData({
        selectedOrder: order,
        showRejectDialog: true,
        rejectReason: ''
      });
    }
  },

  closeRejectDialog() {
    this.setData({
      showRejectDialog: false,
      selectedOrder: null,
      rejectReason: ''
    });
  },

  onRejectReasonInput(e) {
    this.setData({
      rejectReason: e.detail.value
    });
  },

  async confirmReject() {
    if (!this.data.selectedOrder) return;

    if (!this.data.rejectReason.trim()) {
      showToast('请填写拒单理由');
      return;
    }

    wx.showLoading({ title: '提交中...', mask: true });

    try {
      await rejectOrder(this.data.selectedOrder.id, {
        reject_reason: this.data.rejectReason
      });
      wx.hideLoading();
      showToast('拒单成功', 'success');
      this.closeRejectDialog();

      this.setData({ page: 1, orders: [], hasMore: true });
      await Promise.all([
        this.loadOrders(),
        this.loadOrderStats()
      ]);
    } catch (error) {
      console.error('拒单失败:', error);
      wx.hideLoading();
      showToast(error.msg || '拒单失败，请重试');
    }
  },

  showShipOrderDialog(e) {
    const orderId = e.currentTarget.dataset.id;
    const order = this.data.orders.find(o => o.id === orderId);

    if (order) {
      this.setData({
        selectedOrder: order,
        showShipDialog: true,
        shippingCompany: 'sf',
        shippingCompanyIndex: 0,
        trackingNumber: ''
      });
    }
  },

  closeShipDialog() {
    this.setData({
      showShipDialog: false,
      selectedOrder: null,
      shippingCompany: 'sf',
      shippingCompanyIndex: 0,
      trackingNumber: ''
    });
  },

  onShippingCompanyChange(e) {
    const index = e.detail.value;
    const company = this.data.shippingCompanies[index];
    this.setData({
      shippingCompanyIndex: index,
      shippingCompany: company.value
    });
  },

  onTrackingNumberInput(e) {
    this.setData({
      trackingNumber: e.detail.value
    });
  },

  async shipOrder() {
    if (!this.data.selectedOrder) return;

    if (!this.data.trackingNumber.trim()) {
      showToast('请填写物流单号');
      return;
    }

    wx.showLoading({ title: '发货中...', mask: true });

    try {
      await shipOrder(this.data.selectedOrder.id, {
        shipping_company: this.data.shippingCompany,
        tracking_number: this.data.trackingNumber.trim(),
        shipping_method: 'express',
        estimated_arrival_days: 3
      });

      wx.hideLoading();
      showToast('发货成功', 'success');
      this.closeShipDialog();

      this.setData({ page: 1, orders: [], hasMore: true });
      await Promise.all([
        this.loadOrders(),
        this.loadOrderStats()
      ]);
    } catch (error) {
      console.error('发货失败:', error);
      wx.hideLoading();
      showToast(error.msg || '发货失败，请重试');
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
      content: '确定要删除该订单吗？删除后无法恢复。',
      success: async (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '删除中...', mask: true });
          try {
            await deleteOrder(orderId);
            wx.hideLoading();
            
            const newOrders = this.data.orders.filter(order => order.id !== orderId);
            this.setData({ orders: newOrders });
            showToast('删除成功', 'success');
          } catch (error) {
            console.error('删除订单失败:', error);
            wx.hideLoading();
            showToast(error.msg || '删除失败，请重试');
          }
        }
      }
    });
  },

  goToProducts() {
    wx.switchTab({
      url: '/pages/products/index'
    });
  },

  formatOrders(orders) {
    return orders.map(order => {
      const formatted = {
        ...order,
        formattedTotalAmount: order.total_amount ? order.total_amount.toFixed(2) : '0.00',
        formattedDiscountAmount: order.discount_amount ? order.discount_amount.toFixed(2) : '0.00',
        formattedPayAmount: order.pay_amount ? order.pay_amount.toFixed(2) : '0.00',
        formattedShippingFee: order.shipping_fee ? order.shipping_fee.toFixed(2) : '0.00',
        hasLogistics: order.logistics && order.logistics.items && order.logistics.items.length > 0,
        hasPriceDetail: order.total_amount > 0 || order.discount_amount > 0 || order.shipping_fee > 0,
        hasAddress: order.address && order.address.name && order.address.phone,
        isPendingAccept: order.status === 'pending_accept',
        statusText: STATUS_TEXT_MAP[order.status] || order.status
      };
      
      if (order.price_detail) {
        formatted.formattedProductAmount = order.price_detail.product_amount ? order.price_detail.product_amount.toFixed(2) : '0.00';
        formatted.formattedPriceDiscount = order.price_detail.discount_amount ? order.price_detail.discount_amount.toFixed(2) : '0.00';
        formatted.formattedPriceShipping = order.price_detail.shipping_fee ? order.price_detail.shipping_fee.toFixed(2) : '0.00';
        formatted.formattedPricePay = order.price_detail.pay_amount ? order.price_detail.pay_amount.toFixed(2) : '0.00';
      }
      
      return formatted;
    });
  },

  toggleOrderDetail(e) {
    const orderId = e.currentTarget.dataset.id;
    const expandedOrders = { ...this.data.expandedOrders };
    expandedOrders[orderId] = !expandedOrders[orderId];
    
    this.setData({
      expandedOrders: expandedOrders
    });
  },

  copyTrackingNumber(e) {
    const trackingNumber = e.currentTarget.dataset.tracking;
    if (trackingNumber) {
      wx.setClipboardData({
        data: trackingNumber,
        success: () => {
          showToast('已复制物流单号', 'success');
        }
      });
    }
  },

  stopPropagation() {
    return;
  }
});
