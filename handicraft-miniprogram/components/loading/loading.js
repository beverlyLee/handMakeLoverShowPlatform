Component({
  properties: {
    type: {
      type: String,
      value: 'spinner'
    },
    size: {
      type: String,
      value: 'default'
    },
    color: {
      type: String,
      value: '#E67E22'
    },
    text: {
      type: String,
      value: ''
    },
    show: {
      type: Boolean,
      value: false
    },
    mask: {
      type: Boolean,
      value: true
    }
  },

  data: {
    sizeMap: {
      small: '40rpx',
      default: '64rpx',
      large: '88rpx'
    }
  },

  methods: {
    preventDefault() {}
  }
});
