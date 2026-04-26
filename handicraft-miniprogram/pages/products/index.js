const { getProducts, getCategories } = require('../../api/products');
const { showToast } = require('../../utils/util');

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
      { key: 'sales', label: '销量最高', value: 'sales' }
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

      if (append) {
        this.setData({
          products: [...this.data.products, ...newProducts],
          hasMore: newProducts.length >= this.data.pageSize,
          isLoading: false
        });
      } else {
        this.setData({
          products: newProducts,
          hasMore: newProducts.length >= this.data.pageSize,
          isLoading: false
        });
      }
    } catch (error) {
      console.error('加载作品列表失败:', error);
      this.setData({ isLoading: false });
      showToast('加载失败，请重试');
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
      url: `/pages/product-detail/index?id=${productId}`
    });
  }
});
