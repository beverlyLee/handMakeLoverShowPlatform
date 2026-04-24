Component({
  properties: {
    safeArea: {
      type: Boolean,
      value: true
    },
    bgColor: {
      type: String,
      value: '#FFFFFF'
    },
    showShadow: {
      type: Boolean,
      value: true
    }
  },

  data: {
    safeAreaBottom: 0
  },

  lifetimes: {
    attached() {
      this.initSafeArea();
    }
  },

  methods: {
    initSafeArea() {
      if (!this.properties.safeArea) return;
      
      const systemInfo = wx.getSystemInfoSync();
      const safeAreaBottom = systemInfo.safeArea
        ? systemInfo.screenHeight - systemInfo.safeArea.bottom
        : 0;
      
      this.setData({
        safeAreaBottom: safeAreaBottom || 0
      });
    },

    onLeftTap() {
      this.triggerEvent('lefttap');
    },

    onCenterTap() {
      this.triggerEvent('centertap');
    },

    onRightTap() {
      this.triggerEvent('righttap');
    },

    onButtonTap(e) {
      const index = e.currentTarget.dataset.index;
      this.triggerEvent('buttontap', { index });
    }
  }
});
