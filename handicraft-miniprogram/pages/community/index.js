const { 
  getActivityTypes, 
  getLatestActivities, 
  getActivities 
} = require('../../api/activities');
const { showToast, DEFAULT_IMAGE, formatDateTime } = require('../../utils/util');

Page({
  data: {
    defaultImage: DEFAULT_IMAGE,
    
    bannerActivities: [],
    currentBannerIndex: 0,
    autoplayInterval: 3000,
    
    craftTypes: [],
    activityTypes: [],
    selectedCraftType: '全部',
    selectedActivityType: '全部',
    
    activities: [],
    total: 0,
    page: 1,
    size: 10,
    hasNext: true,
    
    isLoading: false,
    isRefreshing: false,
    isLoadingMore: false,
    showEmpty: false,
    
    showTypeTabs: false
  },

  onLoad() {
    console.log('手工圈页面加载完成');
    this.initPage();
  },

  onReady() {
    console.log('手工圈页面渲染完成');
  },

  onShow() {
    console.log('手工圈页面显示');
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setSelected(2);
    }
  },

  onHide() {
    console.log('手工圈页面隐藏');
  },

  onUnload() {
    console.log('手工圈页面卸载');
  },

  onPullDownRefresh() {
    this.setData({ isRefreshing: true });
    this.refreshData().then(() => {
      wx.stopPullDownRefresh();
      this.setData({ isRefreshing: false });
    });
  },

  onReachBottom() {
    if (this.data.hasNext && !this.data.isLoadingMore) {
      this.loadMoreActivities();
    }
  },

  async initPage() {
    try {
      await this.loadActivityTypes();
      await this.loadBannerActivities();
      await this.loadActivities(true);
    } catch (error) {
      console.error('页面初始化失败:', error);
    }
  },

  async refreshData() {
    try {
      await this.loadBannerActivities();
      await this.loadActivities(true);
    } catch (error) {
      console.error('刷新数据失败:', error);
    }
  },

  async loadActivityTypes() {
    try {
      const result = await getActivityTypes();
      if (result) {
        const craftTypes = ['全部', ...(result.craft_types || [])];
        const activityTypes = ['全部', ...(result.activity_types || [])];
        this.setData({
          craftTypes,
          activityTypes
        });
      }
    } catch (error) {
      console.error('加载活动类型失败:', error);
      this.setData({
        craftTypes: ['全部', '编织', '陶艺', '刺绣', '皮具', '其他'],
        activityTypes: ['全部', '线下体验', '线上课程', '讲座', '工作坊', '其他']
      });
    }
  },

  async loadBannerActivities() {
    try {
      const result = await getLatestActivities({ limit: 5 });
      const activities = result || [];
      
      this.setData({
        bannerActivities: activities,
        currentBannerIndex: 0
      });
    } catch (error) {
      console.error('加载轮播活动失败:', error);
      this.setData({ bannerActivities: [] });
    }
  },

  async loadActivities(isRefresh = false) {
    if (this.data.isLoading && !isRefresh) return;

    const page = isRefresh ? 1 : this.data.page;
    const { size, selectedCraftType, selectedActivityType } = this.data;

    this.setData({ 
      isLoading: true,
      isLoadingMore: !isRefresh && page > 1
    });

    try {
      const params = { page, size };
      
      if (selectedCraftType && selectedCraftType !== '全部') {
        params.craft_type = selectedCraftType;
      }
      if (selectedActivityType && selectedActivityType !== '全部') {
        params.activity_type = selectedActivityType;
      }

      const result = await getActivities(params);
      
      if (result && result.list) {
        const activities = isRefresh 
          ? result.list 
          : [...this.data.activities, ...result.list];
        
        const showEmpty = activities.length === 0;

        this.setData({
          activities,
          total: result.total || 0,
          page: page,
          hasNext: result.has_next || false,
          isLoading: false,
          isLoadingMore: false,
          showEmpty
        });
      }
    } catch (error) {
      console.error('加载活动列表失败:', error);
      this.setData({ 
        isLoading: false,
        isLoadingMore: false,
        showEmpty: this.data.activities.length === 0
      });
      showToast('加载失败，请重试');
    }
  },

  async loadMoreActivities() {
    if (this.data.isLoadingMore || !this.data.hasNext) return;

    const nextPage = this.data.page + 1;
    this.setData({ page: nextPage });
    await this.loadActivities(false);
  },

  onCraftTypeChange(e) {
    const craftType = e.currentTarget.dataset.type;
    if (craftType === this.data.selectedCraftType) return;

    this.setData({
      selectedCraftType: craftType,
      page: 1,
      activities: [],
      hasNext: true
    });
    
    this.loadActivities(true);
  },

  onActivityTypeChange(e) {
    const activityType = e.currentTarget.dataset.type;
    if (activityType === this.data.selectedActivityType) return;

    this.setData({
      selectedActivityType: activityType,
      page: 1,
      activities: [],
      hasNext: true
    });
    
    this.loadActivities(true);
  },

  onBannerChange(e) {
    const current = e.detail.current;
    this.setData({ currentBannerIndex: current });
  },

  onBannerClick(e) {
    const activityId = e.currentTarget.dataset.id;
    if (activityId) {
      this.goToActivityDetail(activityId);
    }
  },

  onActivityCardClick(e) {
    const activityId = e.currentTarget.dataset.id;
    this.goToActivityDetail(activityId);
  },

  goToActivityDetail(activityId) {
    wx.navigateTo({
      url: `/pages/activity-detail/index?id=${activityId}`
    });
  },

  goToHome() {
    wx.switchTab({
      url: '/pages/home/index'
    });
  },

  goToTeacherHome() {
    wx.switchTab({
      url: '/pages/teacher-home/index'
    });
  },

  goToMyActivities() {
    wx.navigateTo({
      url: '/pages/my-activities/index'
    });
  },

  toggleTypeTabs() {
    this.setData({
      showTypeTabs: !this.data.showTypeTabs
    });
  },

  hideTypeTabs() {
    this.setData({
      showTypeTabs: false
    });
  },

  preventBubble() {
    return;
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
  }
});
