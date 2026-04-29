const { 
  getOrderReview, 
  createReview, 
  updateReview,
  calculateRating 
} = require('../../api/reviews');
const { getOrderById } = require('../../api/orders');
const { showToast, getFullImageUrl, processProductImages } = require('../../utils/util');

const PRODUCT_DETAIL_ITEMS = [
  { key: 'craft_quality', label: '工艺质量', description: '手作工艺的精细程度' },
  { key: 'material_quality', label: '材料质感', description: '使用材料的质感和品质' },
  { key: 'design_appeal', label: '款式设计', description: '外观设计的美观程度' },
  { key: 'practical_value', label: '实用价值', description: '产品的实用性和功能性' },
  { key: 'packaging_quality', label: '包装精美', description: '包装的精美和保护程度' }
];

const TEACHER_DETAIL_ITEMS = [
  { key: 'teaching_patience', label: '教学耐心', description: '老师教学的耐心程度' },
  { key: 'communication_timely', label: '沟通及时', description: '回复消息的及时性' },
  { key: 'professional_level', label: '专业程度', description: '老师的专业技能水平' },
  { key: 'service_attitude', label: '服务态度', description: '服务态度的友好程度' },
  { key: 'after_sales_service', label: '售后服务', description: '售后问题处理能力' }
];

const LOGISTICS_DETAIL_ITEMS = [
  { key: 'delivery_speed', label: '配送速度', description: '物流配送的速度' },
  { key: 'package_condition', label: '包裹完好', description: '包裹送达时的完好程度' },
  { key: 'logistics_service', label: '物流服务', description: '快递员的服务态度' }
];

Page({
  data: {
    orderId: null,
    orderInfo: null,
    productInfo: null,
    isLoading: true,
    
    editMode: false,
    reviewId: null,
    hasReview: false,
    existingReview: null,
    
    productDetailItems: PRODUCT_DETAIL_ITEMS,
    teacherDetailItems: TEACHER_DETAIL_ITEMS,
    logisticsDetailItems: LOGISTICS_DETAIL_ITEMS,
    
    productDetailRatings: {},
    teacherDetailRatings: {},
    logisticsDetailRatings: {},
    
    productRating: 0,
    teacherRating: 0,
    logisticsRating: 0,
    overallRating: 0,
    
    allProductRated: false,
    allTeacherRated: false,
    allLogisticsRated: false,
    
    content: '',
    images: [],
    isAnonymous: false,
    
    submitting: false,
    expandedSection: 'product'
  },

  onLoad(options) {
    console.log('order-review onLoad, options:', options);
    const orderId = options.id;
    const mode = options.mode;
    
    if (!orderId) {
      showToast('参数错误');
      wx.navigateBack();
      return;
    }

    const isEditMode = mode === 'edit';
    
    this.setData({ 
      orderId: orderId,
      editMode: isEditMode
    });
    
    if (isEditMode) {
      wx.setNavigationBarTitle({
        title: '修改评价'
      });
    }
    
    this.loadOrderReview();
  },

  async loadOrderReview() {
    this.setData({ isLoading: true });
    
    try {
      const result = await getOrderReview(this.data.orderId);
      console.log('订单评价信息:', result);
      
      const orderInfo = result.order_info;
      
      let productInfo = null;
      if (orderInfo && orderInfo.items && orderInfo.items.length > 0) {
        const item = orderInfo.items[0];
        productInfo = {
          id: item.product_id,
          title: item.product_title,
          image: getFullImageUrl(item.product_image)
        };
      }
      
      if (result.has_review && result.review) {
        const review = result.review;
        const editMode = this.data.editMode;
        
        if (editMode) {
          const productDetailRatings = review.product_detail_ratings || {};
          const teacherDetailRatings = review.teacher_detail_ratings || {};
          const logisticsDetailRatings = review.logistics_detail_ratings || {};
          
          const allProductRated = Object.keys(productDetailRatings).filter(k => productDetailRatings[k] > 0).length === PRODUCT_DETAIL_ITEMS.length;
          const allTeacherRated = Object.keys(teacherDetailRatings).filter(k => teacherDetailRatings[k] > 0).length === TEACHER_DETAIL_ITEMS.length;
          const allLogisticsRated = Object.keys(logisticsDetailRatings).filter(k => logisticsDetailRatings[k] > 0).length === LOGISTICS_DETAIL_ITEMS.length;
          
          this.setData({
            hasReview: true,
            existingReview: review,
            reviewId: review.id,
            orderInfo: orderInfo,
            productInfo: productInfo,
            productDetailRatings: productDetailRatings,
            teacherDetailRatings: teacherDetailRatings,
            logisticsDetailRatings: logisticsDetailRatings,
            productRating: review.product_rating || 0,
            teacherRating: review.teacher_rating || 0,
            logisticsRating: review.logistics_rating || 0,
            overallRating: review.overall_rating || 0,
            allProductRated: allProductRated,
            allTeacherRated: allTeacherRated,
            allLogisticsRated: allLogisticsRated,
            content: review.content || '',
            images: review.images || [],
            isAnonymous: review.is_anonymous || false,
            isLoading: false
          });
        } else {
          this.setData({
            hasReview: true,
            existingReview: review,
            reviewId: review.id,
            orderInfo: orderInfo,
            productInfo: productInfo,
            isLoading: false
          });
        }
        return;
      }
      
      this.setData({
        orderInfo: orderInfo,
        productInfo: productInfo,
        isLoading: false
      });
      
    } catch (error) {
      console.error('加载订单评价信息失败:', error);
      this.setData({ isLoading: false });
      showToast('加载失败，请重试');
    }
  },

  onProductRatingChange(e) {
    const { key } = e.currentTarget.dataset;
    const { value } = e.detail;
    
    console.log('商品评分变化:', key, value);
    
    const productDetailRatings = { ...this.data.productDetailRatings };
    productDetailRatings[key] = value;
    
    const ratedCount = Object.keys(productDetailRatings).filter(k => productDetailRatings[k] > 0).length;
    const allProductRated = ratedCount === PRODUCT_DETAIL_ITEMS.length;
    
    this.setData({
      productDetailRatings: productDetailRatings,
      allProductRated: allProductRated
    });
    
    this.calculateAverageRatings();
  },

  onTeacherRatingChange(e) {
    const { key } = e.currentTarget.dataset;
    const { value } = e.detail;
    
    console.log('老师评分变化:', key, value);
    
    const teacherDetailRatings = { ...this.data.teacherDetailRatings };
    teacherDetailRatings[key] = value;
    
    const ratedCount = Object.keys(teacherDetailRatings).filter(k => teacherDetailRatings[k] > 0).length;
    const allTeacherRated = ratedCount === TEACHER_DETAIL_ITEMS.length;
    
    this.setData({
      teacherDetailRatings: teacherDetailRatings,
      allTeacherRated: allTeacherRated
    });
    
    this.calculateAverageRatings();
  },

  onLogisticsRatingChange(e) {
    const { key } = e.currentTarget.dataset;
    const { value } = e.detail;
    
    console.log('物流评分变化:', key, value);
    
    const logisticsDetailRatings = { ...this.data.logisticsDetailRatings };
    logisticsDetailRatings[key] = value;
    
    const ratedCount = Object.keys(logisticsDetailRatings).filter(k => logisticsDetailRatings[k] > 0).length;
    const allLogisticsRated = ratedCount === LOGISTICS_DETAIL_ITEMS.length;
    
    this.setData({
      logisticsDetailRatings: logisticsDetailRatings,
      allLogisticsRated: allLogisticsRated
    });
    
    this.calculateAverageRatings();
  },

  calculateAverageRatings() {
    const { productDetailRatings, teacherDetailRatings, logisticsDetailRatings } = this.data;
    
    let productRating = 0;
    let productCount = 0;
    for (const item of PRODUCT_DETAIL_ITEMS) {
      if (productDetailRatings[item.key] > 0) {
        productRating += productDetailRatings[item.key];
        productCount++;
      }
    }
    if (productCount > 0) {
      productRating = Math.round((productRating / productCount) * 10) / 10;
    }
    
    let teacherRating = 0;
    let teacherCount = 0;
    for (const item of TEACHER_DETAIL_ITEMS) {
      if (teacherDetailRatings[item.key] > 0) {
        teacherRating += teacherDetailRatings[item.key];
        teacherCount++;
      }
    }
    if (teacherCount > 0) {
      teacherRating = Math.round((teacherRating / teacherCount) * 10) / 10;
    }
    
    let logisticsRating = 0;
    let logisticsCount = 0;
    for (const item of LOGISTICS_DETAIL_ITEMS) {
      if (logisticsDetailRatings[item.key] > 0) {
        logisticsRating += logisticsDetailRatings[item.key];
        logisticsCount++;
      }
    }
    if (logisticsCount > 0) {
      logisticsRating = Math.round((logisticsRating / logisticsCount) * 10) / 10;
    }
    
    let overallRating = 0;
    const hasAllRatings = productCount > 0 && teacherCount > 0 && logisticsCount > 0;
    if (hasAllRatings) {
      const productWeight = 0.4;
      const teacherWeight = 0.35;
      const logisticsWeight = 0.25;
      
      overallRating = productRating * productWeight + 
                      teacherRating * teacherWeight + 
                      logisticsRating * logisticsWeight;
      overallRating = Math.round(overallRating * 10) / 10;
    }
    
    this.setData({
      productRating: productRating,
      teacherRating: teacherRating,
      logisticsRating: logisticsRating,
      overallRating: overallRating
    });
  },

  onContentInput(e) {
    this.setData({ content: e.detail.value });
  },

  chooseImages() {
    const self = this;
    const currentImages = this.data.images;
    const remaining = 9 - currentImages.length;
    
    if (remaining <= 0) {
      showToast('最多上传9张图片');
      return;
    }
    
    wx.chooseImage({
      count: remaining,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success(res) {
        const tempFilePaths = res.tempFilePaths;
        const newImages = [...currentImages, ...tempFilePaths].slice(0, 9);
        self.setData({ images: newImages });
      }
    });
  },

  removeImage(e) {
    const index = e.currentTarget.dataset.index;
    const images = [...this.data.images];
    images.splice(index, 1);
    this.setData({ images: images });
  },

  previewImage(e) {
    const current = e.currentTarget.dataset.url;
    const urls = this.data.images;
    
    wx.previewImage({
      current: current,
      urls: urls
    });
  },

  onAnonymousChange(e) {
    this.setData({ isAnonymous: e.detail.value });
  },

  toggleSection(e) {
    const section = e.currentTarget.dataset.section;
    const current = this.data.expandedSection;
    
    this.setData({
      expandedSection: current === section ? '' : section
    });
  },

  async submitReview() {
    const { 
      orderId, 
      reviewId,
      productDetailRatings, 
      teacherDetailRatings, 
      logisticsDetailRatings,
      content,
      images,
      isAnonymous,
      submitting,
      allProductRated,
      allTeacherRated,
      allLogisticsRated,
      editMode
    } = this.data;
    
    if (submitting) return;
    
    if (!allProductRated) {
      showToast('请完成所有商品评价项');
      return;
    }
    
    if (!allTeacherRated) {
      showToast('请完成所有老师评价项');
      return;
    }
    
    if (!allLogisticsRated) {
      showToast('请完成所有物流评价项');
      return;
    }
    
    this.setData({ submitting: true });
    wx.showLoading({ title: editMode ? '保存中...' : '提交中...', mask: true });
    
    try {
      const submitData = {
        product_detail_ratings: productDetailRatings,
        teacher_detail_ratings: teacherDetailRatings,
        logistics_detail_ratings: logisticsDetailRatings,
        content: content,
        images: [],
        is_anonymous: isAnonymous
      };
      
      if (images.length > 0) {
        submitData.images = images;
      }
      
      let result;
      if (editMode && reviewId) {
        result = await updateReview(reviewId, submitData);
        console.log('评价更新结果:', result);
        showToast('评价保存成功', 'success');
      } else {
        submitData.order_id = orderId;
        result = await createReview(submitData);
        console.log('评价提交结果:', result);
        showToast('评价提交成功', 'success');
      }
      
      wx.hideLoading();
      
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
      
    } catch (error) {
      console.error('评价提交失败:', error);
      wx.hideLoading();
      this.setData({ submitting: false });
      showToast(error.msg || '提交失败，请重试');
    }
  },

  goToReviewDetail() {
    const review = this.data.existingReview;
    if (review) {
      wx.navigateTo({
        url: `/pages/review-detail/index?id=${review.id}`
      });
    }
  }
});
