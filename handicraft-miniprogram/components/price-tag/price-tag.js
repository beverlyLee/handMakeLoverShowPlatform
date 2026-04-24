Component({
  properties: {
    price: {
      type: Number,
      value: 0
    },
    originalPrice: {
      type: Number,
      value: null
    },
    prefix: {
      type: String,
      value: '¥'
    },
    decimalDigits: {
      type: Number,
      value: 2
    },
    size: {
      type: String,
      value: 'default'
    },
    showSales: {
      type: Boolean,
      value: false
    },
    salesCount: {
      type: Number,
      value: 0
    },
    showDiscount: {
      type: Boolean,
      value: false
    },
    showTag: {
      type: Boolean,
      value: false
    },
    tagText: {
      type: String,
      value: ''
    },
    tagType: {
      type: String,
      value: 'default'
    }
  },

  data: {
    sizeMap: {
      small: {
        price: '32rpx',
        original: '22rpx',
        sales: '20rpx'
      },
      default: {
        price: '44rpx',
        original: '26rpx',
        sales: '22rpx'
      },
      large: {
        price: '56rpx',
        original: '30rpx',
        sales: '24rpx'
      }
    },
    tagColorMap: {
      default: {
        bg: 'rgba(230, 126, 34, 0.1)',
        color: '#E67E22'
      },
      hot: {
        bg: 'rgba(231, 76, 60, 0.1)',
        color: '#E74C3C'
      },
      new: {
        bg: 'rgba(46, 204, 113, 0.1)',
        color: '#2ECC71'
      },
      limited: {
        bg: 'rgba(155, 89, 182, 0.1)',
        color: '#9B59B6'
      }
    }
  },

  methods: {
    formatPrice(price, digits) {
      if (price === null || price === undefined) return '';
      return Number(price).toFixed(digits);
    },

    getDiscount() {
      const { price, originalPrice } = this.properties;
      if (!originalPrice || originalPrice <= 0) return 0;
      return Math.round((price / originalPrice) * 10);
    }
  }
});
