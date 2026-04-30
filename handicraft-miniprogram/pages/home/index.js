const { getCategoriesWithHotProducts } = require('../../api/products');
const { batchCheckLikeStatus } = require('../../api/favorites');
const { showToast, getFullImageUrl, processProductImages, DEFAULT_IMAGE } = require('../../utils/util');
const { getToken } = require('../../utils/storage');

Page({
  data: {
    welcomeText: '欢迎来到手工爱好者平台',
    categories: [],
    currentSwiperIndex: {},
    isLoading: false,
    isRefreshing: false
  },

  onLoad() {
    console.log('首页加载完成');
    this.loadCategoriesWithHotProducts();
  },

  onReady() {
    console.log('首页渲染完成');
  },

  onShow() {
    console.log('首页显示');
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setSelected(0);
    }
  },

  onHide() {
    console.log('首页隐藏');
  },

  onUnload() {
    console.log('首页卸载');
  },

  onPullDownRefresh() {
    this.setData({
      isRefreshing: true
    });
    this.loadCategoriesWithHotProducts().then(() => {
      wx.stopPullDownRefresh();
      this.setData({ isRefreshing: false });
    });
  },

  async loadCategoriesWithHotProducts() {
    if (this.data.isLoading) return;

    this.setData({ isLoading: true });

    try {
      const result = await getCategoriesWithHotProducts({ limit: 3 });
      const categories = result || [];
      
      const processedCategories = categories.map(category => {
        const processedCategory = { ...category };
        
        if (processedCategory.hot_products && processedCategory.hot_products.length > 0) {
          processedCategory.hot_products = processedCategory.hot_products.map(product => {
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
        }
        
        return processedCategory;
      });
      
      const currentSwiperIndex = {};
      processedCategories.forEach(category => {
        currentSwiperIndex[category.id] = 0;
      });

      this.setData({
        categories: processedCategories,
        currentSwiperIndex: currentSwiperIndex,
        isLoading: false
      });

      this.refreshLikeStatus();
    } catch (error) {
      console.error('加载分类及热门作品失败:', error);
      this.setData({ isLoading: false, isRefreshing: false });
      showToast('加载失败，请重试');
    }
  },

  async refreshLikeStatus() {
    const { categories } = this.data;
    if (!categories || categories.length === 0) return;

    const token = getToken();
    if (!token) {
      console.log('用户未登录，不检查点赞状态');
      return;
    }

    const productIds = [];
    categories.forEach(category => {
      if (category.hot_products && category.hot_products.length > 0) {
        category.hot_products.forEach(product => {
          productIds.push(product.id);
        });
      }
    });

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

        const updatedCategories = categories.map(category => {
          const updatedCategory = { ...category };
          if (updatedCategory.hot_products && updatedCategory.hot_products.length > 0) {
            updatedCategory.hot_products = updatedCategory.hot_products.map(product => {
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
          }
          return updatedCategory;
        });

        this.setData({
          categories: updatedCategories
        });
      }
    } catch (error) {
      console.error('检查点赞状态失败:', error);
    }
  },

  onSwiperChange(e) {
    const categoryId = e.currentTarget.dataset.categoryId;
    const current = e.detail.current;
    
    this.setData({
      [`currentSwiperIndex.${categoryId}`]: current
    });
  },

  goToProductDetail(e) {
    const productId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/work-detail/index?id=${productId}`
    });
  },

  onImageError(e) {
    const categoryId = e.currentTarget.dataset.categoryId;
    const productIndex = e.currentTarget.dataset.productIndex;
    
    console.log('图片加载失败，使用默认图片:', { categoryId, productIndex });
    
    const categories = this.data.categories;
    if (categories && categories.length > 0) {
      const category = categories.find(cat => cat.id === categoryId);
      if (category && category.hot_products && category.hot_products[productIndex]) {
        category.hot_products[productIndex].cover_image = DEFAULT_IMAGE;
        this.setData({
          categories: categories
        });
      }
    }
  },

  onLikeChange(e) {
    const { categoryId, productIndex } = e.currentTarget.dataset;
    const { isLiked, likeCount, popularityScore } = e.detail;
    
    const categories = this.data.categories;
    if (categories && categories.length > 0) {
      const category = categories.find(cat => cat.id === categoryId);
      if (category && category.hot_products && category.hot_products[productIndex]) {
        category.hot_products[productIndex].is_liked = isLiked;
        category.hot_products[productIndex].like_count = likeCount;
        if (popularityScore !== undefined && popularityScore !== null) {
          category.hot_products[productIndex].heat_score = popularityScore;
          category.hot_products[productIndex].popularity_score = popularityScore;
        }
        this.setData({
          categories: categories
        });
      }
    }
  },

  preventBubble() {
    return;
  }
})
