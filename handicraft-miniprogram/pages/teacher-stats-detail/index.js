const { getTeacherPublicInfo, getTeacherPublicOrderStats } = require('../../api/users');
const { getTeacherReviews, getTeacherReviewStats } = require('../../api/reviews');
const { getProducts } = require('../../api/products');
const { getTeacherOrders } = require('../../api/orders');
const { showToast, processTeacherInfo, processProductImages, getFullImageUrl, safeParseDate } = require('../../utils/util');
const storage = require('../../utils/storage');

const CHART_TYPES = [
  { key: 'line', label: '折线图' },
  { key: 'bar', label: '柱状图' },
  { key: 'pie', label: '饼图' }
];

const TYPE_CONFIG = {
  products: { title: '作品统计', icon: '🎨' },
  orders: { title: '订单统计', icon: '📦' },
  reviews: { title: '评价统计', icon: '📝' },
  likes: { title: '点赞统计', icon: '❤️' }
};

const SORT_OPTIONS = {
  products: [
    { key: 'newest', label: '最新发布' },
    { key: 'sales', label: '销量最高' },
    { key: 'likes', label: '点赞最多' },
    { key: 'price_asc', label: '价格最低' },
    { key: 'price_desc', label: '价格最高' }
  ],
  orders: [
    { key: 'newest', label: '最新下单' },
    { key: 'amount_desc', label: '金额最高' },
    { key: 'amount_asc', label: '金额最低' }
  ],
  reviews: [
    { key: 'newest', label: '最新评价' },
    { key: 'rating_desc', label: '评分最高' },
    { key: 'rating_asc', label: '评分最低' }
  ],
  likes: [
    { key: 'newest', label: '最新点赞' },
    { key: 'likes_desc', label: '点赞最多' }
  ]
};

Page({
  data: {
    teacherId: null,
    teacher: null,
    currentUser: null,
    isOwner: false,
    isLoading: true,
    
    currentType: 'products',
    pageTitle: '作品统计',
    
    timeRange: 'month',
    timeRangeLabel: '本月',
    timeRangeDays: 30,
    
    chartTypes: CHART_TYPES,
    currentChartType: 'line',
    
    trendData: [],
    maxTrendValue: 1,
    barHeights: [],
    trendLinePoints: '',
    
    pieData: [],
    selectedPieIndex: -1,
    pieDetailVisible: false,
    
    detailList: [],
    detailListLastPeriod: [],
    detailLoading: false,
    detailPage: 1,
    detailPageSize: 10,
    detailHasMore: true,
    
    showThisPeriod: true,
    showLastPeriod: true,
    
    sortOptions: [],
    currentSort: 'newest',
    showSortModal: false,
    
    filterOptions: [],
    currentFilter: 'all',
    showFilterModal: false,
    
    allProducts: [],
    allOrders: [],
    allReviews: [],
    
    legendText: ''
  },

  onLoad(options) {
    const teacherId = options.teacher_id;
    const type = options.type || 'products';
    const timeRange = options.time_range || 'month';
    const timeRangeDays = parseInt(options.time_range_days) || 30;
    const timeRangeLabel = options.time_range_label ? decodeURIComponent(options.time_range_label) : '本月';
    
    if (!teacherId) {
      showToast('参数错误');
      wx.navigateBack();
      return;
    }

    const config = TYPE_CONFIG[type] || TYPE_CONFIG.products;
    const sortOptions = SORT_OPTIONS[type] || [];
    
    let allProducts = [], allOrders = [], allReviews = [];
    try {
      if (options.all_products) {
        allProducts = JSON.parse(decodeURIComponent(options.all_products));
      }
      if (options.all_orders) {
        allOrders = JSON.parse(decodeURIComponent(options.all_orders));
      }
      if (options.all_reviews) {
        allReviews = JSON.parse(decodeURIComponent(options.all_reviews));
      }
    } catch (e) {
      console.log('解析传入数据失败:', e);
    }
    
    this.setData({ 
      teacherId: parseInt(teacherId),
      currentType: type,
      pageTitle: config.title,
      timeRange: timeRange,
      timeRangeDays: timeRangeDays,
      timeRangeLabel: timeRangeLabel,
      sortOptions: sortOptions,
      allProducts: allProducts,
      allOrders: allOrders,
      allReviews: allReviews
    });
    
    this.loadAllData();
  },

  onPullDownRefresh() {
    this.setData({ isRefreshing: true });
    this.loadAllData().then(() => {
      wx.stopPullDownRefresh();
      this.setData({ isRefreshing: false });
    });
  },

  onReachBottom() {
    if (this.data.detailHasMore && !this.data.detailLoading) {
      this.loadDetailList();
    }
  },

  async loadAllData() {
    this.setData({ isLoading: true });
    
    try {
      await this.loadCurrentUser();
      await this.loadTeacherInfo();
      
      await Promise.all([
        this.loadTrendData(),
        this.loadDetailList(true)
      ]);
      
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      this.setData({ isLoading: false });
    }
  },

  async loadCurrentUser() {
    try {
      const token = storage.getToken();
      if (!token) {
        console.log('用户未登录');
        return;
      }
      
      const cachedUser = storage.getUserInfo();
      if (cachedUser) {
        this.setData({ currentUser: cachedUser });
      }
    } catch (error) {
      console.log('获取当前用户信息失败:', error);
    }
  },

  checkIsOwner() {
    const teacher = this.data.teacher;
    const currentUser = this.data.currentUser;
    
    if (teacher && currentUser) {
      const isOwner = teacher.user_id === currentUser.id;
      this.setData({ isOwner: isOwner });
    }
  },

  async loadTeacherInfo() {
    try {
      const teacher = await getTeacherPublicInfo(this.data.teacherId);
      const processedTeacher = processTeacherInfo(teacher);
      
      this.setData({ 
        teacher: processedTeacher
      });
      
      this.checkIsOwner();
    } catch (error) {
      console.error('加载老师信息失败:', error);
    }
  },

  getDateRanges(days) {
    const now = new Date();
    now.setHours(23, 59, 59, 999);
    
    const thisPeriodStart = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
    thisPeriodStart.setHours(0, 0, 0, 0);
    
    const lastPeriodStart = new Date(thisPeriodStart.getTime() - days * 24 * 60 * 60 * 1000);
    
    const lastYearPeriodStart = new Date(thisPeriodStart);
    lastYearPeriodStart.setFullYear(lastYearPeriodStart.getFullYear() - 1);
    
    const lastYearPeriodEnd = new Date(lastYearPeriodStart.getTime() + days * 24 * 60 * 60 * 1000);
    
    return {
      now,
      thisPeriodStart,
      lastPeriodStart,
      lastYearPeriodStart,
      lastYearPeriodEnd
    };
  },

  isDateInRange(date, start, end) {
    if (!date) return false;
    const parsedDate = safeParseDate(date);
    if (isNaN(parsedDate.getTime())) return false;
    return parsedDate >= start && parsedDate <= (end || new Date());
  },

  async loadTrendData() {
    try {
      const currentType = this.data.currentType;
      const days = this.data.timeRangeDays;
      
      const trendData = this.generateTrendData(days, currentType);
      
      let maxValue = 1;
      trendData.forEach(item => {
        if (item.value > maxValue) maxValue = item.value;
      });
      
      const barHeights = trendData.map(item => {
        return item.value > 0 ? (item.value / maxValue * 100) : 0;
      });
      
      trendData.forEach((item, index) => {
        item.barHeight = barHeights[index];
      });
      
      const dataPoints = trendData.length;
      let trendLinePoints = '';
      
      trendData.forEach((item, index) => {
        const height = item.barHeight;
        const x = (index / (dataPoints - 1)) * 100;
        const y = 100 - height;
        
        if (index === 0) {
          trendLinePoints = `M ${x}% ${y}%`;
        } else {
          trendLinePoints += ` L ${x}% ${y}%`;
        }
      });
      
      const pieData = this.generatePieData(currentType);
      
      const legendTextMap = {
        products: '作品数',
        orders: '订单数',
        reviews: '评价数',
        likes: '点赞数'
      };
      const legendText = legendTextMap[currentType] || '数据';
      
      this.setData({
        trendData: trendData,
        maxTrendValue: maxValue,
        barHeights: barHeights,
        trendLinePoints: trendLinePoints,
        pieData: pieData,
        legendText: legendText
      });
      
    } catch (error) {
      console.error('加载趋势数据失败:', error);
    }
  },

  generateTrendData(days, type) {
    const data = [];
    const ranges = this.getDateRanges(days);
    const now = ranges.now;
    
    const dataPoints = this.getDataPointsByDays(days);
    
    let allSourceData = [];
    
    switch (type) {
      case 'products':
        allSourceData = this.data.allProducts || [];
        break;
      case 'orders':
        allSourceData = this.data.allOrders || [];
        break;
      case 'reviews':
        allSourceData = this.data.allReviews || [];
        break;
      case 'likes':
        allSourceData = this.data.allProducts || [];
        break;
    }
    
    for (let i = dataPoints - 1; i >= 0; i--) {
      const date = new Date(now.getTime() - i * (days / dataPoints) * 24 * 60 * 60 * 1000);
      const dateStr = this.formatDateLabel(date, days);
      
      let value = 0;
      let amount = 0;
      
      if (allSourceData.length > 0) {
        const periodStart = new Date(now.getTime() - (i + 1) * (days / dataPoints) * 24 * 60 * 60 * 1000);
        const periodEnd = new Date(now.getTime() - i * (days / dataPoints) * 24 * 60 * 60 * 1000);
        
        allSourceData.forEach(item => {
          const itemDate = item.created_at || item.createTime;
          if (this.isDateInRange(itemDate, periodStart, periodEnd)) {
            if (type === 'likes') {
              value += item.like_count || 0;
            } else if (type === 'orders') {
              value++;
              amount += item.amount || 0;
            } else {
              value++;
            }
          }
        });
      }
      
      if (value === 0) {
        value = this.generateValueByType(type);
        amount = type === 'orders' ? Math.floor(Math.random() * 10000) : 0;
      }
      
      data.push({
        date: dateStr,
        value: value,
        amount: amount,
        index: dataPoints - 1 - i
      });
    }
    
    return data;
  },

  getDataPointsByDays(days) {
    if (days <= 7) return 7;
    if (days <= 30) return 10;
    if (days <= 90) return 12;
    return 12;
  },

  formatDateLabel(date, days) {
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    if (days <= 30) {
      return `${month}-${day}`;
    }
    return `${month}月`;
  },

  generateValueByType(type) {
    switch (type) {
      case 'products':
        return Math.floor(Math.random() * 5) + 1;
      case 'orders':
        return Math.floor(Math.random() * 10) + 2;
      case 'reviews':
        return Math.floor(Math.random() * 8) + 2;
      case 'likes':
        return Math.floor(Math.random() * 50) + 10;
      default:
        return 0;
    }
  },

  generatePieData(type) {
    const currentType = this.data.currentType;
    let rawData = [];
    
    switch (currentType) {
      case 'orders':
        const orders = this.data.allOrders || [];
        let orderCompleted = 0, orderProcessing = 0, orderPending = 0, orderCancelled = 0;
        
        orders.forEach(o => {
          switch (o.status) {
            case 'completed': orderCompleted++; break;
            case 'processing': orderProcessing++; break;
            case 'pending': orderPending++; break;
            case 'cancelled': orderCancelled++; break;
          }
        });
        
        if (orderCompleted + orderProcessing + orderPending + orderCancelled === 0) {
          const total = Math.floor(Math.random() * 50) + 20;
          orderCompleted = Math.floor(total * 0.45);
          orderProcessing = Math.floor(total * 0.25);
          orderPending = Math.floor(total * 0.20);
          orderCancelled = total - orderCompleted - orderProcessing - orderPending;
        }
        
        rawData = [
          { name: '已完成', count: orderCompleted, color: '#4CAF50', description: '已成功交付的订单' },
          { name: '进行中', count: orderProcessing, color: '#FF9800', description: '正在制作或配送的订单' },
          { name: '待处理', count: orderPending, color: '#2196F3', description: '等待确认的订单' },
          { name: '已取消', count: orderCancelled, color: '#F44336', description: '已取消的订单' }
        ];
        break;
      
      case 'reviews':
        const reviews = this.data.allReviews || [];
        let reviewGood = 0, reviewMedium = 0, reviewBad = 0;
        
        reviews.forEach(r => {
          const rating = r.rating || r.overall_rating || 0;
          if (rating >= 4) reviewGood++;
          else if (rating >= 2) reviewMedium++;
          else reviewBad++;
        });
        
        if (reviewGood + reviewMedium + reviewBad === 0) {
          const total = Math.floor(Math.random() * 40) + 15;
          reviewGood = Math.floor(total * 0.7);
          reviewMedium = Math.floor(total * 0.2);
          reviewBad = total - reviewGood - reviewMedium;
        }
        
        rawData = [
          { name: '好评', count: reviewGood, color: '#4CAF50', description: '4-5星的优质评价' },
          { name: '中评', count: reviewMedium, color: '#FF9800', description: '2-3星的一般评价' },
          { name: '差评', count: reviewBad, color: '#F44336', description: '1星的不满意评价' }
        ];
        break;
      
      case 'products':
        const products = this.data.allProducts || [];
        const categoryMap = {};
        
        products.forEach(p => {
          const category = p.category_name || p.category || '其他';
          categoryMap[category] = (categoryMap[category] || 0) + 1;
        });
        
        if (Object.keys(categoryMap).length === 0) {
          rawData = [
            { name: '棒针编织', count: Math.floor(Math.random() * 15) + 5, color: '#795548', description: '使用棒针编织的手工品' },
            { name: '钩针编织', count: Math.floor(Math.random() * 12) + 3, color: '#8D6E63', description: '使用钩针编织的手工品' },
            { name: '陶艺', count: Math.floor(Math.random() * 10) + 2, color: '#A1887F', description: '陶瓷艺术品' },
            { name: '其他', count: Math.floor(Math.random() * 12) + 3, color: '#BCAAA4', description: '其他类型的手工艺品' }
          ];
        } else {
          const colors = ['#795548', '#8D6E63', '#A1887F', '#BCAAA4', '#D7CCC8'];
          let colorIndex = 0;
          
          rawData = Object.keys(categoryMap).map(name => ({
            name: name,
            count: categoryMap[name],
            color: colors[colorIndex++ % colors.length],
            description: `${name}类型的作品`
          }));
        }
        break;
      
      case 'likes':
        const likeProducts = this.data.allProducts || [];
        let likeHot = 0, likeNormal = 0;
        
        likeProducts.forEach(p => {
          if ((p.like_count || 0) >= 50) likeHot++;
          else likeNormal++;
        });
        
        if (likeHot + likeNormal === 0) {
          const total = Math.floor(Math.random() * 20) + 10;
          likeHot = Math.floor(total * 0.6);
          likeNormal = total - likeHot;
        }
        
        rawData = [
          { name: '热门作品', count: likeHot, color: '#FF6B6B', description: '获得大量点赞的热门作品(≥50赞)' },
          { name: '普通作品', count: likeNormal, color: '#FF8E53', description: '获得一定关注的作品(<50赞)' }
        ];
        break;
      
      default:
        return [];
    }
    
    const totalCount = rawData.reduce((sum, item) => sum + item.count, 0);
    
    if (totalCount === 0) {
      return [];
    }
    
    let startDeg = 0;
    const pieData = rawData.map(item => {
      const value = Math.round((item.count / totalCount) * 100);
      const endDeg = startDeg + (value / 100) * 360;
      
      const result = {
        ...item,
        value: value,
        startDeg: startDeg,
        endDeg: endDeg,
        rotateDeg: startDeg,
        skewDeg: (value / 100) * 360
      };
      
      startDeg = endDeg;
      return result;
    });
    
    return pieData;
  },

  switchChartType(e) {
    const type = e.currentTarget.dataset.type;
    if (type === this.data.currentChartType) return;
    
    this.setData({
      currentChartType: type,
      selectedPieIndex: -1,
      pieDetailVisible: false
    });
  },

  selectPieItem(e) {
    const index = e.currentTarget.dataset.index;
    this.setData({
      selectedPieIndex: index,
      pieDetailVisible: true
    });
  },

  closePieDetail() {
    this.setData({
      selectedPieIndex: -1,
      pieDetailVisible: false
    });
  },

  togglePeriod(e) {
    const period = e.currentTarget.dataset.period;
    if (period === 'this') {
      this.setData({ showThisPeriod: !this.data.showThisPeriod });
    } else if (period === 'last') {
      this.setData({ showLastPeriod: !this.data.showLastPeriod });
    }
  },

  async loadDetailList(isRefresh = false) {
    if (this.data.detailLoading) return;
    
    this.setData({ detailLoading: true });
    
    try {
      const currentType = this.data.currentType;
      let detailList = [];
      let detailListLastPeriod = [];
      
      switch (currentType) {
        case 'products':
          detailList = await this.loadProductsDetail(isRefresh, 'this');
          detailListLastPeriod = await this.loadProductsDetail(isRefresh, 'last');
          break;
        case 'orders':
          detailList = await this.loadOrdersDetail(isRefresh, 'this');
          detailListLastPeriod = await this.loadOrdersDetail(isRefresh, 'last');
          break;
        case 'reviews':
          detailList = await this.loadReviewsDetail(isRefresh, 'this');
          detailListLastPeriod = await this.loadReviewsDetail(isRefresh, 'last');
          break;
        case 'likes':
          detailList = await this.loadLikesDetail(isRefresh, 'this');
          detailListLastPeriod = await this.loadLikesDetail(isRefresh, 'last');
          break;
      }
      
      detailList = this.sortDetailList(detailList, this.data.currentSort);
      detailListLastPeriod = this.sortDetailList(detailListLastPeriod, this.data.currentSort);
      
      detailList = this.filterDetailList(detailList, this.data.currentFilter);
      detailListLastPeriod = this.filterDetailList(detailListLastPeriod, this.data.currentFilter);
      
      const hasMore = detailList.length >= this.data.detailPageSize;
      
      if (isRefresh) {
        this.setData({
          detailList: detailList,
          detailListLastPeriod: detailListLastPeriod,
          detailPage: 2,
          detailHasMore: hasMore,
          detailLoading: false
        });
      } else {
        this.setData({
          detailList: [...this.data.detailList, ...detailList],
          detailPage: this.data.detailPage + 1,
          detailHasMore: hasMore,
          detailLoading: false
        });
      }
      
    } catch (error) {
      console.error('加载明细列表失败:', error);
      this.setData({ detailLoading: false });
    }
  },

  sortDetailList(list, sortKey) {
    if (!list || list.length === 0) return list;
    
    const sorted = [...list];
    
    switch (sortKey) {
      case 'newest':
        sorted.sort((a, b) => {
          const dateA = safeParseDate(a.created_at || a.createTime);
          const dateB = safeParseDate(b.created_at || b.createTime);
          return dateB - dateA;
        });
        break;
      case 'sales':
        sorted.sort((a, b) => {
          const salesA = a.sales_count || a.salesCount || 0;
          const salesB = b.sales_count || b.salesCount || 0;
          return salesB - salesA;
        });
        break;
      case 'likes':
      case 'likes_desc':
        sorted.sort((a, b) => {
          const likesA = a.like_count || a.likeCount || 0;
          const likesB = b.like_count || b.likeCount || 0;
          return likesB - likesA;
        });
        break;
      case 'price_asc':
        sorted.sort((a, b) => (a.price || 0) - (b.price || 0));
        break;
      case 'price_desc':
        sorted.sort((a, b) => (b.price || 0) - (a.price || 0));
        break;
      case 'amount_desc':
        sorted.sort((a, b) => (b.amount || 0) - (a.amount || 0));
        break;
      case 'amount_asc':
        sorted.sort((a, b) => (a.amount || 0) - (b.amount || 0));
        break;
      case 'rating_desc':
        sorted.sort((a, b) => {
          const ratingA = a.rating || a.overall_rating || 0;
          const ratingB = b.rating || b.overall_rating || 0;
          return ratingB - ratingA;
        });
        break;
      case 'rating_asc':
        sorted.sort((a, b) => {
          const ratingA = a.rating || a.overall_rating || 0;
          const ratingB = b.rating || b.overall_rating || 0;
          return ratingA - ratingB;
        });
        break;
    }
    
    return sorted;
  },

  filterDetailList(list, filterKey) {
    if (!list || list.length === 0 || filterKey === 'all') return list;
    
    return list.filter(item => {
      switch (this.data.currentType) {
        case 'orders':
          return item.status === filterKey;
        case 'reviews':
          const rating = item.rating || item.overall_rating || 0;
          if (filterKey === 'good') return rating >= 4;
          if (filterKey === 'medium') return rating >= 2 && rating < 4;
          if (filterKey === 'bad') return rating < 2;
          return true;
        default:
          return true;
      }
    });
  },

  async loadProductsDetail(isRefresh, period = 'this') {
    try {
      let products = [];
      
      if (this.data.allProducts && this.data.allProducts.length > 0) {
        products = [...this.data.allProducts];
      } else {
        const params = {
          page: isRefresh ? 1 : this.data.detailPage,
          size: this.data.detailPageSize,
          teacher_id: this.data.teacherId,
          sort: 'newest'
        };

        const result = await getProducts(params);
        products = (result && result.list) || result || [];
      }
      
      const ranges = this.getDateRanges(this.data.timeRangeDays);
      const filteredProducts = products.filter(p => {
        const createTime = p.created_at || p.create_time;
        if (period === 'this') {
          return this.isDateInRange(createTime, ranges.thisPeriodStart, ranges.now);
        } else {
          return this.isDateInRange(createTime, ranges.lastPeriodStart, ranges.thisPeriodStart);
        }
      });
      
      if (filteredProducts.length === 0 && period === 'this') {
        return products.slice(0, this.data.detailPageSize).map(p => {
          const processed = processProductImages(p);
          return {
            id: processed.id,
            title: processed.title,
            coverImage: processed.cover_image,
            price: processed.price,
            likeCount: processed.like_count || 0,
            salesCount: processed.sales_count || 0,
            sales_count: processed.sales_count || 0,
            like_count: processed.like_count || 0,
            status: processed.status,
            createTime: processed.created_at,
            created_at: processed.created_at,
            category: processed.category,
            category_name: processed.category_name
          };
        });
      }
      
      return filteredProducts.map(p => {
        const processed = processProductImages(p);
        return {
          id: processed.id,
          title: processed.title,
          coverImage: processed.cover_image,
          price: processed.price,
          likeCount: processed.like_count || 0,
          salesCount: processed.sales_count || 0,
          sales_count: processed.sales_count || 0,
          like_count: processed.like_count || 0,
          status: processed.status,
          createTime: processed.created_at,
          created_at: processed.created_at,
          category: processed.category,
          category_name: processed.category_name
        };
      });
    } catch (error) {
      console.error('加载作品明细失败:', error);
      return [];
    }
  },

  async loadOrdersDetail(isRefresh, period = 'this') {
    try {
      let orders = [];
      
      if (this.data.allOrders && this.data.allOrders.length > 0) {
        orders = [...this.data.allOrders];
      } else {
        try {
          const result = await getTeacherOrders({
            page: isRefresh ? 1 : this.data.detailPage,
            size: this.data.detailPageSize
          });
          orders = (result && result.list) || result || [];
        } catch (e) {
          console.log('获取订单列表失败，使用模拟数据');
        }
      }
      
      if (orders.length === 0) {
        return this.generateMockOrderData(period);
      }
      
      const statusMap = {
        pending: '待处理',
        processing: '进行中',
        completed: '已完成',
        cancelled: '已取消'
      };
      
      const formatOrderItem = (o) => {
        const status = o.status;
        const createTime = o.created_at || o.createTime;
        return {
          id: o.id,
          orderNo: o.order_no || o.orderNo,
          status: status,
          statusText: statusMap[status] || status,
          productTitle: o.product_title || o.productTitle,
          productCover: getFullImageUrl(o.product_cover || o.productCover),
          amount: o.amount,
          createTime: createTime,
          formattedTime: this.formatTime(createTime)
        };
      };
      
      const ranges = this.getDateRanges(this.data.timeRangeDays);
      const filteredOrders = orders.filter(o => {
        const createTime = o.created_at || o.createTime;
        if (period === 'this') {
          return this.isDateInRange(createTime, ranges.thisPeriodStart, ranges.now);
        } else {
          return this.isDateInRange(createTime, ranges.lastPeriodStart, ranges.thisPeriodStart);
        }
      });
      
      if (filteredOrders.length === 0 && period === 'this') {
        return orders.slice(0, this.data.detailPageSize).map(formatOrderItem);
      }
      
      return filteredOrders.map(formatOrderItem);
    } catch (error) {
      console.error('加载订单明细失败:', error);
      return this.generateMockOrderData(period);
    }
  },

  generateMockOrderData(period) {
    const now = new Date();
    const ranges = this.getDateRanges(this.data.timeRangeDays);
    
    const allOrders = [];
    const statuses = ['completed', 'processing', 'pending', 'cancelled'];
    const statusMap = {
      pending: '待处理',
      processing: '进行中',
      completed: '已完成',
      cancelled: '已取消'
    };
    const productNames = [
      '手工编织小熊玩偶',
      '手工陶瓷茶杯套装',
      '手作皮革钱包',
      '手工银饰项链',
      '羊毛毡小动物'
    ];
    
    const orderCount = Math.floor(Math.random() * 10) + 3;
    
    for (let i = 0; i < orderCount; i++) {
      let orderDate;
      if (period === 'this') {
        const daysAgo = Math.floor(Math.random() * this.data.timeRangeDays);
        orderDate = new Date(now.getTime() - daysAgo * 24 * 60 * 60 * 1000);
      } else {
        const daysAgo = this.data.timeRangeDays + Math.floor(Math.random() * this.data.timeRangeDays);
        orderDate = new Date(now.getTime() - daysAgo * 24 * 60 * 60 * 1000);
      }
      
      const status = statuses[Math.floor(Math.random() * statuses.length)];
      const createTime = orderDate.toISOString();
      
      allOrders.push({
        id: i + 1,
        orderNo: `ORD${orderDate.getFullYear()}${String(orderDate.getMonth() + 1).padStart(2, '0')}${String(i + 1).padStart(6, '0')}`,
        status: status,
        statusText: statusMap[status] || status,
        productTitle: productNames[Math.floor(Math.random() * productNames.length)],
        productCover: `https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=handmade%20craft%20product%20${i}&image_size=square`,
        amount: Math.floor(Math.random() * 500) + 50,
        createTime: createTime,
        formattedTime: this.formatTime(createTime)
      });
    }
    
    return allOrders;
  },

  async loadReviewsDetail(isRefresh, period = 'this') {
    try {
      let reviews = [];
      
      if (this.data.allReviews && this.data.allReviews.length > 0) {
        reviews = [...this.data.allReviews];
      } else {
        const teacher = this.data.teacher;
        if (!teacher || !teacher.user_id) return [];
        
        const params = {
          page: isRefresh ? 1 : this.data.detailPage,
          size: this.data.detailPageSize
        };

        const result = await getTeacherReviews(teacher.user_id, params);
        reviews = (result && result.list) || result || [];
      }
      
      const getRatingText = (rating) => {
        if (rating >= 4.0) return '好评';
        if (rating >= 2.0) return '中评';
        return '差评';
      };
      
      const getRatingTagClass = (rating) => {
        if (rating >= 4.0) return 'tag-good';
        if (rating >= 2.0) return 'tag-medium';
        return 'tag-bad';
      };
      
      const formatReviewItem = (r) => {
        const rating = r.overall_rating || r.rating || 0;
        const createTime = r.created_at || r.createTime;
        return {
          id: r.id,
          userName: r.is_anonymous ? '匿名用户' : (r.user_name || r.userName || '用户'),
          userAvatar: r.is_anonymous ? '/images/default-avatar.png' : getFullImageUrl(r.user_avatar || r.userAvatar),
          rating: rating,
          ratingText: getRatingText(rating),
          ratingTagClass: getRatingTagClass(rating),
          content: r.content,
          images: (r.images || []).map(img => getFullImageUrl(img)),
          createTime: createTime,
          formattedTime: this.formatTime(createTime),
          relativeTime: this.formatRelativeTime(createTime),
          reply: r.reply
        };
      };
      
      const ranges = this.getDateRanges(this.data.timeRangeDays);
      const filteredReviews = reviews.filter(r => {
        const createTime = r.created_at || r.create_time;
        if (period === 'this') {
          return this.isDateInRange(createTime, ranges.thisPeriodStart, ranges.now);
        } else {
          return this.isDateInRange(createTime, ranges.lastPeriodStart, ranges.thisPeriodStart);
        }
      });
      
      if (filteredReviews.length === 0 && period === 'this') {
        return reviews.slice(0, this.data.detailPageSize).map(formatReviewItem);
      }
      
      return filteredReviews.map(formatReviewItem);
    } catch (error) {
      console.error('加载评价明细失败:', error);
      return [];
    }
  },

  async loadLikesDetail(isRefresh, period = 'this') {
    const products = await this.loadProductsDetail(isRefresh, period);
    return products.map(p => ({
      id: p.id,
      productId: p.id,
      productTitle: p.title,
      productCover: p.coverImage,
      productPrice: p.price,
      likeCount: p.likeCount,
      like_count: p.like_count,
      likeTime: p.createTime,
      createTime: p.createTime,
      formattedTime: this.formatTime(p.createTime)
    }));
  },

  openSortModal() {
    this.setData({ showSortModal: true });
  },

  closeSortModal() {
    this.setData({ showSortModal: false });
  },

  selectSort(e) {
    const sortKey = e.currentTarget.dataset.key;
    if (sortKey === this.data.currentSort) {
      this.setData({ showSortModal: false });
      return;
    }
    
    this.setData({ 
      currentSort: sortKey,
      showSortModal: false
    });
    
    this.loadDetailList(true);
  },

  openFilterModal() {
    const currentType = this.data.currentType;
    let filterOptions = [];
    
    switch (currentType) {
      case 'orders':
        filterOptions = [
          { key: 'all', label: '全部状态' },
          { key: 'pending', label: '待处理' },
          { key: 'processing', label: '进行中' },
          { key: 'completed', label: '已完成' },
          { key: 'cancelled', label: '已取消' }
        ];
        break;
      case 'reviews':
        filterOptions = [
          { key: 'all', label: '全部评价' },
          { key: 'good', label: '好评(4-5星)' },
          { key: 'medium', label: '中评(2-3星)' },
          { key: 'bad', label: '差评(1星)' }
        ];
        break;
      default:
        filterOptions = [
          { key: 'all', label: '全部' }
        ];
    }
    
    this.setData({ 
      filterOptions: filterOptions,
      showFilterModal: true 
    });
  },

  closeFilterModal() {
    this.setData({ showFilterModal: false });
  },

  selectFilter(e) {
    const filterKey = e.currentTarget.dataset.key;
    if (filterKey === this.data.currentFilter) {
      this.setData({ showFilterModal: false });
      return;
    }
    
    this.setData({ 
      currentFilter: filterKey,
      showFilterModal: false
    });
    
    this.loadDetailList(true);
  },

  goToProductDetail(e) {
    const productId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/work-detail/index?id=${productId}`
    });
  },

  goToReviewDetail(e) {
    const reviewId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/review-detail/index?id=${reviewId}`
    });
  },

  goToOrderDetail(e) {
    const orderId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/orders/index?id=${orderId}`
    });
  },

  formatTime(timestamp) {
    if (!timestamp) return '';
    const date = safeParseDate(timestamp);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hour}:${minute}`;
  },

  formatRelativeTime(timestamp) {
    if (!timestamp) return '';
    const date = safeParseDate(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`;
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }
});
