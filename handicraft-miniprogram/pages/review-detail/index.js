const { getReviewById, likeReview, replyReview, getOrderReview, deleteReview } = require('../../api/reviews');
const storage = require('../../utils/storage');

Page({
  data: {
    reviewId: null,
    review: null,
    isLoading: true,
    productDetailItems: [],
    teacherDetailItems: [],
    logisticsDetailItems: [],
    expandedSection: 'product',
    showReplyInput: false,
    replyContent: '',
    currentUserId: null,
    isOwner: false,
    isTeacher: false
  },

  onLoad(options) {
    const userInfo = storage.getUserInfo();
    if (userInfo && userInfo.id) {
      this.setData({ currentUserId: userInfo.id });
    }
    
    const { id, orderId } = options;
    if (id) {
      this.setData({ reviewId: id });
      this.loadReviewDetail(id);
    } else if (orderId) {
      this.loadOrderReview(orderId);
    } else {
      wx.showToast({
        title: '参数错误',
        icon: 'none'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    }
  },

  async loadReviewDetail(reviewId) {
    this.setData({ isLoading: true });
    try {
      const review = await getReviewById(reviewId);
      if (review) {
        this.setData({
          review: review,
          productDetailItems: review.product_detail_items || [],
          teacherDetailItems: review.teacher_detail_items || [],
          logisticsDetailItems: review.logistics_detail_items || [],
          isLoading: false
        });
        this.checkIsOwner(review);
      } else {
        throw new Error('评价不存在');
      }
    } catch (error) {
      console.error('加载评价详情失败:', error);
      wx.showToast({
        title: error.msg || error.message || '加载失败',
        icon: 'none'
      });
      this.setData({ isLoading: false });
    }
  },

  async loadOrderReview(orderId) {
    this.setData({ isLoading: true });
    try {
      const result = await getOrderReview(orderId);
      if (result.has_review && result.review) {
        const review = result.review;
        this.setData({
          review: review,
          reviewId: review.id,
          productDetailItems: review.product_detail_items || [],
          teacherDetailItems: review.teacher_detail_items || [],
          logisticsDetailItems: review.logistics_detail_items || [],
          isLoading: false
        });
        this.checkIsOwner(review);
      } else {
        throw new Error('该订单暂无评价');
      }
    } catch (error) {
      console.error('加载订单评价失败:', error);
      wx.showToast({
        title: error.msg || error.message || '加载失败',
        icon: 'none'
      });
      this.setData({ isLoading: false });
    }
  },

  checkIsOwner(review) {
    const currentUserId = this.data.currentUserId;
    if (review && currentUserId) {
      const isOwner = review.user_id === currentUserId;
      const isTeacher = review.teacher_id === currentUserId;
      this.setData({ 
        isOwner: isOwner,
        isTeacher: isTeacher
      });
      console.log('判断身份:', {
        reviewUserId: review.user_id,
        reviewTeacherId: review.teacher_id,
        currentUserId: currentUserId,
        isOwner: isOwner,
        isTeacher: isTeacher
      });
    }
  },

  toggleSection(e) {
    const section = e.currentTarget.dataset.section;
    this.setData({
      expandedSection: this.data.expandedSection === section ? null : section
    });
  },

  previewImage(e) {
    const { url } = e.currentTarget.dataset;
    const { review } = this.data;
    const images = review.images || [];
    
    wx.previewImage({
      current: url,
      urls: images
    });
  },

  async handleLike() {
    const { review } = this.data;
    if (!review) return;

    try {
      const result = await likeReview(review.id);
      const newLikeCount = result && result.like_count !== undefined ? result.like_count : (review.like_count || 0) + 1;
      const currentLikeCount = review.like_count || 0;
      const newIsLiked = newLikeCount > currentLikeCount;
      
      this.setData({
        'review.is_liked': newIsLiked,
        'review.like_count': newLikeCount
      });
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

  toggleReplyInput() {
    this.setData({
      showReplyInput: !this.data.showReplyInput
    });
  },

  onReplyInput(e) {
    this.setData({
      replyContent: e.detail.value
    });
  },

  async submitReply() {
    const { review, replyContent } = this.data;
    if (!replyContent.trim()) {
      wx.showToast({
        title: '请输入回复内容',
        icon: 'none'
      });
      return;
    }

    wx.showLoading({ title: '提交中...' });
    try {
      const result = await replyReview(review.id, replyContent.trim());
      wx.hideLoading();
      wx.showToast({
        title: '回复成功',
        icon: 'success'
      });
      
      const replyTime = result && result.reply_time ? result.reply_time : new Date().toISOString();
      const reply = result && result.reply_content ? result.reply_content : replyContent.trim();
      
      this.setData({
        'review.reply_content': reply,
        'review.reply_time': replyTime,
        showReplyInput: false,
        replyContent: ''
      });
    } catch (error) {
      wx.hideLoading();
      console.error('回复失败:', error);
      wx.showToast({
        title: error.msg || error.message || '回复失败',
        icon: 'none'
      });
    }
  },

  handleEdit() {
    const { review } = this.data;
    if (!review) return;
    
    wx.navigateTo({
      url: `/pages/order-review/index?orderId=${review.order_id}&mode=edit`
    });
  },

  handleDelete() {
    const { review } = this.data;
    if (!review) return;
    
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条评价吗？删除后无法恢复。',
      confirmColor: '#795548',
      success: async (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '删除中...' });
          try {
            await deleteReview(review.id);
            wx.hideLoading();
            wx.showToast({
              title: '删除成功',
              icon: 'success'
            });
            setTimeout(() => {
              wx.navigateBack();
            }, 1500);
          } catch (error) {
            wx.hideLoading();
            console.error('删除评价失败:', error);
            wx.showToast({
              title: error.msg || error.message || '删除失败',
              icon: 'none'
            });
          }
        }
      }
    });
  },

  formatTime(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hour}:${minute}`;
  },

  onShareAppMessage() {
    const { review } = this.data;
    return {
      title: '评价详情',
      path: `/pages/review-detail/index?id=${review?.id || ''}`
    };
  }
});
