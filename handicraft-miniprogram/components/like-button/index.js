const { toggleLike } = require('../../api/favorites');
const { showToast } = require('../../utils/util');
const { getToken } = require('../../utils/storage');

Component({
  properties: {
    productId: {
      type: Number,
      value: 0
    },
    isLiked: {
      type: Boolean,
      value: false,
      observer: 'updateStatus'
    },
    likeCount: {
      type: Number,
      value: 0,
      observer: 'updateStatus'
    },
    popularityScore: {
      type: Number,
      value: 0,
      observer: 'updateStatus'
    },
    size: {
      type: String,
      value: 'default'
    },
    showCount: {
      type: Boolean,
      value: true
    },
    disabled: {
      type: Boolean,
      value: false
    }
  },

  data: {
    _isLiked: false,
    _likeCount: 0,
    _popularityScore: 0,
    isAnimating: false
  },

  lifetimes: {
    attached() {
      this.updateStatus();
    }
  },

  methods: {
    updateStatus() {
      this.setData({
        _isLiked: this.properties.isLiked,
        _likeCount: this.properties.likeCount,
        _popularityScore: this.properties.popularityScore
      });
    },

    async onTap() {
      if (this.properties.disabled || this.data.isAnimating) return;
      
      const { productId } = this.properties;
      if (!productId) {
        showToast('产品ID不能为空');
        return;
      }

      const token = getToken();
      if (!token) {
        showToast('请先登录后再点赞');
        return;
      }

      this.setData({ isAnimating: true });

      try {
        const result = await toggleLike({ product_id: productId });
        
        if (result) {
          const is_liked = result.is_liked;
          const like_count = result.like_count;
          const popularity_score = result.popularity_score || result.heat_score;
          
          this.setData({
            _isLiked: is_liked,
            _likeCount: like_count,
            _popularityScore: popularity_score,
            isAnimating: false
          });
          
          this.triggerEvent('change', {
            productId: productId,
            isLiked: is_liked,
            likeCount: like_count,
            popularityScore: popularity_score
          });

          this.triggerEvent(is_liked ? 'like' : 'unlike', {
            productId: productId,
            likeCount: like_count,
            popularityScore: popularity_score
          });
        }
      } catch (error) {
        console.error('点赞失败:', error);
        this.setData({ isAnimating: false });
        
        if (error && error.code === 2002) {
          showToast('请先登录后再点赞');
        } else {
          showToast(error.msg || '操作失败，请重试');
        }
      }
    }
  }
});