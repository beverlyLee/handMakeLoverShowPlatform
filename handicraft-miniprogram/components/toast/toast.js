Component({
  properties: {
    show: {
      type: Boolean,
      value: false
    },
    type: {
      type: String,
      value: 'text'
    },
    title: {
      type: String,
      value: ''
    },
    message: {
      type: String,
      value: ''
    },
    duration: {
      type: Number,
      value: 2000
    },
    icon: {
      type: String,
      value: ''
    }
  },

  data: {
    isVisible: false,
    iconMap: {
      success: '✓',
      fail: '✕',
      warning: '!',
      loading: '◯'
    }
  },

  observers: {
    'show': function(show) {
      if (show) {
        this.setData({ isVisible: true });
        if (this.properties.type !== 'loading') {
          this.startTimer();
        }
      } else {
        this.hide();
      }
    }
  },

  lifetimes: {
    detached() {
      this.clearTimer();
    }
  },

  methods: {
    startTimer() {
      this.clearTimer();
      const duration = this.properties.duration;
      if (duration > 0) {
        this.timer = setTimeout(() => {
          this.hide();
        }, duration);
      }
    },

    clearTimer() {
      if (this.timer) {
        clearTimeout(this.timer);
        this.timer = null;
      }
    },

    hide() {
      this.setData({ isVisible: false });
      this.clearTimer();
      this.triggerEvent('close');
    },

    preventDefault() {}
  }
});
