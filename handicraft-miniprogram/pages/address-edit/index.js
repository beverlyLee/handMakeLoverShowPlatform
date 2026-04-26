const { createAddress, updateAddress, getAddressDetail } = require('../../api/users');
const { showToast, showLoading, hideLoading, isEmpty } = require('../../utils/util');
const storage = require('../../utils/storage');

Page({
  data: {
    addressId: null,
    isEdit: false,
    
    name: '',
    phone: '',
    province: '',
    city: '',
    district: '',
    detail: '',
    is_default: false,
    
    regionText: '',
    region: [],
    
    isSubmitting: false,
    isLoading: false
  },

  onLoad(options) {
    console.log('地址编辑页面加载');
    this.initTestToken();
    
    if (options.id) {
      const addressId = parseInt(options.id);
      this.setData({
        addressId: addressId,
        isEdit: true
      });
      
      this.loadAddressDetail(addressId);
    }
    
    if (options.data) {
      try {
        const addressData = JSON.parse(decodeURIComponent(options.data));
        this.fillAddressData(addressData);
      } catch (e) {
        console.error('解析地址数据失败:', e);
      }
    }
  },

  initTestToken() {
    const currentToken = storage.getToken();
    if (!currentToken) {
      storage.setToken('test_token');
      console.log('已设置测试 Token');
    }
  },

  async loadAddressDetail(addressId) {
    if (this.data.isLoading) return;
    
    this.setData({ isLoading: true });
    showLoading('加载中...');
    
    try {
      const result = await getAddressDetail(addressId);
      console.log('获取地址详情成功:', result);
      
      if (result) {
        this.fillAddressData(result);
      } else {
        showToast('地址不存在');
      }
    } catch (error) {
      console.error('获取地址详情失败:', error);
      showToast('加载失败，请重试');
    } finally {
      this.setData({ isLoading: false });
      hideLoading();
    }
  },

  fillAddressData(address) {
    const { name, phone, province, city, district, detail, is_default } = address;
    
    let regionText = '';
    let region = [];
    
    if (province && city && district) {
      regionText = `${province} ${city} ${district}`;
      region = [province, city, district];
    }
    
    this.setData({
      name: name || '',
      phone: phone || '',
      province: province || '',
      city: city || '',
      district: district || '',
      detail: detail || '',
      is_default: is_default || false,
      regionText: regionText,
      region: region
    });
  },

  onInputName(e) {
    this.setData({
      name: e.detail.value
    });
  },

  onInputPhone(e) {
    this.setData({
      phone: e.detail.value
    });
  },

  onInputDetail(e) {
    this.setData({
      detail: e.detail.value
    });
  },

  onRegionChange(e) {
    const value = e.detail.value;
    if (value && value.length === 3) {
      this.setData({
        province: value[0],
        city: value[1],
        district: value[2],
        regionText: `${value[0]} ${value[1]} ${value[2]}`,
        region: value
      });
    }
  },

  onDefaultChange(e) {
    this.setData({
      is_default: e.detail.value
    });
  },

  chooseWxAddress() {
    wx.chooseAddress({
      success: (res) => {
        console.log('选择微信地址成功:', res);
        
        const { userName, telNumber, provinceName, cityName, countyName, detailInfo } = res;
        
        this.setData({
          name: userName,
          phone: telNumber,
          province: provinceName,
          city: cityName,
          district: countyName,
          detail: detailInfo,
          regionText: `${provinceName} ${cityName} ${countyName}`,
          region: [provinceName, cityName, countyName]
        });
      },
      fail: (err) => {
        console.log('选择微信地址失败:', err);
        if (err.errMsg.includes('cancel')) {
          return;
        }
        showToast('获取微信地址失败，请手动输入');
      }
    });
  },

  validateForm() {
    const { name, phone, province, city, district, detail } = this.data;
    
    if (isEmpty(name)) {
      showToast('请输入收货人姓名');
      return false;
    }
    
    if (isEmpty(phone)) {
      showToast('请输入手机号码');
      return false;
    }
    
    const phoneReg = /^1[3-9]\d{9}$/;
    if (!phoneReg.test(phone)) {
      showToast('请输入正确的手机号码');
      return false;
    }
    
    if (isEmpty(province) || isEmpty(city) || isEmpty(district)) {
      showToast('请选择所在地区');
      return false;
    }
    
    if (isEmpty(detail)) {
      showToast('请输入详细地址');
      return false;
    }
    
    return true;
  },

  async submitAddress() {
    if (this.data.isSubmitting) return;
    
    if (!this.validateForm()) return;
    
    this.setData({ isSubmitting: true });
    showLoading('保存中...');
    
    try {
      const addressData = {
        name: this.data.name,
        phone: this.data.phone,
        province: this.data.province,
        city: this.data.city,
        district: this.data.district,
        detail: this.data.detail,
        is_default: this.data.is_default
      };
      
      let result;
      if (this.data.isEdit && this.data.addressId) {
        result = await updateAddress(this.data.addressId, addressData);
      } else {
        result = await createAddress(addressData);
      }
      
      console.log('保存地址成功:', result);
      
      hideLoading();
      showToast('保存成功', 'success');
      
      setTimeout(() => {
        wx.navigateBack();
      }, 1000);
    } catch (error) {
      console.error('保存地址失败:', error);
      hideLoading();
      this.setData({ isSubmitting: false });
      showToast('保存失败，请重试');
    }
  }
});
