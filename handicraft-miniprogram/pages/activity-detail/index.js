const { 
  getActivityDetail, 
  registerActivity, 
  cancelRegistration 
} = require('../../api/activities');
const { showToast, formatDateTime, DEFAULT_IMAGE } = require('../../utils/util');
const { getToken } = require('../../utils/storage');

Page({
  data: {
    activityId: null,
    activity: null,
    isLoading: true,
    currentImageIndex: 0,
    
    showRegisterDialog: false,
    registerForm: {
      name: '',
      phone: '',
      remark: ''
    },
    
    isRegistered: false,
    registrationStatus: null,
    
    isFavorited: false,
    favoriteCount: 0,
    
    isUpcoming: false,
    upcomingText: '',
    isUrgent: false
  },

  onLoad(options) {
    console.log('activity-detail onLoad, options:', options);
    const activityId = options.id;
    if (!activityId) {
      showToast('参数错误');
      wx.navigateBack();
      return;
    }

    this.setData({ activityId: parseInt(activityId) });
    this.loadActivityDetail();
  },

  onShow() {
    console.log('activity-detail onShow');
  },

  onShareAppMessage() {
    const activity = this.data.activity;
    return {
      title: (activity && activity.title) || '精彩手工活动',
      path: `/pages/activity-detail/index?id=${this.data.activityId}`
    };
  },

  onShareTimeline() {
    const activity = this.data.activity;
    return {
      title: (activity && activity.title) || '精彩手工活动',
      imageUrl: activity && activity.cover_image ? activity.cover_image : ''
    };
  },

  async loadActivityDetail() {
    console.log('开始加载活动详情, activityId:', this.data.activityId);
    this.setData({ isLoading: true });

    try {
      const activity = await getActivityDetail(this.data.activityId);
      console.log('加载活动详情成功:', activity);
      
      const upcomingInfo = this.checkUpcoming(activity.start_time);
      
      this.setData({
        activity: activity,
        isRegistered: activity.is_registered || false,
        registrationStatus: activity.registration_status || null,
        favoriteCount: activity.favorite_count || 0,
        isUpcoming: upcomingInfo.isUpcoming,
        upcomingText: upcomingInfo.upcomingText,
        isUrgent: upcomingInfo.isUrgent,
        isLoading: false
      });
    } catch (error) {
      console.error('加载活动详情失败:', error);
      this.setData({ isLoading: false });
      showToast('加载失败，请重试');
    }
  },

  checkUpcoming(startTimeStr) {
    if (!startTimeStr) {
      return { isUpcoming: false, upcomingText: '', isUrgent: false };
    }

    const now = new Date();
    const startTime = new Date(startTimeStr);
    const diffMs = startTime - now;
    const diffHours = diffMs / (1000 * 60 * 60);
    const diffDays = diffHours / 24;

    if (diffMs < 0) {
      return { isUpcoming: false, upcomingText: '', isUrgent: false };
    }

    if (diffHours <= 24) {
      const hours = Math.floor(diffHours);
      const minutes = Math.floor((diffHours - hours) * 60);
      if (hours > 0) {
        return { 
          isUpcoming: true, 
          upcomingText: `活动将在 ${hours} 小时${minutes > 0 ? minutes + ' 分钟' : ''}后开始`, 
          isUrgent: true 
        };
      } else {
        return { 
          isUpcoming: true, 
          upcomingText: `活动将在 ${Math.max(1, minutes)} 分钟后开始`, 
          isUrgent: true 
        };
      }
    }

    if (diffDays <= 3) {
      const days = Math.floor(diffDays);
      const hours = Math.floor((diffDays - days) * 24);
      if (days === 0) {
        return { 
          isUpcoming: true, 
          upcomingText: `活动将在今天 ${hours} 小时后开始`, 
          isUrgent: false 
        };
      } else if (days === 1) {
        return { 
          isUpcoming: true, 
          upcomingText: '活动将在明天开始', 
          isUrgent: false 
        };
      } else {
        return { 
          isUpcoming: true, 
          upcomingText: `活动将在 ${days} 天后开始`, 
          isUrgent: false 
        };
      }
    }

    return { isUpcoming: false, upcomingText: '', isUrgent: false };
  },

  onImageChange(e) {
    this.setData({
      currentImageIndex: e.detail.current
    });
  },

  previewImage(e) {
    const current = e.currentTarget.dataset.url;
    const urls = (this.data.activity && this.data.activity.images) || [];
    
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

  goBackList() {
    wx.switchTab({
      url: '/pages/community/index'
    });
  },

  goToHome() {
    wx.switchTab({
      url: '/pages/home/index'
    });
  },

  toggleFavorite() {
    const token = getToken();
    if (!token) {
      showToast('请先登录');
      return;
    }

    showToast('收藏功能开发中');
  },

  showRegisterDialog() {
    const token = getToken();
    if (!token) {
      showToast('请先登录');
      return;
    }

    const { activity, isRegistered } = this.data;
    
    if (isRegistered) {
      showToast('您已报名该活动');
      return;
    }

    if (!activity.is_registration_open) {
      showToast('活动报名已截止');
      return;
    }

    this.setData({ showRegisterDialog: true });
  },

  hideRegisterDialog() {
    this.setData({ showRegisterDialog: false });
  },

  onRegisterInput(e) {
    const field = e.currentTarget.dataset.field;
    const value = e.detail.value;
    
    this.setData({
      [`registerForm.${field}`]: value
    });
  },

  async submitRegistration() {
    const { activityId, registerForm } = this.data;
    
    if (!registerForm.name) {
      showToast('请输入姓名');
      return;
    }
    if (!registerForm.phone) {
      showToast('请输入手机号');
      return;
    }

    try {
      wx.showLoading({ title: '报名中...' });
      
      const result = await registerActivity(activityId, registerForm);
      
      wx.hideLoading();
      
      showToast('报名成功', 'success');
      
      this.setData({
        isRegistered: true,
        registrationStatus: 'confirmed',
        showRegisterDialog: false,
        'activity.is_registered': true,
        'activity.registration_status': 'confirmed',
        'activity.current_participants': (this.data.activity.current_participants || 0) + 1
      });
      
    } catch (error) {
      wx.hideLoading();
      console.error('报名失败:', error);
      showToast(error.msg || '报名失败，请重试');
    }
  },

  async cancelMyRegistration() {
    const { activityId } = this.data;
    
    wx.showModal({
      title: '确认取消',
      content: '确定要取消报名吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            wx.showLoading({ title: '取消中...' });
            
            await cancelRegistration(activityId);
            
            wx.hideLoading();
            
            showToast('已取消报名', 'success');
            
            this.setData({
              isRegistered: false,
              registrationStatus: null,
              'activity.is_registered': false,
              'activity.registration_status': null,
              'activity.current_participants': Math.max(0, (this.data.activity.current_participants || 0) - 1)
            });
            
          } catch (error) {
            wx.hideLoading();
            console.error('取消报名失败:', error);
            showToast(error.msg || '取消失败，请重试');
          }
        }
      }
    });
  },

  contactTeacher() {
    showToast('联系老师功能开发中');
  },

  shareActivity() {
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
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
    return formatDateTime(timeStr, 'YYYY年MM月DD日 HH:mm:ss');
  },

  formatDate(timeStr) {
    if (!timeStr) return '';
    return formatDateTime(timeStr, 'MM月DD日 HH:mm:ss');
  },

  formatTimeRange(startTime, endTime) {
    if (!startTime) return '';
    
    const startFormatted = this.formatTime(startTime);
    
    if (!endTime) {
      return startFormatted;
    }
    
    const endFormatted = this.formatTime(endTime);
    
    if (startFormatted === endFormatted) {
      return startFormatted;
    }
    
    return `${startFormatted} 至 ${endFormatted}`;
  },

  formatShortTimeRange(startTime, endTime) {
    if (!startTime) return '';
    
    const startFormatted = formatDateTime(startTime, 'MM-DD HH:mm');
    
    if (!endTime) {
      return startFormatted;
    }
    
    const endFormatted = formatDateTime(endTime, 'MM-DD HH:mm');
    
    if (startFormatted === endFormatted) {
      return startFormatted;
    }
    
    return `${startFormatted} ~ ${endFormatted}`;
  },

  getRemainingSpots() {
    const { activity } = this.data;
    if (!activity) return 0;
    return Math.max(0, (activity.max_participants || 999) - (activity.current_participants || 0));
  },

  preventBubble() {
    return;
  }
});
