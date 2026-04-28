const { getTeacherInfo, updateTeacherInfo } = require('../../api/users');
const { getSpecialties } = require('../../api/specialties');
const { showToast } = require('../../utils/util');
const storage = require('../../utils/storage');

Page({
  data: {
    formData: {
      real_name: '',
      id_card: '',
      id_card_original: '',
      phone: '',
      phone_original: '',
      specialties: [],
      intro: ''
    },
    specialtyOptions: [],
    showSpecialtyPicker: false,
    isSubmitting: false
  },

  onLoad() {
    this.loadAllData();
  },

  async loadAllData() {
    try {
      const teacher = await getTeacherInfo();
      
      if (teacher) {
        let selectedSpecialties = teacher.specialties;
        
        if (typeof selectedSpecialties === 'string') {
          try {
            selectedSpecialties = JSON.parse(selectedSpecialties);
          } catch (e) {
            selectedSpecialties = selectedSpecialties.split(',').map(s => s.trim()).filter(s => s);
          }
        }
        
        if (!Array.isArray(selectedSpecialties)) {
          selectedSpecialties = [];
        }
        
        this.setData({
          formData: {
            real_name: teacher.real_name || '',
            id_card: this.maskIdCard(teacher.id_card || ''),
            id_card_original: teacher.id_card || '',
            phone: this.maskPhone(teacher.phone || ''),
            phone_original: teacher.phone || '',
            specialties: selectedSpecialties,
            intro: teacher.intro || ''
          }
        });
        
        await this.loadSpecialties(selectedSpecialties);
      }
    } catch (error) {
      console.error('加载数据失败:', error);
      showToast('加载失败，请重试');
    }
  },

  async loadTeacherInfo() {
    try {
      const teacher = await getTeacherInfo();
      
      if (teacher) {
        let selectedSpecialties = teacher.specialties;
        
        if (typeof selectedSpecialties === 'string') {
          try {
            selectedSpecialties = JSON.parse(selectedSpecialties);
          } catch (e) {
            selectedSpecialties = selectedSpecialties.split(',').map(s => s.trim()).filter(s => s);
          }
        }
        
        if (!Array.isArray(selectedSpecialties)) {
          selectedSpecialties = [];
        }
        
        this.setData({
          formData: {
            real_name: teacher.real_name || '',
            id_card: this.maskIdCard(teacher.id_card || ''),
            id_card_original: teacher.id_card || '',
            phone: this.maskPhone(teacher.phone || ''),
            phone_original: teacher.phone || '',
            specialties: selectedSpecialties,
            intro: teacher.intro || ''
          }
        });
      }
    } catch (error) {
      console.error('加载老师信息失败:', error);
      showToast('加载失败，请重试');
    }
  },

  async loadSpecialties(selectedSpecialties = []) {
    try {
      const specialties = await getSpecialties();
      if (specialties && Array.isArray(specialties)) {
        let selected = selectedSpecialties;
        
        if (!Array.isArray(selected)) {
          if (typeof selected === 'string') {
            try {
              selected = JSON.parse(selected);
            } catch (e) {
              selected = selected.split(',').map(s => s.trim()).filter(s => s);
            }
          } else {
            selected = [];
          }
        }
        
        if (selected.length === 0) {
          selected = this.data.formData.specialties || [];
        }
        
        const options = specialties.map(item => ({
          label: item.name,
          value: item.name,
          checked: Array.isArray(selected) && selected.indexOf(item.name) > -1
        }));
        this.setData({ specialtyOptions: options });
      }
    } catch (error) {
      console.error('加载擅长领域失败:', error);
    }
  },

  maskIdCard(idCard) {
    if (!idCard || idCard.length < 18) return '';
    return idCard.substring(0, 4) + '**********' + idCard.substring(14);
  },

  maskPhone(phone) {
    if (!phone || phone.length < 11) return '';
    return phone.substring(0, 3) + '****' + phone.substring(7);
  },

  onInputChange(e) {
    const { field } = e.currentTarget.dataset;
    const value = e.detail.value;
    const updateKey = `formData.${field}`;
    
    this.setData({
      [updateKey]: value
    });
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
    
    if (!formData.id_card_original.trim()) {
      showToast('请填写身份证号');
      return false;
    }
    
    if (!formData.phone_original.trim()) {
      showToast('请填写手机号');
      return false;
    }
    
    const phoneReg = /^1[3-9]\d{9}$/;
    if (!phoneReg.test(formData.phone_original)) {
      showToast('请输入正确的手机号');
      return false;
    }
    
    if (formData.specialties.length === 0) {
      showToast('请至少选择一项擅长领域');
      return false;
    }
    
    return true;
  },

  async submitForm() {
    if (!this.validateForm()) {
      return;
    }

    if (this.data.isSubmitting) {
      return;
    }

    this.setData({ isSubmitting: true });
    wx.showLoading({ title: '保存中...', mask: true });

    try {
      const { formData } = this.data;
      const updateData = {
        real_name: formData.real_name,
        id_card: formData.id_card_original,
        phone: formData.phone_original,
        specialties: formData.specialties,
        intro: formData.intro
      };

      await updateTeacherInfo(updateData);

      wx.hideLoading();
      
      wx.showModal({
        title: '保存成功',
        content: '入驻信息已更新',
        showCancel: false,
        confirmText: '确定',
        success: () => {
          wx.navigateBack();
        }
      });
    } catch (error) {
      console.error('更新失败:', error);
      wx.hideLoading();
      this.setData({ isSubmitting: false });
      showToast('更新失败，请重试');
    }
  },

  preventMove() {
    return;
  }
});