const { getAddressList, deleteAddress, setDefaultAddress } = require('../../api/users');
const { showToast, showLoading, hideLoading } = require('../../utils/util');
const storage = require('../../utils/storage');

Page({
  data: {
    addressList: [],
    isLoading: false,
    isSelectMode: false,
    selectedAddressId: null
  },

  onLoad(options) {
    console.log('地址列表页面加载');
    this.initTestToken();
    
    if (options.select === '1') {
      this.setData({
        isSelectMode: true,
        selectedAddressId: options.selectedId ? parseInt(options.selectedId) : null
      });
    }
  },

  initTestToken() {
    const currentToken = storage.getToken();
    if (!currentToken) {
      storage.setToken('test_token');
      console.log('已设置测试 Token');
    }
  },

  onShow() {
    console.log('地址列表页面显示');
    this.loadAddressList();
  },

  onPullDownRefresh() {
    this.loadAddressList().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  async loadAddressList() {
    if (this.data.isLoading) return;

    this.setData({ isLoading: true });
    showLoading('加载中...');

    try {
      const result = await getAddressList();
      console.log('获取地址列表成功:', result);

      const addressList = result?.addresses || result?.list || [];
      
      const formattedList = addressList.map(item => ({
        ...item,
        fullAddress: `${item.province || ''}${item.city || ''}${item.district || ''}${item.detail || ''}`
      }));

      this.setData({
        addressList: formattedList,
        isLoading: false
      });
    } catch (error) {
      console.error('获取地址列表失败:', error);
      this.setData({ isLoading: false });
      showToast('加载失败，请重试');
    } finally {
      hideLoading();
    }
  },

  goToAddAddress() {
    wx.navigateTo({
      url: '/pages/address-edit/index'
    });
  },

  goToEditAddress(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({
      url: `/pages/address-edit/index?id=${id}`
    });
  },

  selectAddress(e) {
    if (!this.data.isSelectMode) return;
    
    const { id } = e.currentTarget.dataset;
    const pages = getCurrentPages();
    const prevPage = pages[pages.length - 2];
    
    if (prevPage) {
      const selectedAddress = this.data.addressList.find(item => item.id === id);
      prevPage.setData({
        selectedAddress: selectedAddress
      });
    }
    
    wx.navigateBack();
  },

  async setAsDefault(e) {
    const { id } = e.currentTarget.dataset;
    const address = this.data.addressList.find(item => item.id === id);
    
    if (address?.is_default) return;

    showLoading('设置中...');

    try {
      await setDefaultAddress(id);
      showToast('设置成功', 'success');
      
      const updatedList = this.data.addressList.map(item => ({
        ...item,
        is_default: item.id === id
      }));
      
      this.setData({
        addressList: updatedList
      });
    } catch (error) {
      console.error('设置默认地址失败:', error);
      showToast('设置失败，请重试');
    } finally {
      hideLoading();
    }
  },

  confirmDelete(e) {
    const { id } = e.currentTarget.dataset;
    
    wx.showModal({
      title: '提示',
      content: '确定要删除这个地址吗？',
      success: async (res) => {
        if (res.confirm) {
          this.deleteAddress(id);
        }
      }
    });
  },

  async deleteAddress(id) {
    showLoading('删除中...');

    try {
      await deleteAddress(id);
      showToast('删除成功', 'success');
      
      const updatedList = this.data.addressList.filter(item => item.id !== id);
      this.setData({
        addressList: updatedList
      });
    } catch (error) {
      console.error('删除地址失败:', error);
      showToast('删除失败，请重试');
    } finally {
      hideLoading();
    }
  }
});
