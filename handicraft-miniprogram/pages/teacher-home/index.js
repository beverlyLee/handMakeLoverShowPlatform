const { getTeacherPublicInfo, getTeacherPublicOrderStats, getUserInfo, updateTeacherInfo, updateUserInfo } = require('../../api/users');
const { getProducts, createProduct, getCategories, updateProduct, deleteProduct } = require('../../api/products');
const { getSpecialties } = require('../../api/specialties');
const { showToast } = require('../../utils/util');
const storage = require('../../utils/storage');

const DEFAULT_SPECIALTIES = [
  { label: '棒针编织', value: '棒针编织', checked: false },
  { label: '钩针编织', value: '钩针编织', checked: false },
  { label: '编织', value: '编织', checked: false },
  { label: '陶艺', value: '陶艺', checked: false },
  { label: '拉坯', value: '拉坯', checked: false },
  { label: '釉上彩', value: '釉上彩', checked: false },
  { label: '皮革工艺', value: '皮革工艺', checked: false },
  { label: '刺绣', value: '刺绣', checked: false },
  { label: '纸艺', value: '纸艺', checked: false },
  { label: '珠串', value: '珠串', checked: false },
  { label: '木艺', value: '木艺', checked: false },
  { label: '布艺', value: '布艺', checked: false },
  { label: '手工皂', value: '手工皂', checked: false },
  { label: '蜡烛', value: '蜡烛', checked: false },
  { label: '押花', value: '押花', checked: false },
  { label: '热缩片', value: '热缩片', checked: false },
  { label: '滴胶', value: '滴胶', checked: false },
  { label: '黏土', value: '黏土', checked: false }
];

let specialtyList = [...DEFAULT_SPECIALTIES];

function createSpecialtyOptions(selectedSpecialties = []) {
  return specialtyList.map(option => ({
    ...option,
    checked: selectedSpecialties.indexOf(option.value) > -1
  }));
}

Page({
  data: {
    teacherId: null,
    teacher: null,
    products: [],
    productsTotal: 0,
    orderStats: null,
    recentOrders: [],
    currentTab: 'orders',
    isLoading: true,
    productsLoading: false,
    productsPage: 1,
    productsPageSize: 10,
    productsHasMore: true,
    ordersLoading: false,
    currentUser: null,
    isOwner: false,
    
    specialtyOptions: [],
    
    showEditDialog: false,
    editDialogField: '',
    editDialogTitle: '',
    editDialogValue: '',
    editDialogType: 'input',
    savingEdit: false,
    
    showSpecialtiesDialog: false,
    tempSpecialties: [],
    
    showStudioDialog: false,
    studioEditForm: {
      name: '',
      address: ''
    },
    
    showProductCreate: false,
    categories: [],
    productForm: {
      title: '',
      description: '',
      category_id: null,
      category_name: '',
      price: '',
      original_price: '',
      stock: 999,
      tags: [],
      images: [],
      cover_image: ''
    },
    creatingProduct: false,
    isEditingProduct: false,
    editingProductId: null
  },

  onLoad(options) {
    const teacherId = options.id;
    const tab = options.tab || 'orders';
    
    if (!teacherId) {
      showToast('参数错误');
      wx.navigateBack();
      return;
    }

    this.setData({ 
      teacherId: parseInt(teacherId),
      currentTab: tab
    });
    this.loadAllData();
  },

  onPullDownRefresh() {
    this.setData({
      productsPage: 1,
      productsHasMore: true,
      products: [],
      isRefreshing: true
    });
    this.loadAllData().then(() => {
      wx.stopPullDownRefresh();
      this.setData({ isRefreshing: false });
    });
  },

  onReachBottom() {
    if (this.data.currentTab === 'products' && this.data.productsHasMore && !this.data.productsLoading) {
      this.setData({
        productsPage: this.data.productsPage + 1
      });
      this.loadTeacherProducts(true);
    }
  },

  onShareAppMessage() {
    const teacher = this.data.teacher;
    const teacherName = (teacher && teacher.user_info && teacher.user_info.nickname) || (teacher && teacher.real_name) || '手作老师';
    return {
      title: teacherName,
      path: `/pages/teacher-home/index?id=${this.data.teacherId}`
    };
  },

  async loadAllData() {
    this.setData({ isLoading: true });
    
    try {
      await Promise.all([
        this.loadCurrentUser(),
        this.loadTeacherInfo(),
        this.loadCategories(),
        this.loadSpecialties(),
        this.loadTeacherProducts()
      ]);
      
      if (this.data.currentTab === 'orders' && this.data.recentOrders.length === 0 && !this.data.orderStats) {
        await this.loadOrderStats();
      }
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
        console.log('用户未登录，不判断是否为所有者');
        const cachedUser = storage.getUserInfo();
        if (cachedUser) {
          this.setData({ currentUser: cachedUser });
        }
        return;
      }
      
      try {
        const userInfo = await getUserInfo();
        if (userInfo) {
          this.setData({ currentUser: userInfo });
          this.checkIsOwner();
        }
      } catch (apiError) {
        console.log('API获取用户信息失败，尝试使用缓存:', apiError);
        const cachedUser = storage.getUserInfo();
        if (cachedUser) {
          this.setData({ currentUser: cachedUser });
          this.checkIsOwner();
        }
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
      console.log('判断是否为所有者:', { 
        teacherUserId: teacher.user_id, 
        currentUserId: currentUser.id, 
        isOwner: isOwner 
      });
    }
  },

  async loadTeacherInfo() {
    try {
      const teacher = await getTeacherPublicInfo(this.data.teacherId);
      const specialties = (teacher && teacher.specialties) || [];
      
      this.setData({ 
        teacher: teacher,
        specialtyOptions: createSpecialtyOptions(specialties)
      });
      
      this.checkIsOwner();
    } catch (error) {
      console.error('加载老师信息失败:', error);
      showToast('加载老师信息失败');
    }
  },

  async loadCategories() {
    try {
      const categories = await getCategories();
      this.setData({ categories: categories || [] });
    } catch (error) {
      console.error('加载分类失败:', error);
    }
  },

  async loadSpecialties() {
    try {
      const specialties = await getSpecialties();
      if (specialties && Array.isArray(specialties)) {
        specialtyList = specialties.map(item => ({
          label: item.name,
          value: item.name,
          checked: false
        }));
      }
    } catch (error) {
      console.error('加载擅长领域失败:', error);
      specialtyList = [...DEFAULT_SPECIALTIES];
    }
  },

  async loadTeacherProducts(append = false) {
    if (this.data.productsLoading) return;

    this.setData({ productsLoading: true });

    try {
      const params = {
        page: append ? this.data.productsPage : 1,
        size: this.data.productsPageSize,
        teacher_id: this.data.teacherId,
        sort: 'newest'
      };

      const result = await getProducts(params);
      const newProducts = (result && result.list) || result || [];
      const total = (result && result.total) || newProducts.length;

      if (append) {
        this.setData({
          products: [...this.data.products, ...newProducts],
          productsTotal: total,
          productsHasMore: newProducts.length >= this.data.productsPageSize,
          productsLoading: false
        });
      } else {
        this.setData({
          products: newProducts,
          productsTotal: total,
          productsPage: 1,
          productsHasMore: newProducts.length >= this.data.productsPageSize,
          productsLoading: false
        });
      }
    } catch (error) {
      console.error('加载老师作品失败:', error);
      this.setData({ productsLoading: false });
      showToast('加载作品失败');
    }
  },

  async loadOrderStats() {
    this.setData({ ordersLoading: true });
    
    try {
      const result = await getTeacherPublicOrderStats(this.data.teacherId);
      this.setData({
        orderStats: result.stats,
        recentOrders: result.recent_orders || [],
        statusNames: result.status_names,
        ordersLoading: false
      });
    } catch (error) {
      console.error('加载订单统计失败:', error);
      this.setData({ ordersLoading: false });
    }
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ currentTab: tab });
    
    if (tab === 'products' && this.data.products.length === 0) {
      this.loadTeacherProducts();
    }
    if (tab === 'orders' && this.data.recentOrders.length === 0 && !this.data.orderStats) {
      this.loadOrderStats();
    }
  },

  goToProductDetail(e) {
    const productId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/work-detail/index?id=${productId}`
    });
  },

  goToProductList() {
    wx.navigateTo({
      url: `/pages/products/index?teacher_id=${this.data.teacherId}`
    });
  },

  followTeacher() {
    showToast('关注功能开发中');
  },

  contactTeacher() {
    showToast('联系老师功能开发中');
  },

  goToEditInfo() {
    wx.navigateTo({
      url: '/pages/teacher-info-edit/index'
    });
  },

  goToEditProfile() {
    showToast('请在当前页面点击编辑按钮');
  },

  goToManage() {
    showToast('管理后台功能开发中');
  },

  previewStudioImage(e) {
    const url = e.currentTarget.dataset.url;
    const images = this.data.teacher.studio_images || [];
    
    wx.previewImage({
      current: url,
      urls: images
    });
  },

  openEditDialog(e) {
    const { field, title, value, type } = e.currentTarget.dataset;
    
    this.setData({
      showEditDialog: true,
      editDialogField: field,
      editDialogTitle: title,
      editDialogValue: value || '',
      editDialogType: type || 'input'
    });
  },

  closeEditDialog() {
    this.setData({
      showEditDialog: false,
      editDialogField: '',
      editDialogTitle: '',
      editDialogValue: '',
      editDialogType: 'input'
    });
  },

  onEditInput(e) {
    const value = e.detail.value;
    this.setData({
      editDialogValue: value
    });
  },

  async saveEditDialog() {
    const { editDialogField, editDialogValue, teacher } = this.data;
    
    if (!editDialogField) return;
    
    this.setData({ savingEdit: true });
    wx.showLoading({ title: '保存中...', mask: true });
    
    try {
      const updateData = {};
      
      if (editDialogField === 'experience_years') {
        updateData[editDialogField] = parseInt(editDialogValue) || 0;
      } else {
        updateData[editDialogField] = editDialogValue;
      }
      
      if (editDialogField === 'nickname') {
        await updateUserInfo(updateData);
        
        const updatedTeacher = {
          ...teacher,
          user_info: {
            ...teacher.user_info,
            nickname: editDialogValue
          }
        };
        
        this.setData({
          teacher: updatedTeacher,
          savingEdit: false
        });
      } else {
        await updateTeacherInfo(updateData);
        
        const updatedTeacher = {
          ...teacher,
          ...updateData
        };
        
        this.setData({
          teacher: updatedTeacher,
          savingEdit: false
        });
      }
      
      wx.hideLoading();
      this.closeEditDialog();
      showToast('保存成功', 'success');
    } catch (error) {
      console.error('保存失败:', error);
      wx.hideLoading();
      this.setData({ savingEdit: false });
      showToast('保存失败，请重试');
    }
  },

  openSpecialtiesEdit() {
    const teacher = this.data.teacher;
    const specialties = (teacher && teacher.specialties) || [];
    
    this.setData({
      showSpecialtiesDialog: true,
      specialtyOptions: createSpecialtyOptions(specialties),
      tempSpecialties: [...specialties]
    });
  },

  closeSpecialtiesDialog() {
    this.setData({
      showSpecialtiesDialog: false
    });
  },

  toggleSpecialtyItem(e) {
    const index = e.currentTarget.dataset.index;
    const specialtyOptions = [...this.data.specialtyOptions];
    const option = specialtyOptions[index];
    
    option.checked = !option.checked;
    
    const selectedSpecialties = specialtyOptions
      .filter(item => item.checked)
      .map(item => item.value);
    
    this.setData({
      specialtyOptions: specialtyOptions,
      tempSpecialties: selectedSpecialties
    });
  },

  async saveSpecialtiesDialog() {
    const { tempSpecialties, teacher } = this.data;
    
    this.setData({ savingEdit: true });
    wx.showLoading({ title: '保存中...', mask: true });
    
    try {
      await updateTeacherInfo({
        specialties: tempSpecialties
      });
      
      const updatedTeacher = {
        ...teacher,
        specialties: tempSpecialties
      };
      
      this.setData({
        teacher: updatedTeacher,
        savingEdit: false
      });
      
      wx.hideLoading();
      this.closeSpecialtiesDialog();
      showToast('保存成功', 'success');
    } catch (error) {
      console.error('保存失败:', error);
      wx.hideLoading();
      this.setData({ savingEdit: false });
      showToast('保存失败，请重试');
    }
  },

  openStudioEdit() {
    const teacher = this.data.teacher;
    
    this.setData({
      showStudioDialog: true,
      studioEditForm: {
        name: (teacher && teacher.studio_name) || '',
        address: (teacher && teacher.studio_address) || ''
      }
    });
  },

  closeStudioDialog() {
    this.setData({
      showStudioDialog: false
    });
  },

  onStudioNameInput(e) {
    const value = e.detail.value;
    this.setData({
      'studioEditForm.name': value
    });
  },

  onStudioAddressInput(e) {
    const value = e.detail.value;
    this.setData({
      'studioEditForm.address': value
    });
  },

  async saveStudioDialog() {
    const { studioEditForm, teacher } = this.data;
    
    this.setData({ savingEdit: true });
    wx.showLoading({ title: '保存中...', mask: true });
    
    try {
      await updateTeacherInfo({
        studio_name: studioEditForm.name,
        studio_address: studioEditForm.address
      });
      
      const updatedTeacher = {
        ...teacher,
        studio_name: studioEditForm.name,
        studio_address: studioEditForm.address
      };
      
      this.setData({
        teacher: updatedTeacher,
        savingEdit: false
      });
      
      wx.hideLoading();
      this.closeStudioDialog();
      showToast('保存成功', 'success');
    } catch (error) {
      console.error('保存失败:', error);
      wx.hideLoading();
      this.setData({ savingEdit: false });
      showToast('保存失败，请重试');
    }
  },

  openProductCreate() {
    this.setData({
      showProductCreate: true,
      isEditingProduct: false,
      editingProductId: null,
      productForm: {
        title: '',
        description: '',
        category_id: null,
        category_name: '',
        price: '',
        original_price: '',
        stock: 999,
        tags: [],
        images: [],
        cover_image: ''
      }
    });
  },

  openProductEdit(e) {
    const product = e.currentTarget.dataset.product;
    if (!product) return;

    const { categories } = this.data;
    let category_name = '';
    if (product.category_id && categories) {
      const cat = categories.find(c => c.id === product.category_id);
      if (cat) {
        category_name = cat.name;
      }
    }

    this.setData({
      showProductCreate: true,
      isEditingProduct: true,
      editingProductId: product.id,
      productForm: {
        title: product.title || '',
        description: product.description || '',
        category_id: product.category_id || null,
        category_name: category_name || '',
        price: product.price ? String(product.price) : '',
        original_price: product.original_price ? String(product.original_price) : '',
        stock: product.stock ? String(product.stock) : '999',
        tags: product.tags || [],
        images: product.images || [],
        cover_image: product.cover_image || ''
      }
    });
  },

  closeProductCreate() {
    this.setData({ 
      showProductCreate: false,
      isEditingProduct: false,
      editingProductId: null
    });
  },

  onProductInput(e) {
    const field = e.currentTarget.dataset.field;
    const value = e.detail.value;
    
    this.setData({
      [`productForm.${field}`]: value
    });
  },

  onCategoryChange(e) {
    const index = e.detail.value;
    const categories = this.data.categories;
    
    if (categories && categories[index]) {
      this.setData({
        'productForm.category_id': categories[index].id,
        'productForm.category_name': categories[index].name
      });
    }
  },

  chooseImages() {
    const self = this;
    wx.chooseImage({
      count: 9,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success(res) {
        const tempFilePaths = res.tempFilePaths;
        const currentImages = self.data.productForm.images;
        const newImages = [...currentImages, ...tempFilePaths].slice(0, 9);
        
        self.setData({
          'productForm.images': newImages,
          'productForm.cover_image': newImages[0] || ''
        });
      }
    });
  },

  removeImage(e) {
    const index = e.currentTarget.dataset.index;
    const images = [...this.data.productForm.images];
    images.splice(index, 1);
    
    this.setData({
      'productForm.images': images,
      'productForm.cover_image': images[0] || ''
    });
  },

  async createProduct() {
    const { productForm, teacher, isEditingProduct, editingProductId } = this.data;
    
    if (!productForm.title) {
      showToast('请填写作品标题');
      return;
    }
    if (!productForm.price) {
      showToast('请填写作品价格');
      return;
    }
    
    this.setData({ creatingProduct: true });
    
    try {
      const productData = {
        title: productForm.title,
        description: productForm.description,
        category_id: productForm.category_id,
        price: parseFloat(productForm.price) || 0,
        original_price: parseFloat(productForm.original_price) || parseFloat(productForm.price) || 0,
        stock: parseInt(productForm.stock) || 999,
        status: 'active',
        tags: productForm.tags,
        images: productForm.images,
        cover_image: productForm.cover_image
      };
      
      if (productData.images.length === 0) {
        productData.images = [
          'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=handmade%20craft%20artwork%20elegant%20handcrafted%20product&image_size=square'
        ];
        productData.cover_image = productData.images[0];
      }
      
      if (isEditingProduct && editingProductId) {
        await updateProduct(editingProductId, productData);
        showToast('作品更新成功');
      } else {
        await createProduct(productData);
        const newProductCount = ((teacher && teacher.product_count) || 0) + 1;
        this.setData({
          'teacher.product_count': newProductCount
        });
        showToast('作品创建成功');
      }
      
      this.setData({
        showProductCreate: false,
        creatingProduct: false,
        isEditingProduct: false,
        editingProductId: null,
        products: [],
        productsPage: 1
      });
      
      this.loadTeacherProducts();
    } catch (error) {
      console.error(isEditingProduct ? '更新作品失败:' : '创建作品失败:', error);
      this.setData({ creatingProduct: false });
      showToast(isEditingProduct ? '更新失败，请重试' : '创建失败，请重试');
    }
  },

  deleteProduct(e) {
    const product = e.currentTarget.dataset.product;
    if (!product) return;

    const self = this;
    wx.showModal({
      title: '确认删除',
      content: '确定要删除该作品吗？删除后无法恢复。',
      success: async (res) => {
        if (res.confirm) {
          try {
            await deleteProduct(product.id);
            
            const newProductCount = Math.max(0, ((self.data.teacher && self.data.teacher.product_count) || 1) - 1);
            
            self.setData({
              products: [],
              productsPage: 1,
              'teacher.product_count': newProductCount
            });
            
            self.loadTeacherProducts();
            showToast('作品已删除');
          } catch (error) {
            console.error('删除作品失败:', error);
            showToast('删除失败，请重试');
          }
        }
      }
    });
  },

  preventMove() {
    return;
  },

  getStatusColor(status) {
    const colors = {
      pending: '#999999',
      paid: '#FF9800',
      shipped: '#2196F3',
      delivered: '#9C27B0',
      completed: '#4CAF50',
      cancelled: '#F44336'
    };
    return colors[status] || '#999999';
  }
});