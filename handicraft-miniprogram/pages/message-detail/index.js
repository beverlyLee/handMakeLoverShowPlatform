const { getMessageDetail, markAsRead, deleteMessage } = require('../../api/messages');
const { showToast, safeParseDate } = require('../../utils/util');

const MESSAGE_TYPES = {
  system: {
    key: 'system',
    name: '系统通知',
    icon: '📢',
    bgColor: 'linear-gradient(135deg, #795548 0%, #8D6E63 100%)'
  },
  order: {
    key: 'order',
    name: '订单消息',
    icon: '📦',
    bgColor: 'linear-gradient(135deg, #FF9800 0%, #F57C00 100%)'
  },
  activity: {
    key: 'activity',
    name: '活动消息',
    icon: '🎉',
    bgColor: 'linear-gradient(135deg, #4CAF50 0%, #388E3C 100%)'
  }
};

Page({
  data: {
    messageId: null,
    messageDetail: null,
    typeConfig: null,
    isLoading: true,
    isRead: false,
    showDeleteDialog: false
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ messageId: parseInt(options.id) });
      this.loadMessageDetail();
    } else {
      showToast('消息ID缺失');
      wx.navigateBack();
    }
  },

  onPullDownRefresh() {
    this.loadMessageDetail().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  async loadMessageDetail() {
    const { messageId } = this.data;
    this.setData({ isLoading: true });

    try {
      const result = await getMessageDetail(messageId);
      const message = result || {};
      
      const typeConfig = MESSAGE_TYPES[message.type] || MESSAGE_TYPES.system;
      
      this.setData({
        messageDetail: message,
        typeConfig: typeConfig,
        isRead: message.is_read || false,
        isLoading: false
      });

      if (!message.is_read) {
        this.markMessageAsRead();
      }

      wx.setNavigationBarTitle({
        title: typeConfig.name
      });
    } catch (error) {
      console.error('加载消息详情失败:', error);
      this.setData({ isLoading: false });
      this.loadMockData();
    }
  },

  loadMockData() {
    const mockData = {
      id: this.data.messageId || 1,
      type: this.data.messageId % 2 === 0 ? 'order' : 'system',
      title: this.data.messageId % 2 === 0 ? '订单发货通知' : '欢迎加入手工爱好者平台',
      content: this.data.messageId % 2 === 0 
        ? '您好！您的订单 ORD202404250001 已发货。\n\n📦 订单信息：\n• 商品：手工编织羊毛围巾 x1\n• 快递公司：顺丰速运\n• 快递单号：SF1234567890\n\n预计3-5个工作日送达，请注意查收。\n\n如有问题，请联系客服。'
        : '亲爱的手作爱好者：\n\n🎉 欢迎加入手工爱好者平台！\n\n在这里，您可以：\n• 浏览精选手工作品\n• 与手作达人交流学习\n• 购买优质手工材料\n• 分享您的创作故事\n\n我们致力于为手工爱好者打造一个温馨、专业的交流社区。\n\n✨ 新用户专享福利：\n首次下单立享9折优惠，优惠码：NEWCRAFT\n\n如有任何问题，欢迎随时联系客服。\n\n祝您创作愉快！\n\n—— 手工爱好者平台团队',
      sender: this.data.messageId % 2 === 0 ? '订单中心' : '系统管理员',
      sender_avatar: '',
      create_time: '2024-04-28 10:30:00',
      is_read: false
    };

    const typeConfig = MESSAGE_TYPES[mockData.type] || MESSAGE_TYPES.system;

    this.setData({
      messageDetail: mockData,
      typeConfig: typeConfig,
      isRead: mockData.is_read,
      isLoading: false
    });

    wx.setNavigationBarTitle({
      title: typeConfig.name
    });
  },

  async markMessageAsRead() {
    const { messageId } = this.data;
    try {
      await markAsRead(messageId);
      this.setData({ isRead: true });
    } catch (error) {
      console.error('标记已读失败:', error);
    }
  },

  showDeleteConfirm() {
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条消息吗？删除后无法恢复。',
      confirmColor: '#DC3545',
      success: (res) => {
        if (res.confirm) {
          this.handleDelete();
        }
      }
    });
  },

  async handleDelete() {
    const { messageId } = this.data;
    wx.showLoading({ title: '删除中...', mask: true });

    try {
      await deleteMessage(messageId);
      wx.hideLoading();
      showToast('删除成功', 'success');
      
      setTimeout(() => {
        wx.navigateBack({
          delta: 1
        });
      }, 1500);
    } catch (error) {
      wx.hideLoading();
      console.error('删除失败:', error);
      showToast('删除失败，请重试');
    }
  },

  formatTime(timeStr) {
    if (!timeStr) return '';
    
    const date = safeParseDate(timeStr);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const hour = date.getHours().toString().padStart(2, '0');
    const minute = date.getMinutes().toString().padStart(2, '0');
    
    return `${year}年${month}月${day}日 ${hour}:${minute}`;
  },

  onShareAppMessage() {
    const { messageDetail, typeConfig } = this.data;
    return {
      title: `${typeConfig?.name || '消息'}: ${messageDetail?.title || ''}`,
      path: `/pages/message-detail/index?id=${this.data.messageId}`
    };
  }
});
