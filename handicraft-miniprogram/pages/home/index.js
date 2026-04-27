const { getProducts, getProductDetail } = require('../../api/products');
const { showToast } = require('../../utils/util');

Page({
  data: {
    welcomeText: '欢迎来到手工爱好者平台',
    products: [],
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
    isLoading: false,
    isRefreshing: false
  },

  onLoad() {
    console.log('首页加载完成');
    this.loadProducts();
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
      page: 1,
      hasMore: true,
      products: [],
      isRefreshing: true
    });
    this.loadProducts().then(() => {
      wx.stopPullDownRefresh();
      this.setData({ isRefreshing: false });
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

  async loadProducts(append = false) {
    if (this.data.isLoading) return;

    this.setData({ isLoading: true });

    try {
      const params = {
        page: this.data.page,
        size: this.data.pageSize,
        sort: this.data.currentSort
      };

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
      this.setData({ isLoading: false, isRefreshing: false });
      showToast('加载失败，请重试');
    }
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

  goToProductDetail(e) {
    const productId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/work-detail/index?id=${productId}`
    });
  },

  goToTeacherProfile(e) {
    e.stopPropagation();
    const teacherId = e.currentTarget.dataset.teacherId;
    wx.navigateTo({
      url: `/pages/teacher-home/index?id=${teacherId}`
    });
  },

  preventBubble() {
    return;
  }
})
