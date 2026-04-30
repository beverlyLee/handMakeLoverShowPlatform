const { getHotProducts, getNewProducts } = require('../../api/products');
const { batchCheckLikeStatus } = require('../../api/favorites');
const { showToast, getFullImageUrl, processProductImages, DEFAULT_IMAGE } = require('../../utils/util');
const { getToken } = require('../../utils/storage');

Page({
  data: {
    featuredProducts: [],
    isLoading: false,
    isRefreshing: false,
    defaultImage: DEFAULT_IMAGE
  },

  onLoad() {
    console.log('手工圈页面加载完成');
    this.loadFeaturedProducts();
  },

  onReady() {
    console.log('手工圈页面渲染完成');
  },

  onShow() {
    console.log('手工圈页面显示');
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setSelected(2);
    }
    this.refreshLikeStatus();
  },

  onHide() {
    console.log('手工圈页面隐藏');
  },

  onUnload() {
    console.log('手工圈页面卸载');
  },

  onPullDownRefresh() {
    this.setData({
      isRefreshing: true
    });
    this.loadFeaturedProducts().then(() => {
      wx.stopPullDownRefresh();
      this.setData({ isRefreshing: false });
    });
  },

  async loadFeaturedProducts() {
    if (this.data.isLoading) return;

    this.setData({ isLoading: true });

    try {
      const result = await getHotProducts({ limit: 12 });
      const products = result || [];
      
      const processedProducts = products.map(product => {
        const processedProduct = { ...product };
        
        if (processedProduct.is_liked === undefined || processedProduct.is_liked === null) {
          processedProduct.is_liked = false;
        }
        
        if (!processedProduct.cover_image) {
          if (processedProduct.images && processedProduct.images.length > 0) {
            processedProduct.cover_image = processedProduct.images[0];
          } else {
            processedProduct.cover_image = DEFAULT_IMAGE;
          }
        }
        
        processedProduct.cover_image = getFullImageUrl(processedProduct.cover_image);
        
        if (!processedProduct.images || processedProduct.images.length === 0) {
          processedProduct.images = [processedProduct.cover_image];
        } else {
          processedProduct.images = processedProduct.images.map(img => getFullImageUrl(img));
        }
        
        return processedProduct;
      });

      this.setData({
        featuredProducts: processedProducts,
        isLoading: false
      });

      this.refreshLikeStatus();
    } catch (error) {
      console.error('加载精选作品失败:', error);
      this.setData({ isLoading: false, isRefreshing: false });
      showToast('加载失败，请重试');
    }
  },

  async refreshLikeStatus() {
    const { featuredProducts } = this.data;
    if (!featuredProducts || featuredProducts.length === 0) return;

    const token = getToken();
    if (!token) {
      console.log('用户未登录，不检查点赞状态');
      return;
    }

    const productIds = featuredProducts.map(product => product.id);

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

        const updatedProducts = featuredProducts.map(product => {
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
          featuredProducts: updatedProducts
        });
      }
    } catch (error) {
      console.error('检查点赞状态失败:', error);
    }
  },

  goToHotProducts() {
    wx.switchTab({
      url: '/pages/products/index'
    });
  },

  goToNewProducts() {
    wx.switchTab({
      url: '/pages/products/index'
    });
  },

  goToCategories() {
    wx.switchTab({
      url: '/pages/products/index'
    });
  },

  goToProductDetail(e) {
    const productId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/work-detail/index?id=${productId}`
    });
  },

  onImageError(e) {
    const index = e.currentTarget.dataset.index;
    const featuredProducts = this.data.featuredProducts;
    
    if (featuredProducts && featuredProducts[index]) {
      featuredProducts[index].cover_image = DEFAULT_IMAGE;
      this.setData({
        featuredProducts: featuredProducts
      });
    }
  },

  onLikeChange(e) {
    const { index } = e.currentTarget.dataset;
    const { isLiked, likeCount, popularityScore } = e.detail;
    
    const featuredProducts = this.data.featuredProducts;
    if (featuredProducts && featuredProducts[index]) {
      featuredProducts[index].is_liked = isLiked;
      featuredProducts[index].like_count = likeCount;
      if (popularityScore !== undefined && popularityScore !== null) {
        featuredProducts[index].heat_score = popularityScore;
        featuredProducts[index].popularity_score = popularityScore;
      }
      this.setData({
        featuredProducts: featuredProducts
      });
    }
  },

  preventBubble() {
    return;
  },

  showComingSoon() {
    showToast('功能开发中，敬请期待');
  }
});
