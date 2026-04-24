Component({
  properties: {
    show: {
      type: Boolean,
      value: false
    },
    text: {
      type: String,
      value: '加载中...'
    },
    mask: {
      type: Boolean,
      value: true
    }
  },

  data: {},

  methods: {
    onMaskTap() {
      this.triggerEvent('masktap');
    }
  }
});
