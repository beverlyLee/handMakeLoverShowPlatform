const { applyTeacher } = require('../../api/users');
const { getSpecialties } = require('../../api/specialties');
const { showToast } = require('../../utils/util');
const storage = require('../../utils/storage');

Page({
  data: {
    formData: {
      real_name: '',
      id_card: '',
      phone: '',
      specialties: [],
      intro: ''
    },
    specialtyOptions: [],
    showSpecialtyPicker: false,
    introMaxLength: 500,
    introCurrentLength: 0,
    isSubmitting: false
  },

  onLoad() {
    console.log('手作老师入驻页面加载');
    this.loadSpecialties();
  },

  async loadSpecialties() {
    try {
      const specialties = await getSpecialties();
      if (specialties && Array.isArray(specialties)) {
        const options = specialties.map(item => ({
          label: item.name,
          value: item.name,
          checked: false
        }));
        this.setData({ specialtyOptions: options });
      }
    } catch (error) {
      console.error('加载擅长领域失败:', error);
      this.setData({
        specialtyOptions: [
          { label: '编织', value: '编织', checked: false },
          { label: '陶艺', value: '陶艺', checked: false },
          { label: '刺绣', value: '刺绣', checked: false },
          { label: '皮革', value: '皮革', checked: false },
          { label: '木工', value: '木工', checked: false },
          { label: '纸艺', value: '纸艺', checked: false },
          { label: '串珠', value: '串珠', checked: false },
          { label: '其他', value: '其他', checked: false }
        ]
      });
    }
  },

  onInputChange(e) {
    const { field } = e.currentTarget.dataset;
    const value = e.detail.value;
    const updateKey = `formData.${field}`;
    
    this.setData({
      [updateKey]: value
    });

    if (field === 'intro') {
      this.setData({
        introCurrentLength: value.length
      });
    }
  },

  toggleSpecialtyPicker() {
    this.setData({
      showSpecialtyPicker: !this.data.showSpecialtyPicker
    });
  },

  onSpecialtyChange(e) {
    const { index } = e.currentTarget.dataset;
    const specialtyOptions = [...this.data.specialtyOptions];
    specialtyOptions[index].checked = !specialtyOptions[index].checked;
    
    const selectedSpecialties = specialtyOptions
      .filter(item => item.checked)
      .map(item => item.value);
    
    this.setData({
      specialtyOptions,
      'formData.specialties': selectedSpecialties
    });
  },

  confirmSpecialty() {
    this.setData({
      showSpecialtyPicker: false
    });
  },

  validateForm() {
    const { formData } = this.data;
    
    if (!formData.real_name.trim()) {
      showToast('请输入真实姓名');
      return false;
    }
    
    if (!formData.id_card.trim()) {
      showToast('请输入身份证号');
      return false;
    }
    
    const idCardReg = /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/;
    if (!idCardReg.test(formData.id_card)) {
      showToast('请输入正确的身份证号');
      return false;
    }
    
    if (!formData.phone.trim()) {
      showToast('请输入手机号');
      return false;
    }
    
    const phoneReg = /^1[3-9]\d{9}$/;
    if (!phoneReg.test(formData.phone)) {
      showToast('请输入正确的手机号');
      return false;
    }
    
    if (formData.specialties.length === 0) {
      showToast('请至少选择一项擅长领域');
      return false;
    }
    
    return true;
  },

  async submitApply() {
    if (!this.validateForm()) {
      return;
    }

    if (this.data.isSubmitting) {
      return;
    }

    this.setData({ isSubmitting: true });
    wx.showLoading({ title: '提交中...', mask: true });

    try {
      const result = await applyTeacher(this.data.formData);
      console.log('入驻申请成功:', result);

      if (result.user) {
        storage.setUserInfo(result.user);
      }

      wx.hideLoading();
      
      wx.showModal({
        title: '提交成功',
        content: '您的老师入驻申请已提交，请等待管理员审核。审核通过后将获得老师身份。',
        showCancel: false,
        confirmText: '我知道了',
        success: () => {
          wx.switchTab({
            url: '/pages/user-center/index'
          });
        }
      });
    } catch (error) {
      console.error('入驻申请失败:', error);
      wx.hideLoading();
      this.setData({ isSubmitting: false });
      
      const errMsg = error.message || '入驻申请失败，请重试';
      wx.showModal({
        title: '申请失败',
        content: errMsg,
        showCancel: false
      });
    }
  },

  preventMove() {
    return;
  }
});
