Page({
  data: {
    welcomeText: '欢迎来到手工爱好者平台'
  },

  onLoad() {
    console.log('首页加载完成')
  },

  onReady() {
    console.log('首页渲染完成')
  },

  onShow() {
    console.log('首页显示')
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setSelected(0)
    }
  },

  onHide() {
    console.log('首页隐藏')
  },

  onUnload() {
    console.log('首页卸载')
  }
})
