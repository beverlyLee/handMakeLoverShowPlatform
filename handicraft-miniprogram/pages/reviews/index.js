const { getReviews, likeReview, getProductReviews, getTeacherReviews } = require('../../api/reviews');

const FILTER_TYPES = [
  { key: 'all', label: '全部' },
  { key: 'product', label: '商品评价' },
  { key: 'teacher', label: '老师评价' },
  { key: 'logistics', label: '物流评价' }
];

const RATING_FILTERS = [
  { key: 'all', label: '全部评分' },
  { key: 'good', label: '好评 (≥4分)' },
  { key: 'medium', label: '中评 (2-3.9分)' },
  { key: 'bad', label: '差评 (<2分)' }
];

Page({
  data: {
    filterTypes: FILTER_TYPES,
    ratingFilters: RATING_FILTERS,
    currentType: 'all',
    currentRating: 'all',
    reviews: [],
    isLoading: true,
    isRefreshing: false,
    isLoadMore: false,
    hasMore: true,
    page: 1,
    pageSize: 10,
    source: 'user',
    productId: null,
    teacherUserId: null,
    stats: {
      total: 0,
      avgRating: 0,
      goodCount: 0,
      mediumCount: 0,
      badCount: 0
    }
  },

  onLoad(options) {
    const { source, productId, teacherUserId, type } = options;
    
    let currentType = 'all';
    if (type === 'product') currentType = 'product';
    else if (type === 'teacher') currentType = 'teacher';
    else if (type === 'logistics') currentType = 'logistics';

    this.setData({
      source: source || 'user',
      productId: productId || null,
      teacherUserId: teacherUserId || null,
      currentType
    });

    this.loadReviews();
  },

  onShow() {
    if (this.data.reviews.length === 0) {
      this.loadReviews();
    }
  },

  async loadReviews(isRefresh = false) {
    const { page, pageSize, currentType, currentRating, source, productId, teacherUserId } = this.data;
    
    if (isRefresh) {
      this.setData({ page: 1, reviews: [], hasMore: true });
    }

    let params = {
      page: isRefresh ? 1 : page,
      page_size: pageSize
    };

    if (currentRating === 'good') {
      params.min_rating = 4.0;
    } else if (currentRating === 'medium') {
      params.min_rating = 2.0;
      params.max_rating = 3.9;
    } else if (currentRating === 'bad') {
      params.max_rating = 1.9;
    }

    try {
      let result;
      
      if (source === 'product' && productId) {
        result = await getProductReviews(productId, params);
      } else if (source === 'teacher' && teacherUserId) {
        result = await getTeacherReviews(teacherUserId, params);
      } else {
        result = await getReviews(params);
      }

      if (result) {
        const newReviews = result.list || [];
        const total = result.total || 0;
        
        this.setData({
          reviews: isRefresh ? newReviews : [...this.data.reviews, ...newReviews],
          hasMore: newReviews.length >= pageSize,
          page: isRefresh ? 2 : this.data.page + 1,
          isLoading: false,
          isRefreshing: false,
          isLoadMore: false
        });

        if (result.stats) {
          this.setData({ stats: result.stats });
        }
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

  onPullDownRefresh() {
    this.setData({ isRefreshing: true });
    this.loadReviews(true).then(() => {
      wx.stopPullDownRefresh();
    }).catch(() => {
      wx.stopPullDownRefresh();
    });
  },

  onReachBottom() {
    const { hasMore, isLoadMore, isLoading } = this.data;
    if (hasMore && !isLoadMore && !isLoading) {
      this.setData({ isLoadMore: true });
      this.loadReviews();
    }
  },

  onTypeChange(e) {
    const type = e.currentTarget.dataset.type;
    if (type === this.data.currentType) return;
    
    this.setData({
      currentType: type,
      page: 1,
      reviews: [],
      hasMore: true,
      isLoading: true
    });
    this.loadReviews(true);
  },

  onRatingChange(e) {
    const rating = e.currentTarget.dataset.rating;
    if (rating === this.data.currentRating) return;
    
    this.setData({
      currentRating: rating,
      page: 1,
      reviews: [],
      hasMore: true,
      isLoading: true
    });
    this.loadReviews(true);
  },

  goToReviewDetail(e) {
    const { id, orderId } = e.currentTarget.dataset;
    if (id) {
      wx.navigateTo({
        url: `/pages/review-detail/index?id=${id}`
      });
    } else if (orderId) {
      wx.navigateTo({
        url: `/pages/review-detail/index?orderId=${orderId}`
      });
    }
  },

  async handleLike(e) {
    const { id, index } = e.currentTarget.dataset;
    const { reviews } = this.data;
    const review = reviews[index];
    
    if (!review) return;

    try {
      const result = await likeReview(id);
      const newLikeCount = result && result.like_count !== undefined ? result.like_count : (review.like_count || 0) + 1;
      const currentLikeCount = review.like_count || 0;
      const newIsLiked = newLikeCount > currentLikeCount;
      
      reviews[index] = {
        ...review,
        is_liked: newIsLiked,
        like_count: newLikeCount
      };
      this.setData({ reviews });
      wx.showToast({
        title: newIsLiked ? '点赞成功' : '已取消点赞',
        icon: 'none'
      });
    } catch (error) {
      console.error('点赞失败:', error);
      wx.showToast({
        title: error.msg || error.message || '操作失败',
        icon: 'none'
      });
    }
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
    
    if (diff < 60000) {
      return '刚刚';
    }
    if (diff < 3600000) {
      return `${Math.floor(diff / 60000)}分钟前`;
    }
    if (diff < 86400000) {
      return `${Math.floor(diff / 3600000)}小时前`;
    }
    if (diff < 604800000) {
      return `${Math.floor(diff / 86400000)}天前`;
    }
    
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
  }
});
