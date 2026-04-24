const app = getApp();

Component({
  properties: {
    title: {
      type: String,
      value: ''
    },
    showBack: {
      type: Boolean,
      value: true
    },
    showHome: {
      type: Boolean,
      value: false
    },
    backText: {
      type: String,
      value: ''
    },
    bgColor: {
      type: String,
      value: '#795548'
    },
    titleColor: {
      type: String,
      value: '#FFFFFF'
    },
    iconColor: {
      type: String,
      value: '#FFFFFF'
    },
    fixed: {
      type: Boolean,
      value: false
    },
    placeholder: {
      type: Boolean,
      value: true
    }
  },

  data: {
    statusBarHeight: 0,
    navBarHeight: 0,
    menuInfo: null,
    leftWidth: 0
  },

  lifetimes: {
    attached() {
      this.initNavBar();
    }
  },

  methods: {
    initNavBar() {
      const systemInfo = wx.getSystemInfoSync();
      const menuInfo = wx.getMenuButtonBoundingClientRect();
      
      const statusBarHeight = systemInfo.statusBarHeight || 20;
      const navBarHeight = (menuInfo.top - statusBarHeight) * 2 + menuInfo.height;
      
      const leftWidth = menuInfo.left;
      
      this.setData({
        statusBarHeight,
        navBarHeight,
        menuInfo,
        leftWidth
      });
      
      this.triggerEvent('inited', {
        statusBarHeight,
        navBarHeight,
        totalHeight: statusBarHeight + navBarHeight
      });
    },

    onBackTap() {
      const pages = getCurrentPages();
      if (pages.length > 1) {
        wx.navigateBack();
      }
      this.triggerEvent('back');
    },

    onHomeTap() {
      wx.switchTab({
        url: '/pages/home/index'
      });
      this.triggerEvent('home');
    },

    onTitleTap() {
      this.triggerEvent('titletap');
    },

    onRightTap() {
      this.triggerEvent('righttap');
    }
  }
});
