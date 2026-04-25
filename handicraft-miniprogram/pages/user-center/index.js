const { getUserInfo, updateUserInfo } = require('../../api/users');
const { showToast } = require('../../utils/util');

Page({
  data: {
    userInfo: {},
    genderText: '未知',
    isEditingBio: false,
    editBioValue: '',
    isLoading: true
  },

  onLoad() {
    console.log('用户中心页面加载');
    this.loadUserInfo();
  },

  onShow() {
    console.log('用户中心页面显示');
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setSelected(4)
    }
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

      const genderText = this.getGenderText(userInfo.gender);

      this.setData({
        userInfo: userInfo,
        genderText: genderText,
        editBioValue: userInfo.bio || '',
        isLoading: false
      });
    } catch (error) {
      console.error('获取用户信息失败:', error);
      this.setData({ isLoading: false });
      showToast('获取用户信息失败');
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

  toggleBioEdit() {
    const { isEditingBio, userInfo, editBioValue } = this.data;

    if (isEditingBio) {
      this.saveBio();
    } else {
      this.setData({
        isEditingBio: true,
        editBioValue: userInfo.bio || ''
      });
    }
  },

  onBioInput(e) {
    const value = e.detail.value;
    this.setData({
      editBioValue: value
    });
  },

  async saveBio() {
    const { editBioValue, userInfo } = this.data;

    if (editBioValue === userInfo.bio) {
      this.setData({
        isEditingBio: false
      });
      return;
    }

    wx.showLoading({
      title: '保存中...',
      mask: true
    });

    try {
      const result = await updateUserInfo({
        bio: editBioValue
      });

      console.log('更新个人简介成功:', result);

      this.setData({
        'userInfo.bio': editBioValue,
        isEditingBio: false
      });

      wx.hideLoading();
      showToast('保存成功', 'success');
    } catch (error) {
      console.error('更新个人简介失败:', error);
      wx.hideLoading();
      showToast('保存失败，请重试');
    }
  },

  onShareAppMessage() {
    return {
      title: '手工爱好者平台 - 个人中心',
      path: '/pages/user-center/index'
    };
  }
});
