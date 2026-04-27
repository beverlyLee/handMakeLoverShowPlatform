const { getTeacherPublicInfo, getTeacherInfo, updateTeacherInfo, getUserInfo } = require('../../api/users');
const { getProducts, createProduct, getCategories } = require('../../api/products');
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
    currentTab: 'info',
    isLoading: true,
    productsLoading: false,
    productsPage: 1,
    productsPageSize: 10,
    productsHasMore: true,
    
    isOwner: false,
    currentUser: null,
    
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
      price: '',
      original_price: '',
      stock: 999,
      tags: [],
      images: [],
      cover_image: ''
    },
    creatingProduct: false
  },

  onLoad(options) {
    const teacherId = options.id;
    const tab = options.tab || 'info';
    
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

  onShareAppMessage() {
    const teacher = this.data.teacher;
    return {
      title: (teacher && teacher.real_name) || '手作老师',
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
        this.loadSpecialties()
      ]);
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      this.setData({ isLoading: false });
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

  async loadCurrentUser() {
    try {
      const token = storage.getToken();
      if (!token) {
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
        }
      } catch (apiError) {
        console.log('API获取用户信息失败，尝试使用缓存:', apiError);
        const cachedUser = storage.getUserInfo();
        if (cachedUser) {
          this.setData({ currentUser: cachedUser });
        }
      }
    } catch (error) {
      console.log('获取当前用户信息失败:', error);
    }
  },

  async loadTeacherInfo() {
    try {
      const teacher = await getTeacherPublicInfo(this.data.teacherId);
      const specialties = teacher.specialties || [];
      
      this.setData({
        teacher: teacher,
        specialtyOptions: createSpecialtyOptions(specialties)
      });
      
      this.checkIsOwner();
      
      if (this.data.currentTab === 'products') {
        this.loadTeacherProducts();
      }
    } catch (error) {
      console.error('加载老师信息失败:', error);
      showToast('加载失败，请重试');
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

  async loadCategories() {
    try {
      const categories = await getCategories();
      this.setData({ categories: categories || [] });
    } catch (error) {
      console.error('加载分类失败:', error);
    }
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ currentTab: tab });
    
    if (tab === 'products' && this.data.products.length === 0) {
      this.loadTeacherProducts();
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

      if (append) {
        this.setData({
          products: [...this.data.products, ...newProducts],
          productsHasMore: newProducts.length >= this.data.productsPageSize,
          productsLoading: false
        });
      } else {
        this.setData({
          products: newProducts,
          productsPage: 1,
          productsHasMore: newProducts.length >= this.data.productsPageSize,
          productsLoading: false
        });
      }
    } catch (error) {
      console.error('加载老师作品失败:', error);
      this.setData({ productsLoading: false });
      showToast('加载失败，请重试');
    }
  },

  onReachBottom() {
    if (this.data.currentTab === 'products' && this.data.productsHasMore && !this.data.productsLoading) {
      this.setData({
        productsPage: this.data.productsPage + 1
      });
      this.loadTeacherProducts(true);
    }
  },

  goToProductDetail(e) {
    const productId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/work-detail/index?id=${productId}`
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
      
      await updateTeacherInfo(updateData);
      
      const updatedTeacher = {
        ...teacher,
        ...updateData
      };
      
      this.setData({
        teacher: updatedTeacher,
        savingEdit: false
      });
      
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
    const specialties = teacher.specialties || [];
    
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
        name: teacher.studio_name || '',
        address: teacher.studio_address || ''
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

  closeProductCreate() {
    this.setData({ showProductCreate: false });
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
    const { productForm, categories } = this.data;
    
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
      const createData = {
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
      
      if (createData.images.length === 0) {
        createData.images = [
          'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=handmade%20craft%20artwork%20elegant%20handcrafted%20product&image_size=square'
        ];
        createData.cover_image = createData.images[0];
      }
      
      await createProduct(createData);
      
      this.setData({
        showProductCreate: false,
        creatingProduct: false,
        products: [],
        productsPage: 1
      });
      
      this.loadTeacherProducts();
      showToast('作品创建成功');
    } catch (error) {
      console.error('创建作品失败:', error);
      this.setData({ creatingProduct: false });
      showToast('创建失败，请重试');
    }
  },

  preventMove() {
    return;
  }
});