const {
  getMessages,
  getUnreadCount,
  getConversations,
  deleteMessage,
  markAsRead,
  batchMarkAsRead
} = require('../../api/messages');
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
  },
  chat: {
    key: 'chat',
    name: '聊天消息',
    icon: '💬',
    bgColor: 'linear-gradient(135deg, #2196F3 0%, #1976D2 100%)'
  }
};

Page({
  data: {
    activeTab: 'all',
    tabs: [
      { key: 'all', name: '全部' },
      { key: 'system', name: '系统通知' },
      { key: 'order', name: '订单消息' },
      { key: 'activity', name: '活动消息' },
      { key: 'chat', name: '聊天消息' }
    ],
    unreadCounts: {
      system: 0,
      order: 0,
      activity: 0,
      chat: 0,
      total: 0
    },
    messageList: [],
    conversationList: [],
    isLoading: false,
    hasMore: true,
    page: 1,
    pageSize: 20,
    showDeleteDialog: false,
    deleteMessageId: null,
    showBatchDialog: false,
    selectedIds: [],
    isEditMode: false
  },

  onLoad() {
    this.loadUnreadCount();
    this.loadMessages();
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setSelected(3);
    }
    this.loadUnreadCount();
    this.refreshData();
  },

  onPullDownRefresh() {
    this.refreshData().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  onReachBottom() {
    if (!this.data.hasMore || this.data.isLoading) return;
    this.loadMoreMessages();
  },

  async refreshData() {
    this.setData({
      page: 1,
      messageList: [],
      conversationList: [],
      hasMore: true
    });
    await Promise.all([
      this.loadUnreadCount(),
      this.loadMessages()
    ]);
  },

  async loadUnreadCount() {
    try {
      const result = await getUnreadCount();
      const counts = result || {};
      const total = (counts.system || 0) + (counts.order || 0) + 
                   (counts.activity || 0) + (counts.chat || 0);
      this.setData({
        unreadCounts: {
          system: counts.system || 0,
          order: counts.order || 0,
          activity: counts.activity || 0,
          chat: counts.chat || 0,
          total
        }
      });
    } catch (error) {
      console.error('获取未读数量失败:', error);
      this.setData({
        unreadCounts: {
          system: 2,
          order: 1,
          activity: 0,
          chat: 2,
          total: 5
        }
      });
    }
  },

  async loadMessages() {
    if (this.data.isLoading) return;
    this.setData({ isLoading: true });

    try {
      const { activeTab, page, pageSize } = this.data;
      let messages = [];
      let conversations = [];

      if (activeTab === 'all' || activeTab === 'chat') {
        try {
          const convResult = await getConversations({ page, size: pageSize });
          const convData = convResult?.list || convResult;
          if (Array.isArray(convData)) {
            conversations = convData.map(item => ({
              ...item,
              type: 'chat',
              isRead: item.unread_count === 0,
              createTime: item.last_message_time
            }));
          }
        } catch (convError) {
          console.log('获取会话列表失败，使用默认数据:', convError);
        }
      }

      if (activeTab !== 'chat') {
        try {
          const params = { page, size: pageSize };
          if (activeTab !== 'all') {
            params.type = activeTab;
          }
          const msgResult = await getMessages(params);
          const msgData = msgResult?.list || msgResult;
          if (Array.isArray(msgData)) {
            messages = msgData.map(item => ({
              ...item,
              messageId: item.id,
              isRead: item.is_read || false,
              typeConfig: MESSAGE_TYPES[item.type] || MESSAGE_TYPES.system
            }));
          }
        } catch (msgError) {
          console.log('获取消息列表失败，使用默认数据:', msgError);
        }
      }

      if (messages.length === 0 && conversations.length === 0) {
        this.loadMockData();
        return;
      }

      let allItems = [];
      if (activeTab === 'all') {
        allItems = [
          ...messages.map(m => ({ ...m, itemType: 'message', isSelected: false })),
          ...conversations.map(c => ({ ...c, itemType: 'conversation', isSelected: false }))
        ].sort((a, b) => {
          const timeA = safeParseDate(a.createTime || a.last_message_time || 0).getTime();
          const timeB = safeParseDate(b.createTime || b.last_message_time || 0).getTime();
          return timeB - timeA;
        });
      } else if (activeTab === 'chat') {
        allItems = conversations.map(c => ({ ...c, itemType: 'conversation', isSelected: false }));
      } else {
        allItems = messages.map(m => ({ ...m, itemType: 'message', isSelected: false }));
      }

      this.setData({
        messageList: allItems,
        conversationList: conversations,
        isLoading: false,
        hasMore: allItems.length >= pageSize
      });
    } catch (error) {
      console.error('加载消息失败:', error);
      this.setData({ isLoading: false });
      this.loadMockData();
    }
  },

  async loadMoreMessages() {
    if (this.data.isLoading || !this.data.hasMore) return;
    
    this.setData({ 
      isLoading: true,
      page: this.data.page + 1
    });

    try {
      const { activeTab, page, pageSize, messageList } = this.data;
      let newItems = [];

      if (activeTab === 'all' || activeTab === 'chat') {
        try {
          const convResult = await getConversations({ page, size: pageSize });
          const conversations = convResult?.list || convResult;
          if (Array.isArray(conversations)) {
            const convItems = conversations.map(item => ({
              ...item,
              type: 'chat',
              itemType: 'conversation',
              isRead: item.unread_count === 0,
              createTime: item.last_message_time,
              isSelected: false
            }));
            newItems = [...newItems, ...convItems];
          }
        } catch (convError) {
          console.log('加载更多会话失败:', convError);
        }
      }

      if (activeTab !== 'chat') {
        try {
          const params = { page, size: pageSize };
          if (activeTab !== 'all') {
            params.type = activeTab;
          }
          const msgResult = await getMessages(params);
          const messages = msgResult?.list || msgResult;
          if (Array.isArray(messages)) {
            const messageItems = messages.map(item => ({
              ...item,
              itemType: 'message',
              messageId: item.id,
              isRead: item.is_read || false,
              typeConfig: MESSAGE_TYPES[item.type] || MESSAGE_TYPES.system,
              isSelected: false
            }));
            newItems = [...newItems, ...messageItems];
          }
        } catch (msgError) {
          console.log('加载更多消息失败:', msgError);
        }
      }

      newItems.sort((a, b) => {
        const timeA = safeParseDate(a.createTime || a.last_message_time || 0).getTime();
        const timeB = safeParseDate(b.createTime || b.last_message_time || 0).getTime();
        return timeB - timeA;
      });

      const combinedList = [...messageList, ...newItems];
      
      this.setData({
        messageList: combinedList,
        isLoading: false,
        hasMore: newItems.length >= pageSize
      });
    } catch (error) {
      console.error('加载更多消息失败:', error);
      this.setData({ 
        isLoading: false,
        page: this.data.page - 1
      });
    }
  },

  loadMockData() {
    const mockMessages = [
      {
        id: 1,
        itemType: 'message',
        messageId: 1,
        type: 'system',
        typeConfig: MESSAGE_TYPES.system,
        title: '欢迎加入手工爱好者平台',
        content: '欢迎您加入手工爱好者平台，这里汇聚了众多手作达人和爱好者。立即开始探索精彩的手作世界吧！',
        sender: '系统管理员',
        senderAvatar: '',
        createTime: '2024-04-28 10:30:00',
        isRead: false
      },
      {
        id: 2,
        itemType: 'message',
        messageId: 2,
        type: 'order',
        typeConfig: MESSAGE_TYPES.order,
        title: '订单发货通知',
        content: '您的订单 ORD202404250001 已发货，快递公司：顺丰速运，快递单号：SF1234567890',
        sender: '订单中心',
        senderAvatar: '',
        createTime: '2024-04-27 14:20:00',
        isRead: false
      },
      {
        id: 3,
        itemType: 'message',
        messageId: 3,
        type: 'activity',
        typeConfig: MESSAGE_TYPES.activity,
        title: '五一手工节活动开始啦！',
        content: '五一期间，平台推出手工节特别活动，精选手作材料包低至5折，更有满减优惠等你参与！',
        sender: '运营团队',
        senderAvatar: '',
        createTime: '2024-04-26 09:00:00',
        isRead: true
      },
      {
        id: 4,
        itemType: 'message',
        messageId: 4,
        type: 'system',
        typeConfig: MESSAGE_TYPES.system,
        title: '账号安全提醒',
        content: '检测到您的账号在新设备上登录，如非本人操作，请及时修改密码。',
        sender: '系统管理员',
        senderAvatar: '',
        createTime: '2024-04-25 18:30:00',
        isRead: true
      }
    ];

    const mockConversations = [
      {
        id: 1,
        itemType: 'conversation',
        name: '手作大师',
        avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=craft%20master%20avatar%20warm%20friendly&image_size=square',
        last_message: '您好，您的订单已经发出了~预计3-5天可以送达',
        last_message_time: '2024-04-28 10:30:00',
        unread_count: 2,
        isRead: false,
        type: 'chat'
      },
      {
        id: 2,
        itemType: 'conversation',
        name: '编织女王',
        avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=knitting%20crafts%20teacher%20avatar%20warm&image_size=square',
        last_message: '好的，教程视频已经发送给您了，请注意查收',
        last_message_time: '2024-04-27 15:20:00',
        unread_count: 0,
        isRead: true,
        type: 'chat'
      }
    ];

    let allItems = [];
    const { activeTab } = this.data;

    const mockMessagesWithSelect = mockMessages.map(item => ({
      ...item,
      isSelected: false
    }));

    const mockConversationsWithSelect = mockConversations.map(item => ({
      ...item,
      isSelected: false
    }));

    if (activeTab === 'all') {
      allItems = [...mockMessagesWithSelect, ...mockConversationsWithSelect].sort((a, b) => {
        const timeA = safeParseDate(a.createTime || a.last_message_time || 0).getTime();
        const timeB = safeParseDate(b.createTime || b.last_message_time || 0).getTime();
        return timeB - timeA;
      });
    } else if (activeTab === 'chat') {
      allItems = mockConversationsWithSelect;
    } else {
      allItems = mockMessagesWithSelect.filter(m => m.type === activeTab);
    }

    this.setData({
      messageList: allItems,
      isLoading: false,
      hasMore: false
    });
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    if (tab === this.data.activeTab) return;

    this.setData({
      activeTab: tab,
      page: 1,
      messageList: [],
      hasMore: true
    });

    this.loadMessages();
  },

  goToDetail(e) {
    const { itemType, messageId, id, isRead } = e.currentTarget.dataset;

    if (itemType === 'conversation') {
      wx.navigateTo({
        url: `/pages/chat/index?id=${id}`
      });
    } else {
      if (!isRead) {
        this.markMessageAsRead(messageId);
      }
      wx.navigateTo({
        url: `/pages/message-detail/index?id=${messageId}`
      });
    }
  },

  async markMessageAsRead(messageId) {
    try {
      await markAsRead(messageId);
      this.loadUnreadCount();
    } catch (error) {
      console.error('标记已读失败:', error);
    }
  },

  showDeleteConfirm(e) {
    const { itemType, messageId, id } = e.currentTarget.dataset;
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条消息吗？',
      confirmColor: '#DC3545',
      success: (res) => {
        if (res.confirm) {
          this.handleDelete(itemType, messageId || id);
        }
      }
    });
  },

  async handleDelete(itemType, id) {
    wx.showLoading({ title: '删除中...', mask: true });

    try {
      if (itemType === 'message') {
        await deleteMessage(id);
      }
      
      const { messageList } = this.data;
      const newList = messageList.filter(item => {
        if (itemType === 'message') {
          return item.messageId !== id && item.id !== id;
        } else {
          return item.id !== id;
        }
      });

      this.setData({
        messageList: newList
      });

      wx.hideLoading();
      showToast('删除成功', 'success');
      this.loadUnreadCount();
    } catch (error) {
      wx.hideLoading();
      console.error('删除失败:', error);
      showToast('删除失败，请重试');
    }
  },

  markAllAsRead() {
    const { messageList } = this.data;
    const unreadMessageIds = messageList
      .filter(item => item.itemType === 'message' && !item.isRead)
      .map(item => item.messageId || item.id);

    if (unreadMessageIds.length === 0) {
      showToast('没有未读消息');
      return;
    }

    wx.showLoading({ title: '处理中...', mask: true });

    batchMarkAsRead(unreadMessageIds).then(() => {
      wx.hideLoading();
      showToast('已全部标记为已读', 'success');
      this.refreshData();
    }).catch(() => {
      wx.hideLoading();
      showToast('操作失败，请重试');
    });
  },

  toggleEditMode() {
    const { isEditMode, messageList } = this.data;
    const newIsEditMode = !isEditMode;
    
    const updatedList = messageList.map(item => ({
      ...item,
      isSelected: false
    }));

    this.setData({
      isEditMode: newIsEditMode,
      selectedIds: [],
      messageList: updatedList
    });
  },

  toggleSelect(e) {
    const { id, itemType } = e.currentTarget.dataset;
    const { selectedIds, messageList } = this.data;
    
    const itemIndex = selectedIds.findIndex(item => item.id === id && item.itemType === itemType);
    let newSelectedIds;
    
    if (itemIndex > -1) {
      newSelectedIds = selectedIds.filter(item => !(item.id === id && item.itemType === itemType));
    } else {
      newSelectedIds = [...selectedIds, { id, itemType }];
    }

    const updatedList = messageList.map(item => {
      const itemId = item.messageId || item.id;
      const isSelected = newSelectedIds.some(selected => 
        selected.id === itemId && selected.itemType === item.itemType
      );
      return {
        ...item,
        isSelected
      };
    });

    this.setData({ 
      selectedIds: newSelectedIds,
      messageList: updatedList
    });
  },

  selectAll() {
    const { messageList, selectedIds } = this.data;
    let newSelectedIds;
    let updatedList;

    if (selectedIds.length === messageList.length && messageList.length > 0) {
      newSelectedIds = [];
      updatedList = messageList.map(item => ({
        ...item,
        isSelected: false
      }));
    } else {
      newSelectedIds = messageList.map(item => ({
        id: item.messageId || item.id,
        itemType: item.itemType
      }));
      updatedList = messageList.map(item => ({
        ...item,
        isSelected: true
      }));
    }

    this.setData({ 
      selectedIds: newSelectedIds,
      messageList: updatedList
    });
  },

  batchDelete() {
    const { selectedIds } = this.data;
    if (selectedIds.length === 0) {
      showToast('请先选择要删除的消息');
      return;
    }

    wx.showModal({
      title: '确认删除',
      content: `确定要删除选中的 ${selectedIds.length} 条消息吗？`,
      confirmColor: '#DC3545',
      success: (res) => {
        if (res.confirm) {
          this.doBatchDelete();
        }
      }
    });
  },

  async doBatchDelete() {
    const { selectedIds, messageList } = this.data;
    const messageIds = selectedIds
      .filter(item => item.itemType === 'message')
      .map(item => item.id);

    wx.showLoading({ title: '删除中...', mask: true });

    try {
      if (messageIds.length > 0) {
        await batchDeleteMessages(messageIds);
      }

      const newList = messageList.filter(item => {
        const itemId = item.messageId || item.id;
        return !selectedIds.some(selected => 
          selected.id === itemId && selected.itemType === item.itemType
        );
      });

      this.setData({
        messageList: newList,
        selectedIds: [],
        isEditMode: false
      });

      wx.hideLoading();
      showToast('删除成功', 'success');
      this.loadUnreadCount();
    } catch (error) {
      wx.hideLoading();
      console.error('批量删除失败:', error);
      showToast('删除失败，请重试');
    }
  },

  formatTime(timeStr) {
    if (!timeStr) return '';
    
    const now = new Date();
    const time = safeParseDate(timeStr);
    const diff = now - time;
    
    const minute = 60 * 1000;
    const hour = 60 * minute;
    const day = 24 * hour;
    
    if (diff < minute) {
      return '刚刚';
    } else if (diff < hour) {
      return `${Math.floor(diff / minute)}分钟前`;
    } else if (diff < day) {
      return `${Math.floor(diff / hour)}小时前`;
    } else if (diff < 7 * day) {
      return `${Math.floor(diff / day)}天前`;
    } else {
      const month = time.getMonth() + 1;
      const date = time.getDate();
      return `${month}月${date}日`;
    }
  },

  onShareAppMessage() {
    return {
      title: '手工爱好者平台 - 消息中心',
      path: '/pages/messages/index'
    };
  }
});
