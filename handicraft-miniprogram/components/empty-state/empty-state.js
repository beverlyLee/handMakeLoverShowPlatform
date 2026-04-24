Component({
  properties: {
    type: {
      type: String,
      value: 'default'
    },
    title: {
      type: String,
      value: '暂无数据'
    },
    description: {
      type: String,
      value: ''
    },
    showButton: {
      type: Boolean,
      value: false
    },
    buttonText: {
      type: String,
      value: '去逛逛'
    },
    icon: {
      type: String,
      value: ''
    }
  },

  data: {
    iconMap: {
      default: '📭',
      order: '📦',
      product: '🎨',
      favorite: '💝',
      address: '📍',
      message: '💬',
      search: '🔍',
      cart: '🛒'
    }
  },

  methods: {
    onButtonTap() {
      this.triggerEvent('buttontap');
    }
  }
});
