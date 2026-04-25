const { getConversations } = require('../../api/messages');
const { showToast } = require('../../utils/util');

Page({
  data: {
    unreadCounts: {
      system: 0,
      order: 0,
      activity: 0
    },
    lastMessages: {
      system: '',
      order: '',
      activity: ''
    },
    chatList: []
  },

  onLoad() {
    this.loadData();
  },

  onShow() {
    this.loadData();
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setSelected(3)
    }
  },

  async loadData() {
    try {
      const [conversations] = await Promise.all([
        getConversations()
      ]);

      const chatList = conversations?.list || conversations || [];
      
      const mockSystemCount = 2;
      const mockOrderCount = 1;
      const mockActivityCount = 0;

      this.setData({
        unreadCounts: {
          system: mockSystemCount,
          order: mockOrderCount,
          activity: mockActivityCount
        },
        lastMessages: {
          system: '您的订单ORD202404150006已发货',
          order: '您购买的"手工编织羊毛围巾"已确认收货',
          activity: ''
        },
        chatList: chatList.length > 0 ? chatList : [
          {
            id: 1,
            name: '手作大师',
            avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=craft%20master%20avatar&image_size=square',
            last_message: '您好，您的订单已经发出了~',
            last_message_time: '10:30',
            unread_count: 1
          },
          {
            id: 2,
            name: '编织女王',
            avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=knitting%20crafts%20teacher%20avatar&image_size=square',
            last_message: '好的，教程视频已经发送给您了',
            last_message_time: '昨天',
            unread_count: 0
          }
        ]
      });
    } catch (error) {
      console.error('加载消息数据失败:', error);
    }
  },

  goToNotification(e) {
    const type = e.currentTarget.dataset.type;
    wx.navigateTo({
      url: `/pages/notification-list/index?type=${type}`
    });
  },

  goToChat(e) {
    const chatId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/chat/index?id=${chatId}`
    });
  }
});
