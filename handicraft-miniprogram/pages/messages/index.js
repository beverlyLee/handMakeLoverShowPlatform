const {
  getMessages,
  getUnreadCount,
  getConversations,
  deleteMessage,
  batchDeleteMessages,
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

function getPreviewText(content) {
  if (!content) return '';
  const str = String(content);
  const firstLine = str.split('\n')[0];
  return firstLine.substring(0, 60);
}

function isItemUnread(item) {
  if (item.itemType === 'conversation') {
    return item.unread_count > 0;
  }
  return !item.isRead;
}

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
    isEditMode: false,
    swipeButtonWidth: 140,
    currentSwipedIndex: null
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
          system: 0,
          order: 0,
          activity: 0,
          chat: 0,
          total: 0
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
              createTime: item.last_message_time,
              preview: getPreviewText(item.last_message),
              isUnread: item.unread_count > 0
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
              typeConfig: MESSAGE_TYPES[item.type] || MESSAGE_TYPES.system,
              preview: getPreviewText(item.content),
              isUnread: !(item.is_read || false)
            }));
          }
        } catch (msgError) {
          console.log('获取消息列表失败，使用默认数据:', msgError);
        }
      }

      if (messages.length === 0 && conversations.length === 0) {
        this.setData({ 
          messageList: [], 
          isLoading: false,
          hasMore: false
        });
        return;
      }

      let allItems = [];
      if (activeTab === 'all') {
        allItems = [
          ...messages.map(m => ({ ...m, itemType: 'message', isSelected: false, x: 0 })),
          ...conversations.map(c => ({ ...c, itemType: 'conversation', isSelected: false, x: 0 }))
        ].sort((a, b) => {
          const timeA = safeParseDate(a.createTime || a.last_message_time || 0).getTime();
          const timeB = safeParseDate(b.createTime || b.last_message_time || 0).getTime();
          return timeB - timeA;
        });
      } else if (activeTab === 'chat') {
        allItems = conversations.map(c => ({ ...c, itemType: 'conversation', isSelected: false, x: 0 }));
      } else {
        allItems = messages.map(m => ({ ...m, itemType: 'message', isSelected: false, x: 0 }));
      }

      this.setData({
        messageList: allItems,
        conversationList: conversations,
        isLoading: false,
        hasMore: allItems.length >= pageSize
      });
    } catch (error) {
      console.log('加载消息失败:', error);
      this.setData({ 
        isLoading: false,
        messageList: []
      });
      showToast('加载消息失败', 'error');
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
              isSelected: false,
              x: 0,
              preview: getPreviewText(item.last_message),
              isUnread: item.unread_count > 0
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
              isSelected: false,
              x: 0,
              preview: getPreviewText(item.content),
              isUnread: !(item.is_read || false)
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
      console.log('加载更多消息失败:', error);
      this.setData({ 
        isLoading: false,
        page: this.data.page - 1
      });
    }
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
      console.log('标记已读失败:', error);
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
      console.log('删除失败:', error);
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
      isSelected: false,
      x: 0
    }));

    this.setData({
      isEditMode: newIsEditMode,
      selectedIds: [],
      messageList: updatedList,
      currentSwipedIndex: null
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
      console.log('批量删除失败:', error);
      showToast('删除失败，请重试');
    }
  },

  closeOtherSwipedItems(currentIndex) {
    const { messageList, currentSwipedIndex } = this.data;
    
    if (currentSwipedIndex !== null && currentSwipedIndex !== currentIndex) {
      const updatedList = messageList.map((item, index) => {
        if (index === currentSwipedIndex && item.x !== 0) {
          return { ...item, x: 0 };
        }
        return item;
      });
      
      this.setData({
        messageList: updatedList,
        currentSwipedIndex: null
      });
    }
  },

  onMovableViewChange(e) {
    const { source, x } = e.detail;
    const index = e.currentTarget.dataset.index;
    const { messageList, swipeButtonWidth } = this.data;
    
    if (source === 'touch') {
      this.closeOtherSwipedItems(index);
    }
  },

  onSwipeEnd(e) {
    const index = e.currentTarget.dataset.index;
    const { messageList, swipeButtonWidth } = this.data;
    
    const item = messageList[index];
    const currentX = item.x || 0;
    
    const hasMarkButton = !item.isRead || (item.itemType === 'conversation' && item.unread_count > 0);
    const totalButtonWidth = hasMarkButton ? swipeButtonWidth * 2 : swipeButtonWidth;
    
    const threshold = totalButtonWidth / 2;
    
    let newX = 0;
    
    if (currentX < -threshold) {
      newX = -totalButtonWidth;
    } else {
      newX = 0;
    }
    
    const updatedList = messageList.map((m, i) => {
      if (i === index) {
        return { ...m, x: newX };
      }
      return m;
    });
    
    this.setData({
      messageList: updatedList,
      currentSwipedIndex: newX < 0 ? index : null
    });
  },

  onSwipeAction(e) {
    const { action, index, id, itemType } = e.currentTarget.dataset;
    const { messageList } = this.data;
    
    if (action === 'markRead') {
      this.handleMarkReadByIndex(index, id, itemType);
    } else if (action === 'delete') {
      wx.showModal({
        title: '确认删除',
        content: '确定要删除这条消息吗？',
        confirmColor: '#DC3545',
        success: (res) => {
          if (res.confirm) {
            this.handleDeleteByIndex(index, id, itemType);
          }
        }
      });
    }
  },

  handleMarkReadByIndex(index, id, itemType) {
    const { messageList } = this.data;
    
    wx.showLoading({ title: '处理中...', mask: true });

    if (itemType === 'message') {
      markAsRead(id).then(() => {
        const updatedList = messageList.map((m, i) => {
          if (i === index) {
            return { ...m, isRead: true, x: 0 };
          }
          return m;
        });
        
        this.setData({
          messageList: updatedList,
          currentSwipedIndex: null
        });
        
        wx.hideLoading();
        showToast('已标记为已读', 'success');
        this.loadUnreadCount();
      }).catch(() => {
        wx.hideLoading();
        showToast('操作失败，请重试');
      });
    } else {
      const updatedList = messageList.map((m, i) => {
        if (i === index) {
          return { ...m, unread_count: 0, isRead: true, x: 0 };
        }
        return m;
      });
      
      this.setData({
        messageList: updatedList,
        currentSwipedIndex: null
      });
      
      wx.hideLoading();
      showToast('已标记为已读', 'success');
      this.loadUnreadCount();
    }
  },

  handleDeleteByIndex(index, id, itemType) {
    const { messageList } = this.data;
    
    wx.showLoading({ title: '删除中...', mask: true });

    try {
      if (itemType === 'message') {
        deleteMessage(id).then(() => {
          const newList = messageList.filter((m, i) => i !== index);
          
          this.setData({
            messageList: newList,
            currentSwipedIndex: null
          });
          
          wx.hideLoading();
          showToast('删除成功', 'success');
          this.loadUnreadCount();
        }).catch(() => {
          wx.hideLoading();
          showToast('删除失败，请重试');
        });
      } else {
        const newList = messageList.filter((m, i) => i !== index);
        
        this.setData({
          messageList: newList,
          currentSwipedIndex: null
        });
        
        wx.hideLoading();
        showToast('删除成功', 'success');
        this.loadUnreadCount();
      }
    } catch (error) {
      wx.hideLoading();
      console.log('删除失败:', error);
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
