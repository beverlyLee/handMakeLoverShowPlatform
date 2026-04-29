Component({
  properties: {
    value: {
      type: Number,
      value: 0,
      observer: 'updateStars'
    },
    max: {
      type: Number,
      value: 5
    },
    disabled: {
      type: Boolean,
      value: false
    },
    size: {
      type: String,
      value: 'default'
    },
    showValue: {
      type: Boolean,
      value: true
    }
  },

  data: {
    stars: [],
    displayValue: 0
  },

  lifetimes: {
    attached() {
      this.updateStars(this.properties.value);
    }
  },

  methods: {
    updateStars(value) {
      const { max } = this.properties;
      const stars = [];
      
      for (let i = 0; i < max; i++) {
        const starValue = i + 1;
        let type = 'empty';
        
        if (value >= starValue) {
          type = 'full';
        } else if (value >= starValue - 0.5) {
          type = 'half';
        }
        
        stars.push({
          index: i,
          value: starValue,
          type: type
        });
      }
      
      this.setData({
        stars: stars,
        displayValue: Number(value.toFixed(1))
      });
    },

    onStarTap(e) {
      if (this.properties.disabled) return;
      
      const { index } = e.currentTarget.dataset;
      const clientX = e.changedTouches ? e.changedTouches[0].clientX : 0;
      
      const query = wx.createSelectorQuery().in(this);
      query.select('.star-item-' + index).boundingClientRect();
      
      query.exec((res) => {
        if (!res[0]) return;
        
        const starRect = res[0];
        const relativeX = clientX - starRect.left;
        const midPoint = starRect.width / 2;
        
        let newValue;
        if (relativeX < midPoint) {
          newValue = index + 0.5;
        } else {
          newValue = index + 1;
        }
        
        this.triggerEvent('change', {
          value: newValue,
          oldValue: this.properties.value
        });
        
        this.setData({
          value: newValue
        });
        
        this.updateStars(newValue);
      });
    }
  }
});
