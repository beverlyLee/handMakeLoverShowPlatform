Component({
  properties: {
    show: {
      type: Boolean,
      value: false
    },
    title: {
      type: String,
      value: ''
    },
    actions: {
      type: Array,
      value: []
    },
    showCancel: {
      type: Boolean,
      value: true
    },
    cancelText: {
      type: String,
      value: '取消'
    },
    maskClosable: {
      type: Boolean,
      value: true
    }
  },

  data: {
    isVisible: false,
    showAnimation: false
  },

  observers: {
    'show': function(show) {
      if (show) {
        this.setData({ 
          isVisible: true 
        }, () => {
          setTimeout(() => {
            this.setData({ showAnimation: true });
          }, 50);
        });
      } else {
        this.setData({ showAnimation: false });
        setTimeout(() => {
          this.setData({ isVisible: false });
        }, 300);
      }
    }
  },

  methods: {
    onMaskTap() {
      if (this.properties.maskClosable) {
        this.close();
      }
    },

    onActionTap(e) {
      const index = e.currentTarget.dataset.index;
      const actions = this.properties.actions;
      const action = actions[index];
      
      if (action.disabled) return;
      
      this.triggerEvent('actiontap', { index, action });
      this.close();
    },

    onCancelTap() {
      this.triggerEvent('cancel');
      this.close();
    },

    close() {
      this.setData({ showAnimation: false });
      setTimeout(() => {
        this.setData({ isVisible: false });
        this.triggerEvent('close');
      }, 300);
    },

    preventDefault() {}
  }
});
