const { getReviewById, likeReview, replyReview, getOrderReview, deleteReview, appendReview, deleteAppendReview } = require('../../api/reviews');
const { getFullImageUrl } = require('../../utils/util');
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
    isTeacher: false,
    showAppendInput: false,
    appendContent: '',
    appendImages: [],
    isSubmitting: false,
    processedAppendImages: []
  },

  processAppendReview(appendReview, currentUserId) {
    if (!appendReview) return appendReview;
    
    const processed = { ...appendReview };
    
    if (processed.user_avatar) {
      processed.user_avatar = getFullImageUrl(processed.user_avatar);
    }
    
    if (processed.images && Array.isArray(processed.images)) {
      processed.images = processed.images.map(img => getFullImageUrl(img));
    }
    
    if (currentUserId) {
      processed.is_owner = String(processed.user_id) === String(currentUserId);
    }
    
    return processed;
  },

  processReviewData(review) {
    if (!review) return review;
    
    const processed = { ...review };
    const currentUserId = this.data.currentUserId;
    
    if (processed.user_avatar && !processed.is_anonymous) {
      processed.user_avatar = getFullImageUrl(processed.user_avatar);
    }
    
    if (processed.images && Array.isArray(processed.images)) {
      processed.images = processed.images.map(img => getFullImageUrl(img));
    }
    
    if (processed.append_images && Array.isArray(processed.append_images)) {
      processed.append_images = processed.append_images.map(img => getFullImageUrl(img));
    }
    
    if (processed.append_reviews && Array.isArray(processed.append_reviews)) {
      processed.append_reviews = processed.append_reviews.map(ar => 
        this.processAppendReview(ar, currentUserId)
      );
    }
    
    return processed;
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

  onShow() {
    const pages = getCurrentPages();
    const currentPage = pages[pages.length - 1];
    this.setData({
      currentPageIndex: pages.length - 1
    });
  },

  async loadReviewDetail(reviewId) {
    this.setData({ isLoading: true });
    try {
      const review = await getReviewById(reviewId);
      if (review) {
        const processedReview = this.processReviewData(review);
        this.setData({
          review: processedReview,
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
        const processedReview = this.processReviewData(review);
        this.setData({
          review: processedReview,
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
      const isOwner = String(review.user_id) === String(currentUserId);
      const isTeacher = String(review.teacher_id) === String(currentUserId);
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

  previewAppendImage(e) {
    const { url } = e.currentTarget.dataset;
    const { review } = this.data;
    const images = review.append_images || [];
    
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
        title: '追加评论成功',
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
      console.error('追加评论失败:', error);
      wx.showToast({
        title: error.msg || error.message || '提交失败',
        icon: 'none'
      });
    }
  },

  handleAppendReview() {
    const { review } = this.data;
    if (!review) return;
    
    this.setData({
      showAppendInput: true,
      appendContent: '',
      appendImages: [],
      processedAppendImages: []
    });
  },

  toggleAppendInput() {
    this.setData({
      showAppendInput: !this.data.showAppendInput
    });
  },

  onAppendContentInput(e) {
    this.setData({
      appendContent: e.detail.value
    });
  },

  chooseAppendImages() {
    const { appendImages } = this.data;
    const remaining = 9 - appendImages.length;
    
    if (remaining <= 0) {
      wx.showToast({
        title: '最多上传9张图片',
        icon: 'none'
      });
      return;
    }
    
    wx.chooseImage({
      count: remaining,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const newImages = [...appendImages, ...res.tempFilePaths];
        this.setData({
          appendImages: newImages.slice(0, 9)
        });
      }
    });
  },

  removeAppendImage(e) {
    const index = e.currentTarget.dataset.index;
    const { appendImages } = this.data;
    appendImages.splice(index, 1);
    this.setData({ appendImages });
  },

  previewAppendInputImage(e) {
    const { url } = e.currentTarget.dataset;
    const { appendImages } = this.data;
    
    wx.previewImage({
      current: url,
      urls: appendImages
    });
  },

  async submitAppendReview() {
    const { review, appendContent, appendImages, isSubmitting } = this.data;
    
    if (isSubmitting) return;
    
    if (!appendContent.trim()) {
      wx.showToast({
        title: '请输入追加评论内容',
        icon: 'none'
      });
      return;
    }
    
    wx.showLoading({ title: '提交中...' });
    this.setData({ isSubmitting: true });
    
    try {
      const result = await appendReview(review.id, appendContent.trim(), appendImages);
      wx.hideLoading();
      
      wx.showToast({
        title: '追加评论成功',
        icon: 'success'
      });
      
      const processedResult = this.processReviewData(result);
      
      this.setData({
        showAppendInput: false,
        isSubmitting: false,
        appendContent: '',
        appendImages: [],
        'review.append_reviews': processedResult.append_reviews
      });
      
    } catch (error) {
      wx.hideLoading();
      this.setData({ isSubmitting: false });
      console.error('追加评论失败:', error);
      wx.showToast({
        title: error.msg || error.message || '提交失败',
        icon: 'none'
      });
    }
  },

  handleDelete() {
    const { review, currentPageIndex } = this.data;
    if (!review) return;
    
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条评价吗？删除后无法恢复，相关的追加评论也会被删除。',
      confirmColor: '#795548',
      success: async (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '删除中...' });
          try {
            await deleteReview(review.id);
            wx.hideLoading();
            
            const pages = getCurrentPages();
            for (let i = pages.length - 2; i >= 0; i--) {
              const prevPage = pages[i];
              
              if (prevPage.loadReviewStats && prevPage.loadReviews) {
                prevPage.loadReviewStats();
                prevPage.loadReviews(true);
              }
              
              if (prevPage.loadReviews) {
                prevPage.loadReviews(true);
              }
            }
            
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

  handleDeleteAppend(e) {
    const { review, currentUserId } = this.data;
    const { appendReviewId, userId } = e.currentTarget.dataset;
    
    if (!review) return;
    
    if (String(userId) !== String(currentUserId)) {
      wx.showToast({
        title: '只能删除自己的追加评论',
        icon: 'none'
      });
      return;
    }
    
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条追加评论吗？删除后无法恢复。',
      confirmColor: '#795548',
      success: async (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '删除中...' });
          try {
            const result = await deleteAppendReview(appendReviewId);
            wx.hideLoading();
            
            if (result) {
              const processedResult = this.processReviewData(result);
              this.setData({
                'review.append_reviews': processedResult.append_reviews
              });
            } else {
              const appendReviews = (review.append_reviews || []).filter(ar => ar.id !== appendReviewId);
              this.setData({
                'review.append_reviews': appendReviews
              });
            }
            
            wx.showToast({
              title: '追加评论删除成功',
              icon: 'success'
            });
          } catch (error) {
            wx.hideLoading();
            console.error('删除追加评论失败:', error);
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
