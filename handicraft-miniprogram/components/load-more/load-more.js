Component({
  properties: {
    status: {
      type: String,
      value: 'loading'
    },
    loadingText: {
      type: String,
      value: '加载中...'
    },
    noMoreText: {
      type: String,
      value: '没有更多了'
    },
    loadMoreText: {
      type: String,
      value: '加载更多'
    }
  },

  data: {},

  methods: {
    onLoadMore() {
      if (this.properties.status === 'more') {
        this.triggerEvent('loadmore');
      }
    }
  }
});
