const { 
  getTeacherReviews, 
  getTeacherReviewStats, 
  getTeacherUnreadStats,
  getTeacherTrendStats,
  markReviewRead,
  markReviewsBatchRead,
  replyReview,
  updateReviewReply,
  getReviewById
} = require('../../api/reviews');
const { getFullImageUrl, showToast } = require('../../utils/util');
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

Page({
  data: {
    teacherId: null,
    isOwner: false,
    currentUser: null,
    
    ratingFilters: RATING_FILTERS,
    replyStatusFilters: REPLY_STATUS_FILTERS,
    sortOptions: SORT_OPTIONS,
    
    currentRating: 'all',
    currentReplyStatus: 'all',
    sortBy: 'newest',
    
    reviews: [],
    selectedReviews: [],
    isSelectMode: false,
    
    stats: {
      total: 0,
      avgRating: 0,
      goodCount: 0,
      mediumCount: 0,
      badCount: 0,
      unread: 0,
      pendingReply: 0
    },
    
    trendStats: {
      trendData: [],
      overallStats: {},
      days: 30
    },
    
    isLoading: false,
    isRefreshing: false,
    isLoadMore: false,
    hasMore: true,
    page: 1,
    pageSize: 10,
    
    showReplyDialog: false,
    replyingReview: null,
    replyContent: '',
    isEditingReply: false,
    
    showStatsDialog: false,
    currentStatTab: 'overview'
  },

  onLoad(options) {
    const { teacherId } = options;
    
    if (!teacherId) {
      showToast('参数错误');
      wx.navigateBack();
      return;
    }

    this.setData({ 
      teacherId: parseInt(teacherId)
    });
    
    this.loadCurrentUser();
  },

  onShow() {
    if (this.data.teacherId && this.data.isOwner) {
      this.loadAllData();
    }
  },

  onPullDownRefresh() {
    this.setData({ isRefreshing: true });
    this.loadAllData().then(() => {
      wx.stopPullDownRefresh();
      this.setData({ isRefreshing: false });
    }).catch(() => {
      wx.stopPullDownRefresh();
      this.setData({ isRefreshing: false });
    });
  },

  onReachBottom() {
    const { hasMore, isLoadMore, isLoading } = this.data;
    if (hasMore && !isLoadMore && !isLoading) {
      this.setData({ isLoadMore: true });
      this.loadReviews();
    }
  },

  async loadCurrentUser() {
    try {
      const token = storage.getToken();
      if (!token) {
        console.log('用户未登录');
        return;
      }
      
      const cachedUser = storage.getUserInfo();
      if (cachedUser) {
        this.setData({ currentUser: cachedUser });
        this.checkIsOwner();
      }
    } catch (error) {
      console.log('获取当前用户信息失败:', error);
    }
  },

  checkIsOwner() {
    const { teacherId, currentUser } = this.data;
    
    if (teacherId && currentUser) {
      const isOwner = teacherId === currentUser.id;
      this.setData({ isOwner: isOwner });
      
      if (isOwner) {
        this.loadAllData();
      } else {
        showToast('您没有权限查看此页面');
        wx.navigateBack();
      }
    }
  },

  async loadAllData() {
    this.setData({ isLoading: true });
    
    try {
      await Promise.all([
        this.loadUnreadStats(),
        this.loadReviewStats(),
        this.loadReviews(true)
      ]);
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      this.setData({ isLoading: false });
    }
  },

  async loadUnreadStats() {
    try {
      const result = await getTeacherUnreadStats(this.data.teacherId);
      if (result) {
        this.setData({
          'stats.unread': result.unread || 0,
          'stats.pendingReply': result.pending_reply || 0,
          'stats.total': result.total || 0
        });
      }
    } catch (error) {
      console.error('加载未读统计失败:', error);
    }
  },

  async loadReviewStats() {
    try {
      const result = await getTeacherReviewStats(this.data.teacherId);
      if (result && result.stats) {
        const stats = result.stats;
        this.setData({
          'stats.avgRating': stats.avg_overall_rating || 0,
          'stats.goodCount': stats.good_count || 0,
          'stats.mediumCount': stats.medium_count || 0,
          'stats.badCount': stats.bad_count || 0
        });
      }
    } catch (error) {
      console.error('加载评价统计失败:', error);
    }
  },

  async loadTrendStats(days = 30) {
    try {
      const result = await getTeacherTrendStats(this.data.teacherId, { days });
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

  processReviews(reviews) {
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

  async loadReviews(isRefresh = false) {
    const { 
      page, 
      pageSize, 
      currentRating, 
      currentReplyStatus,
      sortBy, 
      teacherId, 
      isLoading 
    } = this.data;
    
    if (isLoading && !isRefresh) return;
    
    if (isRefresh) {
      this.setData({ 
        page: 1, 
        reviews: [], 
        hasMore: true, 
        isLoading: true,
        selectedReviews: [],
        isSelectMode: false
      });
    } else {
      this.setData({ isLoading: true });
    }

    let params = {
      page: isRefresh ? 1 : page,
      page_size: pageSize
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
    } else if (sortBy === 'worst') {
      params.min_rating = 0;
      params.max_rating = 5;
    }

    try {
      const result = await getTeacherReviews(teacherId, params);

      if (result) {
        let newReviews = result.list || [];
        
        if (sortBy === 'oldest') {
          newReviews = newReviews.reverse();
        } else if (sortBy === 'worst') {
          newReviews.sort((a, b) => (a.overall_rating || 0) - (b.overall_rating || 0));
        }
        
        newReviews = this.processReviews(newReviews);
        
        this.setData({
          reviews: isRefresh ? newReviews : [...this.data.reviews, ...newReviews],
          hasMore: newReviews.length >= pageSize,
          page: isRefresh ? 2 : this.data.page + 1,
          isLoading: false,
          isRefreshing: false,
          isLoadMore: false
        });
      }
    } catch (error) {
      console.error('加载评价列表失败:', error);
      wx.showToast({
        title: error.msg || error.message || '加载失败',
        icon: 'none'
      });
      this.setData({
        isLoading: false,
        isRefreshing: false,
        isLoadMore: false
      });
    }
  },

  onRatingChange(e) {
    const rating = e.currentTarget.dataset.rating;
    if (rating === this.data.currentRating) return;
    
    this.setData({
      currentRating: rating,
      page: 1,
      reviews: [],
      hasMore: true
    });
    this.loadReviews(true);
  },

  onReplyStatusChange(e) {
    const status = e.currentTarget.dataset.status;
    if (status === this.data.currentReplyStatus) return;
    
    this.setData({
      currentReplyStatus: status,
      page: 1,
      reviews: [],
      hasMore: true
    });
    this.loadReviews(true);
  },

  onSortChange(e) {
    const sort = e.currentTarget.dataset.sort;
    if (sort === this.data.sortBy) return;
    
    this.setData({
      sortBy: sort,
      page: 1,
      reviews: [],
      hasMore: true
    });
    this.loadReviews(true);
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
    const { reviews, selectedReviews } = this.data;
    
    if (selectedReviews.length === reviews.length) {
      this.setData({ selectedReviews: [] });
    } else {
      this.setData({ selectedReviews: reviews.map(r => r.id) });
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
        const { reviews } = this.data;
        const updatedReviews = reviews.map(r => {
          if (selectedReviews.includes(r.id)) {
            return { ...r, is_read: true, isUnread: false };
          }
          return r;
        });
        
        this.setData({
          reviews: updatedReviews,
          selectedReviews: [],
          isSelectMode: false,
          'stats.unread': Math.max(0, this.data.stats.unread - (result.marked_count || selectedReviews.length))
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

  async markReviewAsRead(reviewId) {
    try {
      await markReviewRead(reviewId);
      
      const { reviews } = this.data;
      const updatedReviews = reviews.map(r => {
        if (r.id === reviewId) {
          return { ...r, is_read: true, isUnread: false };
        }
        return r;
      });
      
      this.setData({
        reviews: updatedReviews,
        'stats.unread': Math.max(0, this.data.stats.unread - 1)
      });
    } catch (error) {
      console.error('标记已读失败:', error);
    }
  },

  openReplyDialog(e) {
    const { id, index } = e.currentTarget.dataset;
    const { reviews } = this.data;
    const review = reviews[index];
    
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
        const { reviews } = this.data;
        const updatedReviews = reviews.map(r => {
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
          reviews: updatedReviews,
          'stats.pendingReply': Math.max(0, this.data.stats.pendingReply + pendingReplyChange)
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
              const { reviews } = this.data;
              const updatedReviews = reviews.map(r => {
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
                reviews: updatedReviews,
                'stats.pendingReply': this.data.stats.pendingReply + 1
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

  goToReviewDetail(e) {
    const { id } = e.currentTarget.dataset;
    if (id) {
      this.markReviewAsRead(id);
      wx.navigateTo({
        url: `/pages/review-detail/index?id=${id}`
      });
    }
  },

  goToProductDetail(e) {
    const { id } = e.currentTarget.dataset;
    if (id) {
      wx.navigateTo({
        url: `/pages/work-detail/index?id=${id}`
      });
    }
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

  previewImage(e) {
    const { url, index } = e.currentTarget.dataset;
    const { reviews } = this.data;
    const review = reviews[index];
    const images = review.images || [];
    
    wx.previewImage({
      current: url,
      urls: images
    });
  },

  formatTime(timestamp) {
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

  getTrendChartData() {
    const { trendData } = this.data.trendStats;
    if (!trendData || trendData.length === 0) return null;
    
    const labels = trendData.map(d => d.date.slice(5));
    const ratings = trendData.map(d => d.avg_rating || 0);
    const counts = trendData.map(d => d.count);
    
    return { labels, ratings, counts };
  }
});
