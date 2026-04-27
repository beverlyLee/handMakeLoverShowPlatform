const { getTeacherPublicInfo, getTeacherInfo, updateTeacherInfo, getUserInfo } = require('../../api/users');
const { getProducts, createProduct, getCategories } = require('../../api/products');
const { showToast } = require('../../utils/util');
const storage = require('../../utils/storage');

const SPECIALTY_OPTIONS = [
  '棒针编织', '钩针编织', '编织',
  '陶艺', '拉坯', '釉上彩',
  '皮革工艺', '刺绣', '纸艺',
  '珠串', '木艺', '布艺',
  '手工皂', '蜡烛', '押花',
  '热缩片', '滴胶', '黏土'
];

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
    isEditMode: false,
    
    editForm: {
      real_name: '',
      intro: '',
      bio: '',
      studio_name: '',
      studio_address: '',
      experience_years: 0,
      specialties: [],
      certifications: []
    },
    
    specialtyOptions: SPECIALTY_OPTIONS,
    
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
      path: `/pages/teacher-profile/index?id=${this.data.teacherId}`
    };
  },

  async loadAllData() {
    this.setData({ isLoading: true });
    
    try {
      await Promise.all([
        this.loadCurrentUser(),
        this.loadTeacherInfo(),
        this.loadCategories()
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
      
      this.setData({
        teacher: teacher,
        editForm: {
          real_name: teacher.real_name || '',
          intro: teacher.intro || '',
          bio: teacher.bio || '',
          studio_name: teacher.studio_name || '',
          studio_address: teacher.studio_address || '',
          experience_years: teacher.experience_years || 0,
          specialties: teacher.specialties || [],
          certifications: teacher.certifications || []
        }
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

  enterEditMode() {
    this.setData({ isEditMode: true });
  },

  cancelEditMode() {
    this.setData({
      isEditMode: false,
      editForm: {
        real_name: this.data.teacher.real_name || '',
        intro: this.data.teacher.intro || '',
        bio: this.data.teacher.bio || '',
        studio_name: this.data.teacher.studio_name || '',
        studio_address: this.data.teacher.studio_address || '',
        experience_years: this.data.teacher.experience_years || 0,
        specialties: this.data.teacher.specialties || [],
        certifications: this.data.teacher.certifications || []
      }
    });
  },

  onInputChange(e) {
    const field = e.currentTarget.dataset.field;
    const value = e.detail.value;
    
    this.setData({
      [`editForm.${field}`]: value
    });
  },

  toggleSpecialty(e) {
    const specialty = e.currentTarget.dataset.specialty;
    const specialties = [...this.data.editForm.specialties];
    const index = specialties.indexOf(specialty);
    
    if (index > -1) {
      specialties.splice(index, 1);
    } else {
      specialties.push(specialty);
    }
    
    this.setData({
      'editForm.specialties': specialties
    });
  },

  async saveTeacherInfo() {
    const { editForm } = this.data;
    
    if (!editForm.real_name) {
      showToast('请填写真实姓名');
      return;
    }
    
    try {
      const updateData = {
        real_name: editForm.real_name,
        intro: editForm.intro,
        bio: editForm.bio,
        studio_name: editForm.studio_name,
        studio_address: editForm.studio_address,
        experience_years: parseInt(editForm.experience_years) || 0,
        specialties: editForm.specialties,
        certifications: editForm.certifications
      };
      
      await updateTeacherInfo(updateData);
      
      this.setData({
        teacher: {
          ...this.data.teacher,
          ...updateData
        },
        isEditMode: false
      });
      
      showToast('保存成功');
    } catch (error) {
      console.error('保存老师信息失败:', error);
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
  }
});
