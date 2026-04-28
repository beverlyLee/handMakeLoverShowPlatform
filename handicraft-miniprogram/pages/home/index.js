const { getCategoriesWithHotProducts } = require('../../api/products');
const { showToast, getFullImageUrl, processProductImages, DEFAULT_IMAGE } = require('../../utils/util');

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
    } catch (error) {
      console.error('加载分类及热门作品失败:', error);
      this.setData({ isLoading: false, isRefreshing: false });
      showToast('加载失败，请重试');
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

  preventBubble() {
    return;
  }
})
