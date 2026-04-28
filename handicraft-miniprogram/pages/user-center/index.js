const { getUserInfo, updateUserInfo, switchRole, getUserRoles } = require('../../api/users');
const { getTeacherOrderStats } = require('../../api/orders');
const { logout } = require('../../api/auth');
const { uploadImage } = require('../../api/upload');
const { showToast, processUserInfo, DEFAULT_IMAGE, getFullImageUrl } = require('../../utils/util');
const storage = require('../../utils/storage');

Page({
  data: {
    userInfo: {},
    genderText: '未知',
    isLoading: true,
    defaultAvatar: DEFAULT_IMAGE,

    showEditDialog: false,
    editDialogTitle: '',
    editField: '',
    editValue: '',

    showGenderPicker: false,
    genderOptions: [
      { value: 0, label: '未知' },
      { value: 1, label: '男' },
      { value: 2, label: '女' }
    ],
    bioLength: 0,

    canSwitchRole: false,
    userRoles: [],
    currentRole: 'customer',
    showRoleSwitchDialog: false,
    targetRole: '',
    isSwitching: false,

    orderStats: {},

    isTeacher: false,
    isCustomer: true,
    hasMultipleRoles: false
  },

  onLoad() {
    console.log('用户中心页面加载');
    this.initTestToken();
    this.loadUserInfo();
  },

  initTestToken() {
    const currentToken = storage.getToken();
    if (!currentToken) {
      storage.setToken('test_token');
      console.log('已设置测试 Token');
    }
  },

  onShow() {
    console.log('用户中心页面显示');
    this.loadUserInfo();
  },

  onReady() {
    console.log('用户中心页面渲染完成');
  },

  onPullDownRefresh() {
    this.loadUserInfo().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  async loadUserInfo() {
    this.setData({ isLoading: true });

    try {
      const userInfo = await getUserInfo();
      console.log('获取用户信息成功:', userInfo);

      const processedUserInfo = processUserInfo(userInfo);

      const genderText = this.getGenderText(processedUserInfo.gender);
      const bioLength = (processedUserInfo.bio || '').length;

      const roles = processedUserInfo.roles || ['customer'];
      const currentRole = processedUserInfo.current_role || processedUserInfo.role || 'customer';
      const hasMultipleRoles = roles.length > 1;
      const isTeacher = roles.includes('teacher');
      const isCustomer = roles.includes('customer');

      storage.setUserInfo(userInfo);

      this.setData({
        userInfo: processedUserInfo,
        genderText: genderText,
        bioLength: bioLength,
        isLoading: false,
        userRoles: roles,
        currentRole: currentRole,
        canSwitchRole: hasMultipleRoles,
        hasMultipleRoles: hasMultipleRoles,
        isTeacher: isTeacher,
        isCustomer: isCustomer
      });

      if (currentRole === 'teacher' && isTeacher) {
        this.loadTeacherOrderStats();
      }
    } catch (error) {
      console.error('获取用户信息失败:', error);
      this.setData({ isLoading: false });
      showToast('获取用户信息失败');
    }
  },

  async loadTeacherOrderStats() {
    try {
      const result = await getTeacherOrderStats();
      console.log('获取老师订单统计成功:', result);

      this.setData({
        orderStats: result.stats || {}
      });
    } catch (error) {
      console.error('获取老师订单统计失败:', error);
    }
  },

  getGenderText(gender) {
    switch (gender) {
      case 0:
        return '未知';
      case 1:
        return '男';
      case 2:
        return '女';
      default:
        return '未知';
    }
  },


  onTapRoleSwitch() {
    if (!this.data.canSwitchRole) {
      if (this.data.currentRole === 'customer' && !this.data.isTeacher) {
        wx.showModal({
          title: '提示',
          content: '您还没有手作老师身份，是否申请入驻？',
          confirmText: '去申请',
          success: (res) => {
            if (res.confirm) {
              wx.navigateTo({
                url: '/pages/teacher-apply/index'
              });
            }
          }
        });
      } else if (this.data.currentRole === 'teacher' && !this.data.isCustomer) {
        showToast('您只有手作老师身份');
      } else {
        showToast('无法切换身份');
      }
      return;
    }

    const currentRole = this.data.currentRole;
    const userRoles = this.data.userRoles;
    const targetRole = userRoles.find(r => r !== currentRole) || currentRole;

    const roleNames = {
      customer: '普通用户',
      teacher: '手作老师'
    };

    this.setData({
      targetRole: targetRole,
      showRoleSwitchDialog: true
    });
  },

  closeRoleSwitchDialog() {
    this.setData({
      showRoleSwitchDialog: false,
      targetRole: ''
    });
  },

  async confirmSwitchRole() {
    if (this.data.isSwitching) {
      return;
    }

    this.setData({ isSwitching: true });
    wx.showLoading({ title: '切换中...', mask: true });

    try {
      const result = await switchRole({ role: this.data.targetRole });
      console.log('角色切换成功:', result);

      if (result.user) {
        storage.setUserInfo(result.user);
      }

      wx.hideLoading();

      const roleNames = {
        customer: '普通用户',
        teacher: '手作老师'
      };

      this.setData({
        showRoleSwitchDialog: false,
        isSwitching: false,
        currentRole: this.data.targetRole,
        isTeacher: this.data.targetRole === 'teacher',
        isCustomer: this.data.targetRole === 'customer'
      });

      if (this.data.targetRole === 'teacher') {
        this.loadTeacherOrderStats();
      }

      showToast(`已切换到${roleNames[this.data.targetRole]}`, 'success');
    } catch (error) {
      console.error('角色切换失败:', error);
      wx.hideLoading();
      this.setData({ isSwitching: false });
      showToast('角色切换失败，请重试');
    }
  },

  onTapApplyTeacher() {
    wx.navigateTo({
      url: '/pages/teacher-apply/index'
    });
  },

  onTapViewOrders() {
    wx.switchTab({
      url: '/pages/orders/index'
    });
  },

  goToMyHome() {
    const userInfo = this.data.userInfo;
    if (userInfo && userInfo.teacher_info && userInfo.teacher_info.id) {
      wx.navigateTo({
        url: `/pages/teacher-home/index?id=${userInfo.teacher_info.id}`
      });
    } else {
      showToast('获取老师信息失败');
    }
  },

  chooseAvatar() {
    wx.showActionSheet({
      itemList: ['从相册选择', '拍照'],
      success: (res) => {
        const sourceType = res.tapIndex === 0 ? ['album'] : ['camera'];
        this.selectImage(sourceType);
      }
    });
  },

  selectImage(sourceType) {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: sourceType,
      success: async (res) => {
        const tempFilePath = res.tempFiles[0].tempFilePath;
        console.log('选择图片成功:', tempFilePath);

        this.setData({
          'userInfo.avatar': tempFilePath
        });

        try {
          console.log('开始上传图片到服务器...');
          const uploadResult = await uploadImage(tempFilePath);
          console.log('图片上传成功:', uploadResult);
          
          const serverUrl = uploadResult.url;
          const fullImageUrl = getFullImageUrl(serverUrl);
          
          wx.showLoading({ title: '更新中...', mask: true });

          await updateUserInfo({
            avatar: serverUrl
          });

          this.setData({
            'userInfo.avatar': fullImageUrl
          });

          wx.hideLoading();
          showToast('头像更新成功', 'success');
        } catch (error) {
          console.error('更新头像失败:', error);
          wx.hideLoading();
          showToast('头像更新失败，请重试');
        }
      },
      fail: (err) => {
        console.log('选择图片失败:', err);
      }
    });
  },

  showEditDialog(e) {
    const { field, title } = e.currentTarget.dataset;
    const { userInfo } = this.data;

    let value = '';
    if (field === 'bio') {
      value = userInfo.bio || '';
    } else if (field === 'nickname') {
      value = userInfo.nickname || '';
    } else if (field === 'username') {
      value = userInfo.username || '';
    } else if (field === 'phone') {
      value = userInfo.phone || '';
    } else if (field === 'email') {
      value = userInfo.email || '';
    }

    this.setData({
      showEditDialog: true,
      editDialogTitle: title,
      editField: field,
      editValue: value
    });
  },

  closeEditDialog() {
    this.setData({
      showEditDialog: false,
      editDialogTitle: '',
      editField: '',
      editValue: ''
    });
  },

  onEditInput(e) {
    const value = e.detail.value;
    this.setData({
      editValue: value
    });
  },

  async saveEdit() {
    const { editField, editValue, userInfo } = this.data;

    console.log('【调试】saveEdit 被调用');
    console.log('【调试】editField:', editField);
    console.log('【调试】editValue:', editValue);

    const originalValue = this.getOriginalValue(editField, userInfo);
    console.log('【调试】originalValue:', originalValue);
    console.log('【调试】是否相等:', editValue === originalValue);

    if (editValue === originalValue) {
      console.log('【调试】值未改变，不调用接口');
      this.closeEditDialog();
      return;
    }

    console.log('【调试】准备调用 updateUserInfo 接口');

    wx.showLoading({ title: '保存中...', mask: true });

    try {
      const updateData = {};
      updateData[editField] = editValue;

      const result = await updateUserInfo(updateData);
      console.log('更新用户信息成功:', result);

      const updateKey = `userInfo.${editField}`;
      const pageData = {
        [updateKey]: editValue
      };

      if (editField === 'bio') {
        pageData.bioLength = editValue.length;
      }

      this.setData(pageData);

      wx.hideLoading();
      showToast('保存成功', 'success');
      this.closeEditDialog();
    } catch (error) {
      console.error('更新用户信息失败:', error);
      wx.hideLoading();
      showToast('保存失败，请重试');
    }
  },

  getOriginalValue(field, userInfo) {
    switch (field) {
      case 'bio':
        return userInfo.bio || '';
      case 'nickname':
        return userInfo.nickname || '';
      case 'username':
        return userInfo.username || '';
      case 'phone':
        return userInfo.phone || '';
      case 'email':
        return userInfo.email || '';
      default:
        return '';
    }
  },

  showGenderPicker() {
    this.setData({
      showGenderPicker: true
    });
  },

  closeGenderPicker() {
    this.setData({
      showGenderPicker: false
    });
  },

  async onGenderChange(e) {
    const selectedIndex = e.detail.value;
    const { genderOptions, userInfo } = this.data;
    const selectedGender = genderOptions[selectedIndex];

    if (selectedGender.value === userInfo.gender) {
      this.closeGenderPicker();
      return;
    }

    wx.showLoading({ title: '保存中...', mask: true });

    try {
      await updateUserInfo({
        gender: selectedGender.value
      });

      this.setData({
        'userInfo.gender': selectedGender.value,
        genderText: selectedGender.label
      });

      wx.hideLoading();
      showToast('保存成功', 'success');
      this.closeGenderPicker();
    } catch (error) {
      console.error('更新性别失败:', error);
      wx.hideLoading();
      showToast('保存失败，请重试');
    }
  },

  async handleLogout() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      confirmColor: '#DC3545',
      success: async (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '退出中...', mask: true });

          try {
            await logout();
          } catch (error) {
            console.log('退出登录接口调用失败，继续清除本地数据:', error);
          }

          storage.removeToken();
          storage.removeUserInfo();

          wx.hideLoading();
          showToast('已退出登录', 'success');

          setTimeout(() => {
            wx.reLaunch({
              url: '/pages/home/index'
            });
          }, 1500);
        }
      }
    });
  },

  preventMove() {
    return;
  },

  goToAddressManage() {
    wx.navigateTo({
      url: '/pages/address-list/index'
    });
  },

  onShareAppMessage() {
    return {
      title: '手工爱好者平台 - 个人中心',
      path: '/pages/user-center/index'
    };
  }
});
