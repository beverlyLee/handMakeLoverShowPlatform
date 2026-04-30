const { getMyRegistrations, getActivityDetail, cancelRegistration } = require('../../api/activities');
const { showToast, DEFAULT_IMAGE, formatDateTime } = require('../../utils/util');
const { getToken } = require('../../utils/storage');

Page({
  data: {
    registrations: [],
    total: 0,
    page: 1,
    size: 10,
    hasNext: true,
    
    isLoading: false,
    isRefreshing: false,
    showEmpty: false,
    
    statusTab: 'all',
    statusTabs: [
      { key: 'all', label: '全部' },
      { key: 'confirmed', label: '已确认' },
      { key: 'pending', label: '待确认' },
      { key: 'cancelled', label: '已取消' }
    ]
  },

  onLoad() {
    console.log('我的活动页面加载');
    this.loadRegistrations(true);
  },

  onShow() {
    console.log('我的活动页面显示');
    if (getToken()) {
      this.loadRegistrations(true);
    }
  },

  onPullDownRefresh() {
    this.setData({ isRefreshing: true });
    this.loadRegistrations(true).then(() => {
      wx.stopPullDownRefresh();
      this.setData({ isRefreshing: false });
    });
  },

  onReachBottom() {
    if (this.data.hasNext && !this.data.isLoading) {
      this.loadRegistrations(false);
    }
  },

  onStatusTabChange(e) {
    const tab = e.currentTarget.dataset.tab;
    if (tab === this.data.statusTab) return;
    
    this.setData({
      statusTab: tab,
      page: 1,
      registrations: [],
      hasNext: true
    });
    this.loadRegistrations(true);
  },

  async loadRegistrations(isRefresh = false) {
    const token = getToken();
    if (!token) {
      showToast('请先登录');
      this.setData({ 
        showEmpty: true,
        isLoading: false
      });
      return;
    }

    if (this.data.isLoading && !isRefresh) return;

    const page = isRefresh ? 1 : this.data.page;
    const { size, statusTab } = this.data;

    this.setData({ isLoading: true });

    try {
      const params = { page, size };
      if (statusTab !== 'all') {
        params.status = statusTab;
      }

      const result = await getMyRegistrations(params);
      
      if (result && result.list) {
        const registrations = isRefresh 
          ? result.list 
          : [...this.data.registrations, ...result.list];
        
        const showEmpty = registrations.length === 0;

        this.setData({
          registrations,
          total: result.total || 0,
          page: page,
          hasNext: result.has_next || false,
          isLoading: false,
          showEmpty
        });
      }
    } catch (error) {
      console.error('加载我的活动失败:', error);
      this.setData({ 
        isLoading: false,
        showEmpty: this.data.registrations.length === 0
      });
    }
  },

  goToActivityDetail(e) {
    const activityId = e.currentTarget.dataset.id;
    if (activityId) {
      wx.navigateTo({
        url: `/pages/activity-detail/index?id=${activityId}`
      });
    }
  },

  goToCommunity() {
    wx.switchTab({
      url: '/pages/community/index'
    });
  },

  async cancelRegistration(e) {
    const registrationId = e.currentTarget.dataset.registrationId;
    const activityId = e.currentTarget.dataset.activityId;
    
    if (!activityId) return;

    wx.showModal({
      title: '确认取消',
      content: '确定要取消报名该活动吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            wx.showLoading({ title: '取消中...' });
            
            await cancelRegistration(activityId);
            
            wx.hideLoading();
            showToast('已取消报名', 'success');
            
            this.loadRegistrations(true);
            
          } catch (error) {
            wx.hideLoading();
            console.error('取消报名失败:', error);
            showToast(error.msg || '取消失败，请重试');
          }
        }
      }
    });
  },

  formatPrice(price) {
    if (price === 0 || price === null || price === undefined) {
      return '免费';
    }
    return `¥${price}`;
  },

  formatTime(timeStr) {
    if (!timeStr) return '';
    return formatDateTime(timeStr, 'MM-DD HH:mm');
  },

  getStatusText(status) {
    const statusMap = {
      'confirmed': '已确认',
      'pending': '待确认',
      'cancelled': '已取消'
    };
    return statusMap[status] || status;
  },

  getStatusClass(status) {
    const classMap = {
      'confirmed': 'status-confirmed',
      'pending': 'status-pending',
      'cancelled': 'status-cancelled'
    };
    return classMap[status] || '';
  },

  canCancel(status) {
    return status === 'confirmed' || status === 'pending';
  }
});
