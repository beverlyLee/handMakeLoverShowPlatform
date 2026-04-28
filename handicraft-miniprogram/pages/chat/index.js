const { getConversationMessages, sendMessage, markAsRead } = require('../../api/messages');
const { showToast, safeParseDate } = require('../../utils/util');
const storage = require('../../utils/storage');

Page({
  data: {
    conversationId: null,
    targetUser: {
      id: null,
      name: '',
      avatar: ''
    },
    messageList: [],
    inputValue: '',
    isLoading: true,
    hasMore: true,
    page: 1,
    pageSize: 20,
    isSending: false,
    showCancelDialog: false,
    scrollToBottom: true,
    currentUserId: null
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ 
        conversationId: parseInt(options.id)
      });
      this.initUserInfo();
      this.loadMessages();
    } else {
      showToast('会话ID缺失');
      wx.navigateBack();
    }
  },

  onShow() {
    this.setData({ scrollToBottom: true });
  },

  onPullDownRefresh() {
    this.loadMoreHistory().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  initUserInfo() {
    const userInfo = storage.getUserInfo();
    if (userInfo && userInfo.id) {
      this.setData({ currentUserId: userInfo.id });
    }
  },

  async loadMessages() {
    const { conversationId, page, pageSize } = this.data;
    this.setData({ isLoading: true });

    try {
      const result = await getConversationMessages(conversationId, { page, size: pageSize });
      const messages = result?.list || result || [];
      
      const processedMessages = this.processMessages(messages);
      
      const mockMessages = this.getMockMessages();
      const allMessages = [...processedMessages, ...mockMessages].sort((a, b) => {
        return safeParseDate(a.createTime).getTime() - safeParseDate(b.createTime).getTime();
      });

      this.setData({
        messageList: allMessages,
        isLoading: false,
        hasMore: messages.length >= pageSize,
        scrollToBottom: true
      });

      this.updateNavigationBar();
    } catch (error) {
      console.log('加载聊天记录失败:', error);
      this.setData({ isLoading: false });
      this.loadMockMessages();
    }
  },

  loadMockMessages() {
    const mockMessages = this.getMockMessages();
    
    this.setData({
      messageList: mockMessages,
      isLoading: false,
      hasMore: false,
      scrollToBottom: true,
      targetUser: {
        id: 1001,
        name: '手作大师',
        avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=craft%20master%20avatar%20warm%20friendly%20handmade&image_size=square'
      }
    });

    wx.setNavigationBarTitle({
      title: '手作大师'
    });
  },

  getMockMessages() {
    return [
      {
        id: 1,
        senderId: 1001,
        senderName: '手作大师',
        senderAvatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=craft%20master%20avatar%20warm%20friendly%20handmade&image_size=square',
        content: '您好，欢迎咨询~有什么可以帮助您的吗？',
        createTime: '2024-04-27 14:20:00',
        isSelf: false,
        showAvatar: true,
        showTime: true
      },
      {
        id: 2,
        senderId: 1002,
        senderName: '我',
        senderAvatar: '',
        content: '您好，我想咨询一下您店里的手工编织羊毛围巾',
        createTime: '2024-04-27 14:22:00',
        isSelf: true,
        showAvatar: false,
        showTime: true
      },
      {
        id: 3,
        senderId: 1001,
        senderName: '手作大师',
        senderAvatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=craft%20master%20avatar%20warm%20friendly%20handmade&image_size=square',
        content: '好的~那款围巾是我亲手编织的，用的是澳洲美利奴羊毛，非常柔软保暖呢~',
        createTime: '2024-04-27 14:23:00',
        isSelf: false,
        showAvatar: true,
        showTime: false
      },
      {
        id: 4,
        senderId: 1001,
        senderName: '手作大师',
        senderAvatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=craft%20master%20avatar%20warm%20friendly%20handmade&image_size=square',
        content: '颜色有深灰、酒红、米白三种可选，您喜欢哪种颜色呢？',
        createTime: '2024-04-27 14:24:00',
        isSelf: false,
        showAvatar: false,
        showTime: true
      },
      {
        id: 5,
        senderId: 1002,
        senderName: '我',
        senderAvatar: '',
        content: '酒红色看起来不错，适合秋冬季节',
        createTime: '2024-04-27 14:26:00',
        isSelf: true,
        showAvatar: false,
        showTime: true
      },
      {
        id: 6,
        senderId: 1001,
        senderName: '手作大师',
        senderAvatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=craft%20master%20avatar%20warm%20friendly%20handmade&image_size=square',
        content: '是的~酒红色很显气质，搭配大衣非常好看！',
        createTime: '2024-04-27 14:27:00',
        isSelf: false,
        showAvatar: true,
        showTime: false
      },
      {
        id: 7,
        senderId: 1001,
        senderName: '手作大师',
        senderAvatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=craft%20master%20avatar%20warm%20friendly%20handmade&image_size=square',
        content: '我店里还有同款的帽子和手套，可以配套购买，有优惠哦~',
        createTime: '2024-04-28 10:30:00',
        isSelf: false,
        showAvatar: false,
        showTime: true
      }
    ];
  },

  processMessages(messages) {
    const { currentUserId } = this.data;
    return messages.map((msg, index, arr) => {
      const isSelf = msg.sender_id === currentUserId;
      const prevMsg = arr[index - 1];
      
      let showAvatar = true;
      let showTime = true;
      
      if (prevMsg) {
        if (prevMsg.sender_id === msg.sender_id) {
          showAvatar = false;
        }
        
        const prevTime = safeParseDate(prevMsg.create_time || prevMsg.createTime).getTime();
        const currTime = safeParseDate(msg.create_time || msg.createTime).getTime();
        if (currTime - prevTime < 5 * 60 * 1000) {
          showTime = false;
        }
      }

      return {
        id: msg.id,
        senderId: msg.sender_id,
        senderName: msg.sender_name || msg.sender?.name || '',
        senderAvatar: msg.sender_avatar || msg.sender?.avatar || '',
        content: msg.content,
        createTime: msg.create_time || msg.createTime,
        isSelf: isSelf,
        showAvatar: showAvatar,
        showTime: showTime
      };
    });
  },

  async loadMoreHistory() {
    if (!this.data.hasMore) return;
    
    this.setData({ page: this.data.page + 1 });
    await this.loadMessages();
  },

  updateNavigationBar() {
    const { messageList, targetUser } = this.data;
    if (messageList.length > 0) {
      const firstMsg = messageList[0];
      if (!firstMsg.isSelf && firstMsg.senderName) {
        wx.setNavigationBarTitle({
          title: firstMsg.senderName
        });
        this.setData({
          'targetUser.name': firstMsg.senderName,
          'targetUser.avatar': firstMsg.senderAvatar
        });
      }
    }
  },

  onInputChange(e) {
    const value = e.detail.value;
    this.setData({ inputValue: value });
  },

  onInputFocus(e) {
    this.setData({ scrollToBottom: true });
  },

  onInputBlur(e) {
  },

  async sendMessage() {
    const { inputValue, conversationId, isSending, messageList } = this.data;
    
    if (!inputValue.trim()) {
      showToast('请输入消息内容');
      return;
    }

    if (inputValue.length > 200) {
      showToast('消息内容不能超过200字');
      return;
    }

    if (isSending) return;

    this.setData({ isSending: true });

    const tempMessage = {
      id: Date.now(),
      senderId: this.data.currentUserId || 1002,
      senderName: '我',
      senderAvatar: '',
      content: inputValue.trim(),
      createTime: new Date().toISOString(),
      isSelf: true,
      showAvatar: false,
      showTime: false,
      isSending: true
    };

    const newList = [...messageList, tempMessage];
    this.setData({
      messageList: newList,
      inputValue: '',
      scrollToBottom: true
    });

    try {
      const result = await sendMessage(conversationId, inputValue.trim());
      
      const updatedList = newList.map(msg => {
        if (msg.id === tempMessage.id) {
          return {
            ...msg,
            id: result?.id || msg.id,
            isSending: false
          };
        }
        return msg;
      });

      this.setData({
        messageList: updatedList,
        isSending: false
      });

      showToast('发送成功', 'success');
    } catch (error) {
      console.log('发送消息失败:', error);
      
      const updatedList = newList.map(msg => {
        if (msg.id === tempMessage.id) {
          return {
            ...msg,
            isSending: false,
            sendFailed: true
          };
        }
        return msg;
      });

      this.setData({
        messageList: updatedList,
        isSending: false
      });

      showToast('发送失败，请重试');
    }
  },

  resendMessage(e) {
    const { id } = e.currentTarget.dataset;
    const { messageList } = this.data;
    
    const failedMsg = messageList.find(m => m.id === id);
    if (!failedMsg) return;

    this.setData({ inputValue: failedMsg.content });
    const updatedList = messageList.filter(m => m.id !== id);
    this.setData({ messageList: updatedList });
  },

  showCancelConfirm() {
    const { inputValue } = this.data;
    if (inputValue.trim()) {
      this.setData({ showCancelDialog: true });
    } else {
      wx.navigateBack();
    }
  },

  closeCancelDialog() {
    this.setData({ showCancelDialog: false });
  },

  confirmCancel() {
    this.setData({ showCancelDialog: false });
    wx.navigateBack();
  },

  formatTime(timeStr) {
    if (!timeStr) return '';
    
    const date = safeParseDate(timeStr);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
    const msgDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());

    const hour = date.getHours().toString().padStart(2, '0');
    const minute = date.getMinutes().toString().padStart(2, '0');

    if (msgDate.getTime() === today.getTime()) {
      return `${hour}:${minute}`;
    } else if (msgDate.getTime() === yesterday.getTime()) {
      return `昨天 ${hour}:${minute}`;
    } else {
      const month = date.getMonth() + 1;
      const day = date.getDate();
      return `${month}月${day}日 ${hour}:${minute}`;
    }
  },

  preventMove() {
    return;
  },

  onShareAppMessage() {
    const { targetUser } = this.data;
    return {
      title: `与${targetUser.name || '用户'}的聊天`,
      path: `/pages/chat/index?id=${this.data.conversationId}`
    };
  }
});
