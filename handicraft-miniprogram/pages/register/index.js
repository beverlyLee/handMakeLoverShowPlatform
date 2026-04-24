const authApi = require('../../api/auth');
const storage = require('../../utils/storage');
const { showToast, showLoading, hideLoading } = require('../../utils/util');

Page({
  data: {
    phone: '',
    code: '',
    nickname: '',
    avatar: '',
    agreeAgreement: false,
    codeBtnText: '获取验证码',
    codeBtnDisabled: false,
    countdown: 60,
    needBindPhone: false,
    openid: '',
    sessionKey: ''
  },

  onLoad(options) {
    const pages = getCurrentPages();
    const prevPage = pages[pages.length - 2];
    const needBindPhone = options.needBindPhone === 'true';
    const openid = options.openid || '';
    const sessionKey = options.sessionKey || '';
    const wxNickname = options.nickname || '';
    const wxAvatar = options.avatar || '';

    this.setData({
      needBindPhone,
      openid,
      sessionKey,
      nickname: wxNickname,
      avatar: wxAvatar
    });

    if (needBindPhone) {
      this.chooseAvatar = this.chooseAvatar.bind(this);
      this.onNicknameInput = this.onNicknameInput.bind(this);
    }
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

  onNicknameInput(e) {
    this.setData({
      nickname: e.detail.value
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

  chooseAvatar(e) {
    const { avatarUrl } = e.detail;
    this.setData({
      avatar: avatarUrl
    });
  },

  onNicknameBlur(e) {
    this.setData({
      nickname: e.detail.value
    });
  },

  async doRegister() {
    const { phone, code, nickname, avatar, agreeAgreement, needBindPhone, openid } = this.data;

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

    if (needBindPhone && !nickname) {
      showToast('请输入昵称');
      return;
    }

    showLoading('注册中...');

    try {
      const registerData = {
        phone,
        code,
        nickname: nickname || `用户${phone.slice(-4)}`,
        avatar: avatar || ''
      };

      if (needBindPhone && openid) {
        registerData.openid = openid;
      }

      const result = await authApi.register(registerData);
      
      hideLoading();

      if (result.token) {
        storage.setToken(result.token);
      }
      if (result.user) {
        storage.setUserInfo(result.user);
        getApp().globalData.userInfo = result.user;
      }

      showToast('注册成功', 'success');

      setTimeout(() => {
        if (needBindPhone) {
          wx.switchTab({
            url: '/pages/user-center/index'
          });
        } else {
          wx.navigateBack();
        }
      }, 1500);

    } catch (error) {
      hideLoading();
      console.error('注册失败:', error);
      showToast(error.msg || '注册失败，请重试');
    }
  },

  goToLogin() {
    wx.navigateTo({
      url: '/pages/login/index'
    });
  }
});
