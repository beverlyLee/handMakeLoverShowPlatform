const authApi = require('../../api/auth');
const storage = require('../../utils/storage');
const { showToast, showLoading, hideLoading } = require('../../utils/util');

Page({
  data: {
    phone: '',
    code: '',
    agreeAgreement: false,
    codeBtnText: '获取验证码',
    codeBtnDisabled: false,
    countdown: 60
  },

  onLoad(options) {
    const pages = getCurrentPages();
    const prevPage = pages[pages.length - 2];
  },

  onPhoneInput(e) {
    this.setData({
      phone: e.detail.value
    });
  },

  onCodeInput(e) {
    this.setData({
      code: e.detail.value
    });
  },

  toggleAgreement() {
    this.setData({
      agreeAgreement: !this.data.agreeAgreement
    });
  },

  getCode() {
    const { phone, codeBtnDisabled } = this.data;
    
    if (!phone) {
      showToast('请输入手机号');
      return;
    }

    if (!/^1[3-9]\d{9}$/.test(phone)) {
      showToast('请输入正确的手机号');
      return;
    }

    if (codeBtnDisabled) return;

    this.setData({
      codeBtnDisabled: true,
      codeBtnText: '60s后重新获取'
    });

    let countdown = 60;
    const timer = setInterval(() => {
      countdown--;
      if (countdown <= 0) {
        clearInterval(timer);
        this.setData({
          codeBtnDisabled: false,
          codeBtnText: '获取验证码'
        });
      } else {
        this.setData({
          codeBtnText: `${countdown}s后重新获取`
        });
      }
    }, 1000);

    showToast('验证码已发送');
  },

  async wechatLogin() {
    if (!this.data.agreeAgreement) {
      showToast('请先同意用户协议');
      return;
    }

    showLoading('登录中...');

    try {
      const loginRes = await new Promise((resolve, reject) => {
        wx.login({
          success: resolve,
          fail: reject
        });
      });

      if (!loginRes.code) {
        throw new Error('微信登录失败');
      }

      const result = await authApi.login({
        code: loginRes.code
      });

      hideLoading();

      if (result.needRegister) {
        showToast('请先完成注册');
        setTimeout(() => {
          wx.navigateTo({
            url: `/pages/register/index?needBindPhone=true&openid=${result.openid || ''}&sessionKey=${result.sessionKey || ''}`
          });
        }, 1500);
        return;
      }

      if (result.token) {
        storage.setToken(result.token);
      }
      if (result.user) {
        storage.setUserInfo(result.user);
        getApp().globalData.userInfo = result.user;
      }

      showToast('登录成功', 'success');

      setTimeout(() => {
        const pages = getCurrentPages();
        if (pages.length > 1) {
          wx.navigateBack();
        } else {
          wx.switchTab({
            url: '/pages/home/index'
          });
        }
      }, 1500);

    } catch (error) {
      hideLoading();
      console.error('微信登录失败:', error);
      showToast(error.msg || '登录失败，请重试');
    }
  },

  async phoneLogin() {
    const { phone, code, agreeAgreement } = this.data;

    if (!agreeAgreement) {
      showToast('请先同意用户协议');
      return;
    }

    if (!phone) {
      showToast('请输入手机号');
      return;
    }

    if (!/^1[3-9]\d{9}$/.test(phone)) {
      showToast('请输入正确的手机号');
      return;
    }

    if (!code) {
      showToast('请输入验证码');
      return;
    }

    showLoading('登录中...');

    try {
      const result = await authApi.login({
        phone,
        code,
        loginType: 'phone'
      });

      hideLoading();

      if (result.needRegister) {
        showToast('请先完成注册');
        setTimeout(() => {
          wx.navigateTo({
            url: `/pages/register/index?needBindPhone=false`
          });
        }, 1500);
        return;
      }

      if (result.token) {
        storage.setToken(result.token);
      }
      if (result.user) {
        storage.setUserInfo(result.user);
        getApp().globalData.userInfo = result.user;
      }

      showToast('登录成功', 'success');

      setTimeout(() => {
        const pages = getCurrentPages();
        if (pages.length > 1) {
          wx.navigateBack();
        } else {
          wx.switchTab({
            url: '/pages/home/index'
          });
        }
      }, 1500);

    } catch (error) {
      hideLoading();
      console.error('手机号登录失败:', error);
      showToast(error.msg || '登录失败，请重试');
    }
  },

  goToRegister() {
    wx.navigateTo({
      url: '/pages/register/index'
    });
  }
});
