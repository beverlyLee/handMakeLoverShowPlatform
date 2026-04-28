const { 
  getConversationMessages, 
  sendMessage, 
  getMessagesWithUser,
  sendDirectChat,
  contactThroughOrder,
  getConversationWithUser
} = require('../../api/messages');
const { showToast, safeParseDate } = require('../../utils/util');
const storage = require('../../utils/storage');

Page({
  data: {
    conversationId: null,
    targetUserId: null,
    orderId: null,
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
    this.initUserInfo();
    
    if (options.id) {
      this.setData({ 
        conversationId: parseInt(options.id)
      });
      this.loadMessagesByConversation();
    } else if (options.target_user_id) {
      this.setData({ 
        targetUserId: parseInt(options.target_user_id),
        targetUser: {
          id: parseInt(options.target_user_id),
          name: options.target_user_name || '用户',
          avatar: options.target_user_avatar || ''
        }
      });
      if (options.target_user_name) {
        wx.setNavigationBarTitle({
          title: options.target_user_name
        });
      }
      this.loadMessagesWithUser();
    } else if (options.order_id) {
      this.setData({ 
        orderId: options.order_id
      });
      this.initFromOrder();
    } else {
      showToast('参数错误');
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

  async initFromOrder() {
    const { orderId } = this.data;
    this.setData({ isLoading: true });

    try {
      const result = await contactThroughOrder(orderId, '');
      
      if (result && result.conversation) {
        this.setData({
          conversationId: result.conversation.id,
          targetUserId: result.target_user_id,
          targetUser: {
            id: result.target_user_id,
            name: result.conversation.other_user_name || '用户',
            avatar: result.conversation.other_user_avatar || ''
          }
        });
        
        if (result.conversation.other_user_name) {
          wx.setNavigationBarTitle({
            title: result.conversation.other_user_name
          });
        }
        
        this.loadMessagesByConversation();
      } else {
        this.setData({ isLoading: false });
      }
    } catch (error) {
      console.log('通过订单初始化聊天失败:', error);
      this.setData({ isLoading: false });
      showToast('加载失败，请重试');
    }
  },

  async loadMessagesByConversation() {
    const { conversationId, page, pageSize } = this.data;
    this.setData({ isLoading: true });

    try {
      const result = await getConversationMessages(conversationId, { page, size: pageSize });
      const messages = result?.list || result || [];
      
      const processedMessages = this.processMessages(messages);
      
      const conversation = result?.conversation;
      if (conversation && conversation.other_user_name) {
        this.setData({
          'targetUser.name': conversation.other_user_name,
          'targetUser.avatar': conversation.other_user_avatar
        });
        wx.setNavigationBarTitle({
          title: conversation.other_user_name
        });
      }

      this.setData({
        messageList: processedMessages,
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

  async loadMessagesWithUser() {
    const { targetUserId, page, pageSize } = this.data;
    this.setData({ isLoading: true });

    try {
      const result = await getMessagesWithUser(targetUserId, { page, size: pageSize });
      const messages = result?.list || result || [];
      
      const processedMessages = this.processMessages(messages);
      
      const conversation = result?.conversation;
      if (conversation) {
        this.setData({
          conversationId: conversation.id
        });
        if (conversation.other_user_name && !this.data.targetUser.name) {
          this.setData({
            'targetUser.name': conversation.other_user_name,
            'targetUser.avatar': conversation.other_user_avatar
          });
          wx.setNavigationBarTitle({
            title: conversation.other_user_name
          });
        }
      }

      this.setData({
        messageList: processedMessages,
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
      scrollToBottom: true
    });
  },

  getMockMessages() {
    return [];
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
    
    if (this.data.conversationId) {
      await this.loadMessagesByConversation();
    } else if (this.data.targetUserId) {
      await this.loadMessagesWithUser();
    }
  },

  updateNavigationBar() {
    const { messageList, targetUser } = this.data;
    if (messageList.length > 0 && !targetUser.name) {
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
    const { inputValue, conversationId, targetUserId, isSending, messageList, currentUserId } = this.data;
    
    if (!inputValue.trim()) {
      showToast('请输入消息内容');
      return;
    }

    if (inputValue.length > 500) {
      showToast('消息内容不能超过500字');
      return;
    }

    if (isSending) return;

    this.setData({ isSending: true });

    const tempMessage = {
      id: Date.now(),
      senderId: currentUserId || 0,
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
      let result;
      
      if (conversationId) {
        result = await sendMessage(conversationId, inputValue.trim());
      } else if (targetUserId) {
        result = await sendDirectChat(targetUserId, inputValue.trim());
        if (result && result.conversation) {
          this.setData({
            conversationId: result.conversation.id
          });
        }
      }

      const sentMessage = result?.message || result;
      
      const updatedList = newList.map(msg => {
        if (msg.id === tempMessage.id) {
          return {
            ...msg,
            id: sentMessage?.id || msg.id,
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
    const { targetUser, conversationId } = this.data;
    return {
      title: `与${targetUser.name || '用户'}的聊天`,
      path: `/pages/chat/index?id=${conversationId}`
    };
  }
});
