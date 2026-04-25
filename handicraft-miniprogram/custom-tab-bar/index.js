Component({
  data: {
    selected: 0,
    list: [
      {
        pagePath: '/pages/home/index',
        text: '首页',
        icon: '🏠'
      },
      {
        pagePath: '/pages/products/index',
        text: '作品',
        icon: '🎨'
      },
      {
        pagePath: '/pages/orders/index',
        text: '订单',
        icon: '📦',
        badge: 0
      },
      {
        pagePath: '/pages/messages/index',
        text: '消息',
        icon: '💬',
        badge: 0
      },
      {
        pagePath: '/pages/user-center/index',
        text: '我的',
        icon: '👤'
      }
    ]
  },

  methods: {
    switchTab(e) {
      const data = e.currentTarget.dataset;
      const url = data.path;
      
      wx.switchTab({ url });
    },

    setSelected(index) {
      this.setData({
        selected: index
      });
    },

    setBadge(tabIndex, count) {
      const list = this.data.list;
      if (list[tabIndex]) {
        list[tabIndex].badge = count || 0;
        this.setData({ list });
      }
    }
  }
});
