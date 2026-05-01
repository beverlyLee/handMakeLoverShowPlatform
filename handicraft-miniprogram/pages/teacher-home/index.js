const { getTeacherPublicInfo, getTeacherPublicOrderStats, getUserInfo, updateTeacherInfo, updateUserInfo } = require('../../api/users');
const { getProducts, createProduct: createProductApi, getCategories, updateProduct, deleteProduct, submitProductReview, takeProductOffline } = require('../../api/products');
const { getSpecialties } = require('../../api/specialties');
const { uploadImages } = require('../../api/upload');
const { 
  getTeacherReviews, 
  getTeacherReviewStats, 
  getTeacherUnreadStats,
  getTeacherTrendStats,
  markReviewRead,
  markReviewsBatchRead,
  replyReview,
  updateReviewReply
} = require('../../api/reviews');
const { getMyActivities } = require('../../api/activities');
const { batchCheckLikeStatus } = require('../../api/favorites');
const { showToast, processTeacherInfo, processProductImages, getRelativeImageUrl, getFullImageUrl } = require('../../utils/util');
const config = require('../../utils/config');
const storage = require('../../utils/storage');

const RATING_FILTERS = [
  { key: 'all', label: '全部', value: null },
  { key: 'good', label: '好评', minRating: 4.0 },
  { key: 'medium', label: '中评', minRating: 2.0, maxRating: 3.9 },
  { key: 'bad', label: '差评', maxRating: 1.9 }
];

const REPLY_STATUS_FILTERS = [
  { key: 'all', label: '全部状态' },
  { key: 'pending', label: '待回复' },
  { key: 'replied', label: '已回复' }
];

const SORT_OPTIONS = [
  { key: 'newest', label: '最新优先' },
  { key: 'oldest', label: '最早优先' },
  { key: 'best', label: '好评优先' },
  { key: 'worst', label: '差评优先' }
];

const DEFAULT_SPECIALTIES = [
  { label: '棒针编织', value: '棒针编织', checked: false },
  { label: '钩针编织', value: '钩针编织', checked: false },
  { label: '编织', value: '编织', checked: false },
  { label: '陶艺', value: '陶艺', checked: false },
  { label: '拉坯', value: '拉坯', checked: false },
  { label: '釉上彩', value: '釉上彩', checked: false },
  { label: '皮革工艺', value: '皮革工艺', checked: false },
  { label: '刺绣', value: '刺绣', checked: false },
  { label: '纸艺', value: '纸艺', checked: false },
  { label: '珠串', value: '珠串', checked: false },
  { label: '木艺', value: '木艺', checked: false },
  { label: '布艺', value: '布艺', checked: false },
  { label: '手工皂', value: '手工皂', checked: false },
  { label: '蜡烛', value: '蜡烛', checked: false },
  { label: '押花', value: '押花', checked: false },
  { label: '热缩片', value: '热缩片', checked: false },
  { label: '滴胶', value: '滴胶', checked: false },
  { label: '黏土', value: '黏土', checked: false }
];

let specialtyList = [...DEFAULT_SPECIALTIES];

function createSpecialtyOptions(selectedSpecialties = []) {
  return specialtyList.map(option => ({
    ...option,
    checked: selectedSpecialties.indexOf(option.value) > -1
  }));
}

Page({
  data: {
    teacherId: null,
    teacher: null,
    products: [],
    productsTotal: 0,
    orderStats: null,
    recentOrders: [],
    currentTab: 'orders',
    isLoading: true,
    productsLoading: false,
    productsPage: 1,
    productsPageSize: 10,
    productsHasMore: true,
    ordersLoading: false,
    currentUser: null,
    isOwner: false,
    
    specialtyOptions: [],
    
    showEditDialog: false,
    editDialogField: '',
    editDialogTitle: '',
    editDialogValue: '',
    editDialogType: 'input',
    savingEdit: false,
    
    showSpecialtiesDialog: false,
    tempSpecialties: [],
    
    showStudioDialog: false,
    studioEditForm: {
      name: '',
      address: ''
    },
    
    showProductCreate: false,
    categories: [],
    productForm: {
      title: '',
      description: '',
      category_id: null,
      category_name: '',
      price: '',
      original_price: '',
      stock: 999,
      tags: [],
      images: [],
      cover_image: ''
    },
    creatingProduct: false,
    isEditingProduct: false,
    editingProductId: null,

    reviewStats: null,
    reviews: [],
    reviewsLoading: false,
    reviewsPage: 1,
    reviewsPageSize: 3,
    reviewsHasMore: true,
    
    ratingFilters: RATING_FILTERS,
    replyStatusFilters: REPLY_STATUS_FILTERS,
    sortOptions: SORT_OPTIONS,
    
    currentRating: 'all',
    currentReplyStatus: 'all',
    sortBy: 'newest',
    
    reviewManageStats: {
      total: 0,
      avgRating: 0,
      goodCount: 0,
      mediumCount: 0,
      badCount: 0,
      unread: 0,
      pendingReply: 0
    },
    reviewManageList: [],
    selectedReviews: [],
    isSelectMode: false,
    
    trendStats: {
      trendData: [],
      overallStats: {},
      days: 30
    },
    
    reviewManageLoading: false,
    reviewManagePage: 1,
    reviewManagePageSize: 10,
    reviewManageHasMore: true,
    
    showReplyDialog: false,
    replyingReview: null,
    replyContent: '',
    isEditingReply: false,
    
    showStatsDialog: false,
    currentStatTab: 'overview',
    
    orderTimeRange: 'total',
    currentTimeRangeLabel: '全部时间',
    pendingOrders: null,
    dailyTrend: [],
    maxTrendCount: 1,
    pending_reviews_count: 0,
    pending_reply_count: 0,

    activities: [],
    activitiesTotal: 0,
    activitiesLoading: false,
    activitiesPage: 1,
    activitiesPageSize: 10,
    activitiesHasMore: true
  },

  onLoad(options) {
    const teacherId = options.id;
    const tab = options.tab || 'orders';
    
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
    const teacherName = (teacher && teacher.user_info && teacher.user_info.nickname) || (teacher && teacher.real_name) || '手作老师';
    return {
      title: teacherName,
      path: `/pages/teacher-home/index?id=${this.data.teacherId}`
    };
  },

  async loadAllData() {
    this.setData({ isLoading: true });
    
    try {
      await this.loadCurrentUser();
      await this.loadTeacherInfo();
      
      await Promise.all([
        this.loadCategories(),
        this.loadSpecialties(),
        this.loadTeacherProducts()
      ]);
      
      if (this.data.currentTab === 'orders' && this.data.recentOrders.length === 0 && !this.data.orderStats) {
        await this.loadOrderStats();
      }
      
      if (this.data.currentTab === 'reviews') {
        if (this.data.isOwner) {
          if (this.data.reviewManageList.length === 0) {
            await this.loadReviewManageStats();
            await this.loadReviewManageList(true);
          }
        } else {
          if (this.data.reviews.length === 0) {
            await this.loadTeacherReviewStats();
            await this.loadTeacherReviews(false);
          }
        }
      }
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
      const processedTeacher = processTeacherInfo(teacher);
      const specialties = (processedTeacher && processedTeacher.specialties) || [];
      
      this.setData({ 
        teacher: processedTeacher,
        specialtyOptions: createSpecialtyOptions(specialties)
      });
      
      this.checkIsOwner();
    } catch (error) {
      console.error('加载老师信息失败:', error);
      showToast('加载老师信息失败');
    }
  },

  async loadCategories() {
    try {
      const categories = await getCategories();
      this.setData({ categories: categories || [] });
    } catch (error) {
      console.error('加载分类失败:', error);
    }
  },

  async loadSpecialties() {
    try {
      const specialties = await getSpecialties();
      if (specialties && Array.isArray(specialties)) {
        specialtyList = specialties.map(item => ({
          label: item.name,
          value: item.name,
          checked: false
        }));
      }
    } catch (error) {
      console.error('加载擅长领域失败:', error);
      specialtyList = [...DEFAULT_SPECIALTIES];
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
      
      const processedProducts = newProducts.map(p => {
        const processed = processProductImages(p);
        if (processed.is_liked === undefined || processed.is_liked === null) {
          processed.is_liked = false;
        }
        return processed;
      });
      
      const total = (result && result.total) || newProducts.length;
      
      let totalPopularity = 0;
      processedProducts.forEach(p => {
        totalPopularity += p.popularity_score || p.heat_score || 0;
      });

      if (append) {
        const currentTotalPopularity = this.data.totalPopularity || 0;
        this.setData({
          products: [...this.data.products, ...processedProducts],
          productsTotal: total,
          totalPopularity: currentTotalPopularity + totalPopularity,
          productsHasMore: processedProducts.length >= this.data.productsPageSize,
          productsLoading: false
        });
      } else {
        this.setData({
          products: processedProducts,
          productsTotal: total,
          totalPopularity: totalPopularity,
          productsPage: 1,
          productsHasMore: processedProducts.length >= this.data.productsPageSize,
          productsLoading: false
        });
        
        this.refreshLikeStatus();
      }
    } catch (error) {
      console.error('加载老师作品失败:', error);
      this.setData({ productsLoading: false });
      showToast('加载作品失败');
    }
  },

  async refreshLikeStatus() {
    const { products } = this.data;
    if (!products || products.length === 0) return;

    const token = storage.getToken();
    if (!token) {
      console.log('用户未登录，不检查点赞状态');
      return;
    }

    const productIds = products.map(p => p.id);
    if (productIds.length === 0) return;

    try {
      const result = await batchCheckLikeStatus({ product_ids: productIds });
      if (result && Array.isArray(result)) {
        const likeStatusMap = {};
        result.forEach(item => {
          likeStatusMap[item.product_id] = {
            is_liked: item.is_liked,
            like_count: item.like_count,
            popularity_score: item.popularity_score
          };
        });

        const updatedProducts = products.map(product => {
          const likeStatus = likeStatusMap[product.id];
          if (likeStatus) {
            return {
              ...product,
              is_liked: likeStatus.is_liked,
              like_count: likeStatus.like_count,
              popularity_score: likeStatus.popularity_score
            };
          }
          return product;
        });

        this.setData({
          products: updatedProducts
        });
      }
    } catch (error) {
      console.error('检查点赞状态失败:', error);
    }
  },

  onLikeChange(e) {
    const { index } = e.currentTarget.dataset;
    const { isLiked, likeCount, popularityScore } = e.detail;
    
    const products = this.data.products;
    if (products && products[index]) {
      products[index].is_liked = isLiked;
      products[index].like_count = likeCount;
      if (popularityScore !== undefined && popularityScore !== null) {
        products[index].heat_score = popularityScore;
        products[index].popularity_score = popularityScore;
      }
      this.setData({
        products: products
      });
    }
  },

  async loadOrderStats() {
    this.setData({ ordersLoading: true });
    
    try {
      const result = await getTeacherPublicOrderStats(this.data.teacherId);
      
      const dailyTrend = result.daily_trend || [];
      let maxTrendCount = 1;
      dailyTrend.forEach(item => {
        if (item.count > maxTrendCount) {
          maxTrendCount = item.count;
        }
      });
      
      this.setData({
        orderStats: result.stats,
        pendingOrders: result.pending_orders,
        dailyTrend: dailyTrend,
        maxTrendCount: maxTrendCount,
        pending_reviews_count: result.pending_reviews_count || 0,
        pending_reply_count: result.pending_reply_count || 0,
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
    if (tab === 'reviews') {
      if (this.data.isOwner) {
        if (this.data.reviewManageList.length === 0) {
          this.loadAllReviewManageData();
        }
      } else {
        if (this.data.reviews.length === 0) {
          this.loadTeacherReviewStats();
          this.loadTeacherReviews(false);
        }
      }
    }
    if (tab === 'activities' && this.data.activities.length === 0) {
      this.loadTeacherActivities();
    }
  },

  switchTimeRange(e) {
    const range = e.currentTarget.dataset.range;
    if (range === this.data.orderTimeRange) return;
    
    const rangeLabels = {
      'total': '全部时间',
      'today': '今日',
      'week': '本周',
      'month': '本月'
    };
    
    this.setData({
      orderTimeRange: range,
      currentTimeRangeLabel: rangeLabels[range] || '全部时间'
    });
    
    this.updateStatsByTimeRange(range);
  },

  updateStatsByTimeRange(range) {
    const orderStats = this.data.orderStats;
    if (!orderStats) return;
    
    if (range === 'today') {
      const todayStats = {
        ...orderStats,
        total: orderStats.today_orders_count || 0,
        total_amount: orderStats.today_orders_amount || 0
      };
      this.setData({ orderStats: todayStats });
    } else if (range === 'week') {
      const weekStats = {
        ...orderStats,
        total: orderStats.week_orders_count || 0,
        total_amount: orderStats.week_orders_amount || 0
      };
      this.setData({ orderStats: weekStats });
    } else if (range === 'month') {
      const monthStats = {
        ...orderStats,
        total: orderStats.month_orders_count || 0,
        total_amount: orderStats.month_orders_amount || 0
      };
      this.setData({ orderStats: monthStats });
    } else {
      this.loadOrderStats();
    }
  },

  async loadTeacherReviewStats() {
    try {
      const teacher = this.data.teacher;
      if (!teacher || !teacher.user_id) {
        console.log('老师信息未加载，暂不获取评价统计');
        return;
      }
      
      const result = await getTeacherReviewStats(teacher.user_id);
      if (result && result.stats) {
        const stats = {
          ...result.stats,
          avg_rating: result.stats.avg_overall_rating || 0,
          goodCount: result.stats.good_count || 0,
          mediumCount: result.stats.medium_count || 0,
          badCount: result.stats.bad_count || 0
        };
        this.setData({ reviewStats: stats });
      }
    } catch (error) {
      console.error('加载老师评价统计失败:', error);
    }
  },

  async loadTeacherReviews(append = false) {
    const { reviewsPage, reviewsPageSize, reviewsHasMore, reviewsLoading } = this.data;
    const teacher = this.data.teacher;
    
    if (reviewsLoading || !reviewsHasMore) return;
    if (!teacher || !teacher.user_id) {
      console.log('老师信息未加载，暂不获取评价列表');
      return;
    }

    this.setData({ reviewsLoading: true });

    try {
      const result = await getTeacherReviews(teacher.user_id, {
        page: append ? reviewsPage : 1,
        size: reviewsPageSize
      });

      if (result) {
        const newReviews = result.list || [];
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
      console.error('加载老师评价列表失败:', error);
      this.setData({ reviewsLoading: false });
    }
  },

  goToAllReviews() {
    this.setData({ currentTab: 'reviews' });
    if (this.data.reviews.length === 0 && !this.data.isOwner) {
      this.loadTeacherReviewStats();
      this.loadTeacherReviews(false);
    }
  },

  goToReviewManage() {
    this.setData({ currentTab: 'reviews' });
    if (this.data.isOwner && this.data.reviewManageList.length === 0) {
      this.loadAllReviewManageData();
    }
  },

  goToReviewManageWithFilter(e) {
    const filter = e.currentTarget.dataset.filter;
    
    this.setData({ currentTab: 'reviews' });
    
    if (filter === 'pending') {
      this.setData({
        currentReplyStatus: 'pending',
        reviewManagePage: 1,
        reviewManageList: [],
        reviewManageHasMore: true
      });
    }
    
    if (this.data.isOwner) {
      this.loadAllReviewManageData();
    }
  },

  goToReviewStats() {
    this.setData({ currentTab: 'reviews' });
    if (this.data.isOwner) {
      this.loadTrendStats();
      this.setData({ showStatsDialog: true, currentStatTab: 'overview' });
    }
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

  goToEditInfo() {
    wx.navigateTo({
      url: '/pages/teacher-info-edit/index'
    });
  },

  goToEditProfile() {
    showToast('请在当前页面点击编辑按钮');
  },

  goToManage() {
    showToast('管理后台功能开发中');
  },

  goToStats() {
    wx.navigateTo({
      url: `/pages/teacher-stats/index?teacher_id=${this.data.teacherId}`
    });
  },

  goToCreateActivity() {
    wx.navigateTo({
      url: '/pages/activity-create/index'
    });
  },

  previewStudioImage(e) {
    const url = e.currentTarget.dataset.url;
    const images = this.data.teacher.studio_images || [];
    
    wx.previewImage({
      current: url,
      urls: images
    });
  },

  openEditDialog(e) {
    const { field, title, value, type } = e.currentTarget.dataset;
    
    this.setData({
      showEditDialog: true,
      editDialogField: field,
      editDialogTitle: title,
      editDialogValue: value || '',
      editDialogType: type || 'input'
    });
  },

  closeEditDialog() {
    this.setData({
      showEditDialog: false,
      editDialogField: '',
      editDialogTitle: '',
      editDialogValue: '',
      editDialogType: 'input'
    });
  },

  onEditInput(e) {
    const value = e.detail.value;
    this.setData({
      editDialogValue: value
    });
  },

  async saveEditDialog() {
    const { editDialogField, editDialogValue, teacher } = this.data;
    
    if (!editDialogField) return;
    
    this.setData({ savingEdit: true });
    wx.showLoading({ title: '保存中...', mask: true });
    
    try {
      const updateData = {};
      
      if (editDialogField === 'experience_years') {
        updateData[editDialogField] = parseInt(editDialogValue) || 0;
      } else {
        updateData[editDialogField] = editDialogValue;
      }
      
      if (editDialogField === 'nickname') {
        await updateUserInfo(updateData);
        
        const updatedTeacher = {
          ...teacher,
          user_info: {
            ...teacher.user_info,
            nickname: editDialogValue
          }
        };
        
        this.setData({
          teacher: updatedTeacher,
          savingEdit: false
        });
      } else {
        await updateTeacherInfo(updateData);
        
        const updatedTeacher = {
          ...teacher,
          ...updateData
        };
        
        this.setData({
          teacher: updatedTeacher,
          savingEdit: false
        });
      }
      
      wx.hideLoading();
      this.closeEditDialog();
      showToast('保存成功', 'success');
    } catch (error) {
      console.error('保存失败:', error);
      wx.hideLoading();
      this.setData({ savingEdit: false });
      showToast('保存失败，请重试');
    }
  },

  openSpecialtiesEdit() {
    const teacher = this.data.teacher;
    const specialties = (teacher && teacher.specialties) || [];
    
    this.setData({
      showSpecialtiesDialog: true,
      specialtyOptions: createSpecialtyOptions(specialties),
      tempSpecialties: [...specialties]
    });
  },

  closeSpecialtiesDialog() {
    this.setData({
      showSpecialtiesDialog: false
    });
  },

  toggleSpecialtyItem(e) {
    const index = e.currentTarget.dataset.index;
    const specialtyOptions = [...this.data.specialtyOptions];
    const option = specialtyOptions[index];
    
    option.checked = !option.checked;
    
    const selectedSpecialties = specialtyOptions
      .filter(item => item.checked)
      .map(item => item.value);
    
    this.setData({
      specialtyOptions: specialtyOptions,
      tempSpecialties: selectedSpecialties
    });
  },

  async saveSpecialtiesDialog() {
    const { tempSpecialties, teacher } = this.data;
    
    this.setData({ savingEdit: true });
    wx.showLoading({ title: '保存中...', mask: true });
    
    try {
      await updateTeacherInfo({
        specialties: tempSpecialties
      });
      
      const updatedTeacher = {
        ...teacher,
        specialties: tempSpecialties
      };
      
      this.setData({
        teacher: updatedTeacher,
        savingEdit: false
      });
      
      wx.hideLoading();
      this.closeSpecialtiesDialog();
      showToast('保存成功', 'success');
    } catch (error) {
      console.error('保存失败:', error);
      wx.hideLoading();
      this.setData({ savingEdit: false });
      showToast('保存失败，请重试');
    }
  },

  openStudioEdit() {
    const teacher = this.data.teacher;
    
    this.setData({
      showStudioDialog: true,
      studioEditForm: {
        name: (teacher && teacher.studio_name) || '',
        address: (teacher && teacher.studio_address) || ''
      }
    });
  },

  closeStudioDialog() {
    this.setData({
      showStudioDialog: false
    });
  },

  onStudioNameInput(e) {
    const value = e.detail.value;
    this.setData({
      'studioEditForm.name': value
    });
  },

  onStudioAddressInput(e) {
    const value = e.detail.value;
    this.setData({
      'studioEditForm.address': value
    });
  },

  async saveStudioDialog() {
    const { studioEditForm, teacher } = this.data;
    
    this.setData({ savingEdit: true });
    wx.showLoading({ title: '保存中...', mask: true });
    
    try {
      await updateTeacherInfo({
        studio_name: studioEditForm.name,
        studio_address: studioEditForm.address
      });
      
      const updatedTeacher = {
        ...teacher,
        studio_name: studioEditForm.name,
        studio_address: studioEditForm.address
      };
      
      this.setData({
        teacher: updatedTeacher,
        savingEdit: false
      });
      
      wx.hideLoading();
      this.closeStudioDialog();
      showToast('保存成功', 'success');
    } catch (error) {
      console.error('保存失败:', error);
      wx.hideLoading();
      this.setData({ savingEdit: false });
      showToast('保存失败，请重试');
    }
  },

  openProductCreate() {
    this.setData({
      showProductCreate: true,
      isEditingProduct: false,
      editingProductId: null,
      productForm: {
        title: '',
        description: '',
        category_id: null,
        category_name: '',
        price: '',
        original_price: '',
        stock: 999,
        tags: [],
        images: [],
        cover_image: ''
      }
    });
  },

  openProductEdit(e) {
    const product = e.currentTarget.dataset.product;
    if (!product) return;

    const { categories } = this.data;
    let category_name = '';
    if (product.category_id && categories) {
      const cat = categories.find(c => c.id === product.category_id);
      if (cat) {
        category_name = cat.name;
      }
    }

    const processedImages = (product.images || []).map(img => getFullImageUrl(img));
    const processedCoverImage = product.cover_image ? getFullImageUrl(product.cover_image) : '';

    this.setData({
      showProductCreate: true,
      isEditingProduct: true,
      editingProductId: product.id,
      productForm: {
        title: product.title || '',
        description: product.description || '',
        category_id: product.category_id || null,
        category_name: category_name || '',
        price: product.price ? String(product.price) : '',
        original_price: product.original_price ? String(product.original_price) : '',
        stock: product.stock ? String(product.stock) : '999',
        tags: product.tags || [],
        images: processedImages,
        cover_image: processedCoverImage
      }
    });
  },

  closeProductCreate() {
    this.setData({ 
      showProductCreate: false,
      isEditingProduct: false,
      editingProductId: null
    });
  },

  onProductInput(e) {
    const field = e.currentTarget.dataset.field;
    const value = e.detail.value;
    
    this.setData({
      [`productForm.${field}`]: value
    });
  },

  onCategoryChange(e) {
    const index = e.detail.value;
    const categories = this.data.categories;
    
    if (categories && categories[index]) {
      this.setData({
        'productForm.category_id': categories[index].id,
        'productForm.category_name': categories[index].name
      });
    }
  },

  chooseImages() {
    const self = this;
    wx.chooseImage({
      count: 9,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success(res) {
        const tempFilePaths = res.tempFilePaths;
        const currentImages = self.data.productForm.images;
        const newImages = [...currentImages, ...tempFilePaths].slice(0, 9);
        
        self.setData({
          'productForm.images': newImages,
          'productForm.cover_image': newImages[0] || ''
        });
      }
    });
  },

  removeImage(e) {
    const index = e.currentTarget.dataset.index;
    const images = [...this.data.productForm.images];
    images.splice(index, 1);
    
    this.setData({
      'productForm.images': images,
      'productForm.cover_image': images[0] || ''
    });
  },

  async createProduct() {
    const { productForm, teacher, isEditingProduct, editingProductId } = this.data;
    
    if (!productForm.title) {
      showToast('请填写作品标题');
      return;
    }
    if (!productForm.price) {
      showToast('请填写作品价格');
      return;
    }
    
    this.setData({ creatingProduct: true });
    
    try {
      let processedImages = [...productForm.images];
      
      const tempImagePaths = [];
      const serverUrls = [];
      const baseUrl = config.baseUrl.replace('/api', '');
      
      for (const img of processedImages) {
        if (!img) continue;
        
        if (img.startsWith('/api/images/')) {
          serverUrls.push(img);
        } else if (img.startsWith('/uploads/')) {
          serverUrls.push(img);
        } else if (img.startsWith('/') && !img.startsWith('//')) {
          serverUrls.push(img);
        } else if (img.startsWith('http://') || img.startsWith('https://')) {
          if (img.startsWith(baseUrl)) {
            serverUrls.push(img);
          } else if (img.includes('__tmp__') || 
                     img.startsWith('http://tmp/') || 
                     img.startsWith('http://127.0.0.1:') ||
                     img.includes('wxfile://')) {
            tempImagePaths.push(img);
          } else {
            serverUrls.push(img);
          }
        } else if (img.startsWith('wxfile://')) {
          tempImagePaths.push(img);
        } else {
          tempImagePaths.push(img);
        }
      }
      
      console.log('图片分类 - 临时路径:', tempImagePaths, '服务器URL:', serverUrls);
      
      const relativeServerUrls = serverUrls.map(url => getRelativeImageUrl(url));
      console.log('转换为相对路径:', relativeServerUrls);
      
      if (tempImagePaths.length > 0) {
        wx.showLoading({ title: '上传图片中...', mask: true });
        
        const uploadResult = await uploadImages(tempImagePaths, false);
        wx.hideLoading();
        
        console.log('上传结果:', uploadResult);
        
        if (uploadResult.failed > 0) {
          showToast(`有 ${uploadResult.failed} 张图片上传失败`);
          this.setData({ creatingProduct: false });
          return;
        }
        
        processedImages = [...relativeServerUrls, ...uploadResult.urls];
      } else {
        processedImages = [...relativeServerUrls];
      }
      
      const productData = {
        title: productForm.title,
        description: productForm.description,
        category_id: productForm.category_id,
        price: parseFloat(productForm.price) || 0,
        original_price: parseFloat(productForm.original_price) || parseFloat(productForm.price) || 0,
        stock: parseInt(productForm.stock) || 999,
        status: 'active',
        tags: productForm.tags,
        images: processedImages,
        cover_image: processedImages[0] || ''
      };
      
      if (productData.images.length === 0) {
        productData.images = [
          'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=handmade%20craft%20artwork%20elegant%20handcrafted%20product&image_size=square'
        ];
        productData.cover_image = productData.images[0];
      }
      
      if (isEditingProduct && editingProductId) {
        await updateProduct(editingProductId, productData);
        showToast('作品更新成功');
      } else {
        await createProductApi(productData);
        const newProductCount = ((teacher && teacher.product_count) || 0) + 1;
        this.setData({
          'teacher.product_count': newProductCount
        });
        showToast('作品创建成功');
      }
      
      this.setData({
        showProductCreate: false,
        creatingProduct: false,
        isEditingProduct: false,
        editingProductId: null,
        products: [],
        productsPage: 1
      });
      
      this.loadTeacherProducts();
    } catch (error) {
      wx.hideLoading();
      console.error(isEditingProduct ? '更新作品失败:' : '创建作品失败:', error);
      this.setData({ creatingProduct: false });
      showToast(isEditingProduct ? '更新失败，请重试' : '创建失败，请重试');
    }
  },

  deleteProduct(e) {
    const product = e.currentTarget.dataset.product;
    if (!product) return;

    const self = this;
    wx.showModal({
      title: '确认删除',
      content: '确定要删除该作品吗？删除后无法恢复。',
      success: async (res) => {
        if (res.confirm) {
          try {
            await deleteProduct(product.id);
            
            const newProductCount = Math.max(0, ((self.data.teacher && self.data.teacher.product_count) || 1) - 1);
            
            self.setData({
              products: [],
              productsPage: 1,
              'teacher.product_count': newProductCount
            });
            
            self.loadTeacherProducts();
            showToast('作品已删除');
          } catch (error) {
            console.error('删除作品失败:', error);
            showToast('删除失败，请重试');
          }
        }
      }
    });
  },

  submitProductReview(e) {
    const product = e.currentTarget.dataset.product;
    if (!product) return;

    const self = this;
    wx.showModal({
      title: '提交审核',
      content: '确定要提交该作品上架审核吗？审核通过后作品将可被用户浏览和购买。',
      success: async (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '提交中...', mask: true });
          try {
            await submitProductReview(product.id);
            
            self.setData({
              products: [],
              productsPage: 1
            });
            
            self.loadTeacherProducts();
            wx.hideLoading();
            showToast('已提交审核，请等待管理员审核', 'success');
          } catch (error) {
            wx.hideLoading();
            console.error('提交审核失败:', error);
            showToast('提交失败，请重试');
          }
        }
      }
    });
  },

  takeProductOffline(e) {
    const product = e.currentTarget.dataset.product;
    if (!product) return;

    const self = this;
    wx.showModal({
      title: '下架作品',
      content: '确定要下架该作品吗？下架后用户将无法浏览和购买该作品。',
      success: async (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '处理中...', mask: true });
          try {
            await takeProductOffline(product.id);
            
            self.setData({
              products: [],
              productsPage: 1
            });
            
            self.loadTeacherProducts();
            wx.hideLoading();
            showToast('作品已下架', 'success');
          } catch (error) {
            wx.hideLoading();
            console.error('下架作品失败:', error);
            showToast('操作失败，请重试');
          }
        }
      }
    });
  },

  getProductStatusText(verifyStatus, isOnline) {
    if (verifyStatus === 'pending') {
      return '审核中';
    }
    if (verifyStatus === 'rejected') {
      return '已拒绝';
    }
    if (isOnline) {
      return '已上架';
    }
    return '已下架';
  },

  getProductStatusType(verifyStatus, isOnline) {
    if (verifyStatus === 'pending') {
      return 'warning';
    }
    if (verifyStatus === 'rejected') {
      return 'error';
    }
    if (isOnline) {
      return 'success';
    }
    return 'info';
  },

  canSubmitReview(verifyStatus, isOnline) {
    return verifyStatus === 'rejected' || (verifyStatus === 'approved' && !isOnline) || verifyStatus === 'pending';
  },

  canTakeOffline(verifyStatus, isOnline) {
    return verifyStatus === 'approved' && isOnline;
  },

  preventMove() {
    return;
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
  },

  preventBubble() {
    return;
  },

  getRatingText(rating) {
    if (rating >= 4.0) return '好评';
    if (rating >= 2.0) return '中评';
    return '差评';
  },

  getRatingTagClass(rating) {
    if (rating >= 4.0) return 'tag-good';
    if (rating >= 2.0) return 'tag-medium';
    return 'tag-bad';
  },

  onRatingChange(e) {
    const rating = e.currentTarget.dataset.rating;
    if (rating === this.data.currentRating) return;
    
    this.setData({
      currentRating: rating,
      reviewManagePage: 1,
      reviewManageList: [],
      reviewManageHasMore: true
    });
    this.loadReviewManageList(true);
  },

  onReplyStatusChange(e) {
    const status = e.currentTarget.dataset.status;
    if (status === this.data.currentReplyStatus) return;
    
    this.setData({
      currentReplyStatus: status,
      reviewManagePage: 1,
      reviewManageList: [],
      reviewManageHasMore: true
    });
    this.loadReviewManageList(true);
  },

  onSortChange(e) {
    const sort = e.currentTarget.dataset.sort;
    if (sort === this.data.sortBy) return;
    
    this.setData({
      sortBy: sort,
      reviewManagePage: 1,
      reviewManageList: [],
      reviewManageHasMore: true
    });
    this.loadReviewManageList(true);
  },

  toggleSelectMode() {
    this.setData({
      isSelectMode: !this.data.isSelectMode,
      selectedReviews: []
    });
  },

  toggleReviewSelection(e) {
    const { id } = e.currentTarget.dataset;
    const { selectedReviews } = this.data;
    
    const index = selectedReviews.indexOf(id);
    if (index > -1) {
      selectedReviews.splice(index, 1);
    } else {
      selectedReviews.push(id);
    }
    
    this.setData({ selectedReviews: [...selectedReviews] });
  },

  toggleSelectAll() {
    const { reviewManageList, selectedReviews } = this.data;
    
    if (selectedReviews.length === reviewManageList.length) {
      this.setData({ selectedReviews: [] });
    } else {
      this.setData({ selectedReviews: reviewManageList.map(r => r.id) });
    }
  },

  async markSelectedAsRead() {
    const { selectedReviews } = this.data;
    
    if (selectedReviews.length === 0) {
      showToast('请选择要标记的评价');
      return;
    }
    
    wx.showLoading({ title: '标记中...', mask: true });
    
    try {
      const result = await markReviewsBatchRead(selectedReviews);
      
      if (result) {
        const { reviewManageList } = this.data;
        const updatedReviews = reviewManageList.map(r => {
          if (selectedReviews.includes(r.id)) {
            return { ...r, is_read: true, isUnread: false };
          }
          return r;
        });
        
        this.setData({
          reviewManageList: updatedReviews,
          selectedReviews: [],
          isSelectMode: false,
          'reviewManageStats.unread': Math.max(0, this.data.reviewManageStats.unread - (result.marked_count || selectedReviews.length))
        });
        
        wx.hideLoading();
        showToast(`已标记 ${result.marked_count || selectedReviews.length} 条评价为已读`, 'success');
      }
    } catch (error) {
      wx.hideLoading();
      console.error('批量标记已读失败:', error);
      showToast('标记失败，请重试');
    }
  },

  async markReviewAsRead(e) {
    const reviewId = e.currentTarget.dataset.id;
    
    try {
      await markReviewRead(reviewId);
      
      const { reviewManageList } = this.data;
      const updatedReviews = reviewManageList.map(r => {
        if (r.id === reviewId) {
          return { ...r, is_read: true, isUnread: false };
        }
        return r;
      });
      
      this.setData({
        reviewManageList: updatedReviews,
        'reviewManageStats.unread': Math.max(0, this.data.reviewManageStats.unread - 1)
      });
    } catch (error) {
      console.error('标记已读失败:', error);
    }
  },

  openReplyDialog(e) {
    const { id, index } = e.currentTarget.dataset;
    const { reviewManageList } = this.data;
    const review = reviewManageList[index];
    
    if (!review) return;
    
    this.setData({
      showReplyDialog: true,
      replyingReview: review,
      replyContent: review.reply_content || '',
      isEditingReply: !!review.reply_content
    });
  },

  closeReplyDialog() {
    this.setData({
      showReplyDialog: false,
      replyingReview: null,
      replyContent: '',
      isEditingReply: false
    });
  },

  onReplyInput(e) {
    this.setData({ replyContent: e.detail.value });
  },

  async submitReply() {
    const { replyingReview, replyContent, isEditingReply } = this.data;
    
    if (!replyingReview) return;
    
    if (!replyContent.trim() && !isEditingReply) {
      showToast('请输入回复内容');
      return;
    }
    
    wx.showLoading({ title: isEditingReply ? '更新中...' : '发送中...', mask: true });
    
    try {
      let result;
      
      if (isEditingReply) {
        result = await updateReviewReply(replyingReview.id, replyContent.trim());
      } else {
        result = await replyReview(replyingReview.id, replyContent.trim());
      }
      
      if (result) {
        const { reviewManageList } = this.data;
        const updatedReviews = reviewManageList.map(r => {
          if (r.id === replyingReview.id) {
            return {
              ...r,
              reply_content: replyContent.trim() || null,
              reply: replyContent.trim() || null,
              reply_time: result.reply_time || new Date().toISOString(),
              isPendingReply: !replyContent.trim()
            };
          }
          return r;
        });
        
        let pendingReplyChange = 0;
        if (isEditingReply) {
          if (!replyingReview.reply_content && replyContent.trim()) {
            pendingReplyChange = -1;
          } else if (replyingReview.reply_content && !replyContent.trim()) {
            pendingReplyChange = 1;
          }
        } else {
          pendingReplyChange = -1;
        }
        
        this.setData({
          reviewManageList: updatedReviews,
          'reviewManageStats.pendingReply': Math.max(0, this.data.reviewManageStats.pendingReply + pendingReplyChange)
        });
        
        wx.hideLoading();
        this.closeReplyDialog();
        showToast(isEditingReply ? '回复已更新' : '回复已发送', 'success');
      }
    } catch (error) {
      wx.hideLoading();
      console.error('提交回复失败:', error);
      showToast(error.msg || error.message || '提交失败，请重试');
    }
  },

  async cancelReply() {
    const { replyingReview } = this.data;
    
    if (!replyingReview || !replyingReview.reply_content) return;
    
    wx.showModal({
      title: '确认撤销',
      content: '确定要撤销这条回复吗？撤销后用户将无法看到。',
      success: async (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '撤销中...', mask: true });
          
          try {
            const result = await updateReviewReply(replyingReview.id, '');
            
            if (result) {
              const { reviewManageList } = this.data;
              const updatedReviews = reviewManageList.map(r => {
                if (r.id === replyingReview.id) {
                  return {
                    ...r,
                    reply_content: null,
                    reply: null,
                    reply_time: null,
                    isPendingReply: true
                  };
                }
                return r;
              });
              
              this.setData({
                reviewManageList: updatedReviews,
                'reviewManageStats.pendingReply': this.data.reviewManageStats.pendingReply + 1
              });
              
              wx.hideLoading();
              this.closeReplyDialog();
              showToast('回复已撤销', 'success');
            }
          } catch (error) {
            wx.hideLoading();
            console.error('撤销回复失败:', error);
            showToast('撤销失败，请重试');
          }
        }
      }
    });
  },

  openStatsDialog() {
    this.loadTrendStats();
    this.setData({ showStatsDialog: true, currentStatTab: 'overview' });
  },

  closeStatsDialog() {
    this.setData({ showStatsDialog: false });
  },

  onStatTabChange(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ currentStatTab: tab });
    
    if (tab === 'trend' && this.data.trendStats.trendData.length === 0) {
      this.loadTrendStats();
    }
  },

  onTrendDaysChange(e) {
    const days = parseInt(e.currentTarget.dataset.days);
    this.loadTrendStats(days);
  },

  async loadTrendStats(days = 30) {
    try {
      const teacher = this.data.teacher;
      if (!teacher || !teacher.user_id) return;
      
      const result = await getTeacherTrendStats(teacher.user_id, { days });
      if (result) {
        this.setData({
          'trendStats.trendData': result.trend_data || [],
          'trendStats.overallStats': result.overall_stats || {},
          'trendStats.days': result.days || days
        });
      }
    } catch (error) {
      console.error('加载趋势统计失败:', error);
    }
  },

  async loadReviewManageStats() {
    try {
      const teacher = this.data.teacher;
      if (!teacher || !teacher.user_id) return;
      
      const unreadResult = await getTeacherUnreadStats(teacher.user_id);
      const statsResult = await getTeacherReviewStats(teacher.user_id);
      
      let updates = {};
      
      if (unreadResult) {
        updates['reviewManageStats.unread'] = unreadResult.unread || 0;
        updates['reviewManageStats.pendingReply'] = unreadResult.pending_reply || 0;
        updates['reviewManageStats.total'] = unreadResult.total || 0;
      }
      
      if (statsResult && statsResult.stats) {
        const stats = statsResult.stats;
        updates['reviewManageStats.avgRating'] = stats.avg_overall_rating || 0;
        updates['reviewManageStats.goodCount'] = stats.good_count || 0;
        updates['reviewManageStats.mediumCount'] = stats.medium_count || 0;
        updates['reviewManageStats.badCount'] = stats.bad_count || 0;
      }
      
      this.setData(updates);
    } catch (error) {
      console.error('加载评价管理统计失败:', error);
    }
  },

  processReviewManageList(reviews) {
    if (!reviews || !Array.isArray(reviews)) return [];
    
    return reviews.map(review => {
      const processed = { ...review };
      
      if (processed.user_avatar && !processed.is_anonymous) {
        processed.user_avatar = getFullImageUrl(processed.user_avatar);
      }
      
      if (processed.images && Array.isArray(processed.images)) {
        processed.images = processed.images.map(img => getFullImageUrl(img));
      }
      
      if (processed.product_info && processed.product_info.cover_image) {
        processed.product_info.cover_image = getFullImageUrl(processed.product_info.cover_image);
      }
      
      processed.isPendingReply = !processed.reply_content;
      processed.isUnread = !processed.is_read;
      
      return processed;
    });
  },

  async loadReviewManageList(isRefresh = false) {
    const { 
      reviewManagePage, 
      reviewManagePageSize, 
      currentRating, 
      currentReplyStatus,
      sortBy, 
      teacher, 
      reviewManageLoading 
    } = this.data;
    
    if (reviewManageLoading && !isRefresh) return;
    if (!teacher || !teacher.user_id) return;
    
    if (isRefresh) {
      this.setData({ 
        reviewManagePage: 1, 
        reviewManageList: [], 
        reviewManageHasMore: true, 
        reviewManageLoading: true,
        selectedReviews: [],
        isSelectMode: false
      });
    } else {
      this.setData({ reviewManageLoading: true });
    }

    let params = {
      page: isRefresh ? 1 : reviewManagePage,
      page_size: reviewManagePageSize
    };

    const ratingFilter = RATING_FILTERS.find(f => f.key === currentRating);
    if (ratingFilter) {
      if (ratingFilter.minRating !== undefined) {
        params.min_rating = ratingFilter.minRating;
      }
      if (ratingFilter.maxRating !== undefined) {
        params.max_rating = ratingFilter.maxRating;
      }
    }

    if (currentReplyStatus === 'pending') {
      params.has_reply = false;
    } else if (currentReplyStatus === 'replied') {
      params.has_reply = true;
    }

    if (sortBy === 'best') {
      params.sort_by = 'best';
    }

    try {
      const result = await getTeacherReviews(teacher.user_id, params);

      if (result) {
        let newReviews = result.list || [];
        
        if (sortBy === 'oldest') {
          newReviews = newReviews.reverse();
        } else if (sortBy === 'worst') {
          newReviews.sort((a, b) => (a.overall_rating || 0) - (b.overall_rating || 0));
        }
        
        newReviews = this.processReviewManageList(newReviews);
        
        this.setData({
          reviewManageList: isRefresh ? newReviews : [...this.data.reviewManageList, ...newReviews],
          reviewManageHasMore: newReviews.length >= reviewManagePageSize,
          reviewManagePage: isRefresh ? 2 : this.data.reviewManagePage + 1,
          reviewManageLoading: false
        });
      }
    } catch (error) {
      console.error('加载评价管理列表失败:', error);
      wx.showToast({
        title: error.msg || error.message || '加载失败',
        icon: 'none'
      });
      this.setData({
        reviewManageLoading: false
      });
    }
  },

  loadAllReviewManageData() {
    this.loadReviewManageStats();
    this.loadReviewManageList(true);
  },

  async loadTeacherActivities(append = false) {
    const { activitiesPage, activitiesPageSize, activitiesHasMore, activitiesLoading } = this.data;
    
    if (activitiesLoading && !append) return;
    if (!this.data.isOwner) {
      this.setData({ activitiesLoading: false });
      return;
    }

    this.setData({ activitiesLoading: true });

    try {
      const result = await getMyActivities({
        page: append ? activitiesPage : 1,
        size: activitiesPageSize
      });

      if (result) {
        const newActivities = result.list || result || [];
        const total = result.total || newActivities.length;
        
        if (append) {
          this.setData({
            activities: [...this.data.activities, ...newActivities],
            activitiesTotal: total,
            activitiesHasMore: newActivities.length >= activitiesPageSize,
            activitiesPage: activitiesPage + 1,
            activitiesLoading: false
          });
        } else {
          this.setData({
            activities: newActivities,
            activitiesTotal: total,
            activitiesPage: 2,
            activitiesHasMore: newActivities.length >= activitiesPageSize,
            activitiesLoading: false
          });
        }
      }
    } catch (error) {
      console.error('加载老师活动列表失败:', error);
      this.setData({ activitiesLoading: false });
    }
  },

  goToActivityDetail(e) {
    const activityId = e.currentTarget.dataset.id;
    if (activityId) {
      wx.navigateTo({
        url: `/pages/activity-detail/index?id=${activityId}`
      });
    }
  }
});