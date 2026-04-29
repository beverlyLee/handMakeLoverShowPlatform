const { getProducts, getCategories } = require('../../api/products');
const { batchCheckLikeStatus } = require('../../api/favorites');
const { showToast, processProductImages } = require('../../utils/util');
const { getToken } = require('../../utils/storage');

Page({
  data: {
    categories: [],
    products: [],
    currentCategoryId: null,
    currentSort: 'default',
    sortOptions: [
      { key: 'default', label: '默认排序', value: 'default' },
      { key: 'price_asc', label: '价格从低到高', value: 'price_asc' },
      { key: 'price_desc', label: '价格从高到低', value: 'price_desc' },
      { key: 'popular', label: '人气最高', value: 'popular' },
      { key: 'sales', label: '销量最高', value: 'sales' },
      { key: 'rating', label: '好评优先', value: 'rating' }
    ],
    currentSortLabel: '默认排序',
    showSortDropdown: false,
    page: 1,
    pageSize: 10,
    hasMore: true,
    isLoading: false
  },

  onLoad() {
    this.loadCategories();
    this.loadProducts();
  },

  onShow() {
    this.loadProducts();
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setSelected(1)
    }
  },

  onPullDownRefresh() {
    this.setData({
      page: 1,
      hasMore: true,
      products: []
    });
    Promise.all([this.loadCategories(), this.loadProducts()]).then(() => {
      wx.stopPullDownRefresh();
    });
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.isLoading) {
      this.setData({
        page: this.data.page + 1
      });
      this.loadProducts(true);
    }
  },

  async loadCategories() {
    try {
      const categories = await getCategories();
      this.setData({
        categories: categories || []
      });
    } catch (error) {
      console.error('加载分类失败:', error);
    }
  },

  async loadProducts(append = false) {
    if (this.data.isLoading) return;

    this.setData({ isLoading: true });

    try {
      const params = {
        page: this.data.page,
        size: this.data.pageSize,
        sort: this.data.currentSort
      };

      if (this.data.currentCategoryId) {
        params.category = this.data.currentCategoryId;
      }

      const result = await getProducts(params);
      const newProducts = (result && result.list) || result || [];
      
      const processedProducts = newProducts.map(p => {
        const processed = processProductImages(p);
        if (processed.is_liked === undefined || processed.is_liked === null) {
          processed.is_liked = false;
        }
        return processed;
      });

      if (append) {
        this.setData({
          products: [...this.data.products, ...processedProducts],
          hasMore: newProducts.length >= this.data.pageSize,
          isLoading: false
        });
      } else {
        this.setData({
          products: processedProducts,
          hasMore: newProducts.length >= this.data.pageSize,
          isLoading: false
        });
      }

      if (!append) {
        this.refreshLikeStatus();
      }
    } catch (error) {
      console.error('加载作品列表失败:', error);
      this.setData({ isLoading: false });
      showToast('加载失败，请重试');
    }
  },

  async refreshLikeStatus() {
    const { products } = this.data;
    if (!products || products.length === 0) return;

    const token = getToken();
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
            like_count: item.like_count
          };
        });

        const updatedProducts = products.map(product => {
          const likeStatus = likeStatusMap[product.id];
          if (likeStatus) {
            return {
              ...product,
              is_liked: likeStatus.is_liked,
              like_count: likeStatus.like_count
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

  switchCategory(e) {
    const categoryId = e.currentTarget.dataset.id;
    this.setData({
      currentCategoryId: this.data.currentCategoryId === categoryId ? null : categoryId,
      page: 1,
      products: [],
      hasMore: true
    });
    this.loadProducts();
  },

  toggleSortDropdown() {
    this.setData({
      showSortDropdown: !this.data.showSortDropdown
    });
  },

  selectSort(e) {
    const sortKey = e.currentTarget.dataset.sort;
    const sortLabel = e.currentTarget.dataset.label;

    if (this.data.currentSort === sortKey) {
      this.setData({ showSortDropdown: false });
      return;
    }

    this.setData({
      currentSort: sortKey,
      currentSortLabel: sortLabel,
      showSortDropdown: false,
      page: 1,
      products: [],
      hasMore: true
    });

    this.loadProducts();
  },

  preventBubble() {
    return;
  },

  goToSearch() {
    wx.navigateTo({
      url: '/pages/search/index'
    });
  },

  goToProductDetail(e) {
    const productId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/work-detail/index?id=${productId}`
    });
  }
});
