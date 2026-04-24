Component({
  properties: {
    value: {
      type: Number,
      value: 0
    },
    max: {
      type: Number,
      value: 5
    },
    size: {
      type: String,
      value: '36rpx'
    },
    editable: {
      type: Boolean,
      value: false
    },
    showText: {
      type: Boolean,
      value: false
    },
    color: {
      type: String,
      value: '#E67E22'
    },
    inactiveColor: {
      type: String,
      value: '#D2B48C'
    }
  },

  data: {
    stars: []
  },

  observers: {
    'value, max': function(value, max) {
      this.initStars();
    }
  },

  lifetimes: {
    attached() {
      this.initStars();
    }
  },

  methods: {
    initStars() {
      const { value, max } = this.properties;
      const stars = [];
      
      for (let i = 1; i <= max; i++) {
        if (i <= Math.floor(value)) {
          stars.push({ type: 'full' });
        } else if (i - value < 1 && i - value > 0) {
          stars.push({ type: 'half' });
        } else {
          stars.push({ type: 'empty' });
        }
      }
      
      this.setData({ stars });
    },

    getRatingText(value) {
      const texts = {
        1: '很差',
        2: '一般',
        3: '还行',
        4: '推荐',
        5: '超赞'
      };
      return texts[Math.round(value)] || '';
    },

    onStarTap(e) {
      if (!this.properties.editable) return;
      
      const index = e.currentTarget.dataset.index;
      const value = index + 1;
      
      this.setData({ value });
      this.triggerEvent('change', { value });
    }
  }
});
