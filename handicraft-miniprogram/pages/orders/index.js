const { getOrders, payOrder, cancelOrder, confirmOrder } = require('../../api/orders');
const { showToast } = require('../../utils/util');

Page({
  data: {
    orderTabs: [
      { label: '全部', value: '' },
      { label: '待付款', value: 'pending' },
      { label: '待发货', value: 'paid' },
      { label: '待收货', value: 'shipped' },
      { label: '已完成', value: 'completed' }
    ],
    currentTab: '',
    orders: [],
    page: 1,
    pageSize: 10,
    hasMore: true,
    isLoading: false
  },

  onLoad(options) {
    if (options.status) {
      this.setData({
        currentTab: options.status
      });
    }
    this.loadOrders();
  },

  onShow() {
    this.setData({
      page: 1,
      orders: [],
      hasMore: true
    });
    this.loadOrders();
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

  async loadOrders(append = false) {
    if (this.data.isLoading) return;

    this.setData({ isLoading: true });

    try {
      const params = {
        page: this.data.page,
        size: this.data.pageSize
      };

      if (this.data.currentTab) {
        params.status = this.data.currentTab;
      }

      const result = await getOrders(params);
      const newOrders = result?.list || result || [];

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
