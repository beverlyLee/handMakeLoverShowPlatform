<template>
  <div class="page-card">
    <div class="page-header">
      <span class="page-title">消息管理</span>
      <div style="margin-left: auto; display: flex; gap: 12px;">
        <el-button type="primary" @click="openAnnouncementDialog">
          <el-icon><Plus /></el-icon>
          发布公告
        </el-button>
        <el-button type="success" @click="openStatsDialog">
          <el-icon><DataLine /></el-icon>
          统计分析
        </el-button>
      </div>
    </div>
    
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="全部消息" name="all" />
      <el-tab-pane label="公告消息" name="announcement" />
      <el-tab-pane label="私信列表" name="conversation" />
    </el-tabs>
    
    <div class="filter-bar" v-if="activeTab !== 'conversation'">
      <el-input
        v-model="queryParams.keyword"
        placeholder="搜索标题/内容"
        clearable
        style="width: 200px;"
        @keyup.enter="handleSearch"
      />
      <el-select
        v-model="queryParams.type"
        placeholder="消息类型"
        clearable
        style="width: 140px;"
      >
        <el-option
          v-for="(name, key) in messageTypeOptions"
          :key="key"
          :label="name"
          :value="key"
        />
      </el-select>
      <el-select
        v-model="queryParams.subtype"
        placeholder="公告子类型"
        clearable
        style="width: 140px;"
        v-if="activeTab === 'announcement'"
      >
        <el-option
          v-for="(name, key) in announcementSubtypeOptions"
          :key="key"
          :label="name"
          :value="key"
        />
      </el-select>
      <el-select
        v-model="queryParams.recipient_type"
        placeholder="接收对象"
        clearable
        style="width: 140px;"
        v-if="activeTab === 'announcement'"
      >
        <el-option
          v-for="(name, key) in recipientTypeOptions"
          :key="key"
          :label="name"
          :value="key"
        />
      </el-select>
      <el-select
        v-model="queryParams.is_read"
        placeholder="已读状态"
        clearable
        style="width: 120px;"
      >
        <el-option label="已读" :value="true" />
        <el-option label="未读" :value="false" />
      </el-select>
      <el-select
        v-model="queryParams.is_expired"
        placeholder="过期状态"
        clearable
        style="width: 120px;"
        v-if="activeTab === 'announcement'"
      >
        <el-option label="未过期" :value="false" />
        <el-option label="已过期" :value="true" />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        style="width: 280px;"
      />
      <el-button type="primary" @click="handleSearch">
        <el-icon><Search /></el-icon>
        搜索
      </el-button>
      <el-button @click="resetQuery">
        <el-icon><Refresh /></el-icon>
        重置
      </el-button>
    </div>
    
    <div class="filter-bar" v-else>
      <el-input
        v-model="queryParams.keyword"
        placeholder="搜索用户昵称"
        clearable
        style="width: 200px;"
        @keyup.enter="handleSearch"
      />
      <el-button type="primary" @click="handleSearch">
        <el-icon><Search /></el-icon>
        搜索
      </el-button>
    </div>
    
    <div class="table-wrapper" v-if="activeTab !== 'conversation'">
      <el-table
        :data="tableData"
        stripe
        style="width: 100%"
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="type_name" label="类型" width="100">
          <template #default="scope">
            <el-tag :type="getMessageType(scope.row.type)" size="small">
              {{ scope.row.type_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="subtype_name" label="子类型" width="100" v-if="activeTab === 'announcement'">
          <template #default="scope">
            {{ scope.row.subtype_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200">
          <template #default="scope">
            <div style="display: flex; flex-direction: column; gap: 4px;">
              <span>{{ scope.row.title }}</span>
              <div style="display: flex; gap: 4px;">
                <el-tag v-if="scope.row.is_announcement" type="warning" size="small" effect="dark">
                  公告
                </el-tag>
                <el-tag v-if="scope.row.is_expired" type="info" size="small">
                  已过期
                </el-tag>
                <el-tag v-if="!scope.row.is_read" type="danger" size="small">
                  未读
                </el-tag>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="recipient_type_name" label="接收对象" width="100" v-if="activeTab === 'announcement'">
          <template #default="scope">
            {{ scope.row.recipient_type_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="user_nickname" label="接收用户" width="120">
          <template #default="scope">
            <div v-if="scope.row.user_id">
              <div>ID: {{ scope.row.user_id }}</div>
              <div style="color: #666; font-size: 12px;">{{ scope.row.user_nickname || '-' }}</div>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="sender" label="发送者" width="100" />
        <el-table-column prop="expire_time" label="过期时间" width="160" v-if="activeTab === 'announcement'">
          <template #default="scope">
            <span v-if="scope.row.expire_time">{{ scope.row.expire_time }}</span>
            <span v-else style="color: #999;">永不过期</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="scope">
            <div class="operation-btns">
              <el-button type="primary" link @click="handleView(scope.row)">
                详情
              </el-button>
              <el-button type="danger" link @click="handleDelete(scope.row)">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <div class="table-wrapper" v-else>
      <el-table
        :data="tableData"
        stripe
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="id" label="会话ID" width="100" />
        <el-table-column prop="user1_id" label="用户1" width="150">
          <template #default="scope">
            <div v-if="scope.row.user1_info">
              <el-avatar :src="scope.row.user1_info.avatar" :size="32" />
              <span style="margin-left: 8px;">
                {{ scope.row.user1_info.nickname }}
              </span>
              <div style="font-size: 12px; color: #999;">ID: {{ scope.row.user1_id }}</div>
            </div>
            <span v-else>{{ scope.row.user1_id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="user2_id" label="用户2" width="150">
          <template #default="scope">
            <div v-if="scope.row.user2_info">
              <el-avatar :src="scope.row.user2_info.avatar" :size="32" />
              <span style="margin-left: 8px;">
                {{ scope.row.user2_info.nickname }}
              </span>
              <div style="font-size: 12px; color: #999;">ID: {{ scope.row.user2_id }}</div>
            </div>
            <span v-else>{{ scope.row.user2_id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_message" label="最后消息" min-width="200">
          <template #default="scope">
            <div v-if="scope.row.last_message">
              <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                {{ scope.row.last_message }}
              </div>
              <div style="font-size: 12px; color: #999;">
                {{ scope.row.updated_at }}
              </div>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="unread_count" label="未读数" width="80">
          <template #default="scope">
            <el-tag v-if="scope.row.unread_count > 0" type="danger" size="small">
              {{ scope.row.unread_count }}
            </el-tag>
            <span v-else style="color: #999;">0</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
      </el-table>
    </div>
    
    <div class="pagination-wrapper" v-if="activeTab !== 'conversation'">
      <div style="display: flex; align-items: center; gap: 12px;">
        <el-button
          type="danger"
          :disabled="selectedIds.length === 0"
          @click="handleBatchDelete"
        >
          批量删除
        </el-button>
      </div>
      <el-pagination
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.size"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchData"
        @current-change="fetchData"
      />
    </div>
    
    <div class="pagination-wrapper" v-else>
      <el-pagination
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.size"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchData"
        @current-change="fetchData"
      />
    </div>
    
    <el-dialog
      v-model="announcementDialogVisible"
      title="发布公告"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        :model="announcementForm"
        :rules="announcementRules"
        label-width="100px"
        ref="announcementFormRef"
      >
        <el-form-item label="公告标题" prop="title">
          <el-input
            v-model="announcementForm.title"
            placeholder="请输入公告标题（至少5个字符）"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="公告子类型" prop="subtype">
          <el-select v-model="announcementForm.subtype" style="width: 100%;">
            <el-option
              v-for="(name, key) in announcementSubtypeOptions"
              :key="key"
              :label="name"
              :value="key"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="接收对象" prop="recipient_type">
          <el-select v-model="announcementForm.recipient_type" style="width: 100%;">
            <el-option
              v-for="(name, key) in recipientTypeOptions"
              :key="key"
              :label="name"
              :value="key"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="过期时间" prop="expire_time">
          <el-date-picker
            v-model="announcementForm.expire_time"
            type="datetime"
            placeholder="选择过期时间（留空则永不过期）"
            style="width: 100%;"
            :disabled-date="disabledDate"
          />
          <div style="font-size: 12px; color: #999; margin-top: 4px;">
            公告在过期后将不再向用户展示
          </div>
        </el-form-item>
        <el-form-item label="公告内容" prop="content">
          <el-input
            v-model="announcementForm.content"
            type="textarea"
            :rows="8"
            placeholder="请输入公告内容（至少20个字符）"
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="announcementDialogVisible = false">取消</el-button>
        <el-button @click="previewAnnouncement">
          <el-icon><View /></el-icon>
          预览
        </el-button>
        <el-button
          type="primary"
          @click="submitAnnouncement"
          :loading="submitting"
        >
          发布公告
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="previewDialogVisible"
      title="公告预览"
      width="500px"
    >
      <div style="padding: 20px; background: #f5f5f5; border-radius: 8px;">
        <div style="font-size: 16px; font-weight: bold; margin-bottom: 12px; color: #333;">
          {{ announcementForm.title || '(暂无标题)' }}
        </div>
        <div style="font-size: 12px; color: #999; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #e0e0e0;">
          <span>子类型：{{ announcementSubtypeOptions[announcementForm.subtype] }}</span>
          <span style="margin-left: 20px;">接收对象：{{ recipientTypeOptions[announcementForm.recipient_type] }}</span>
        </div>
        <div style="font-size: 14px; line-height: 1.8; color: #333; white-space: pre-wrap;">
          {{ announcementForm.content || '(暂无内容)' }}
        </div>
        <div v-if="announcementForm.expire_time" style="margin-top: 16px; padding-top: 12px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #999;">
          过期时间：{{ formatDate(announcementForm.expire_time) }}
        </div>
      </div>
      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="detailVisible"
      title="消息详情"
      width="600px"
    >
      <el-descriptions :column="2" border v-if="currentMessage">
        <el-descriptions-item label="消息ID">{{ currentMessage.id }}</el-descriptions-item>
        <el-descriptions-item label="消息类型">
          <el-tag :type="getMessageType(currentMessage.type)">
            {{ currentMessage.type_name }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="消息标题">{{ currentMessage.title }}</el-descriptions-item>
        <el-descriptions-item label="发送者">{{ currentMessage.sender }}</el-descriptions-item>
        <el-descriptions-item label="接收用户ID">{{ currentMessage.user_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="接收用户">{{ currentMessage.user_nickname || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentMessage.created_at }}</el-descriptions-item>
        <el-descriptions-item label="是否已读">
          <el-tag :type="currentMessage.is_read ? 'success' : 'danger'" size="small">
            {{ currentMessage.is_read ? '已读' : '未读' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="是否公告">
          <el-tag :type="currentMessage.is_announcement ? 'warning' : 'info'" size="small">
            {{ currentMessage.is_announcement ? '是' : '否' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="是否过期" v-if="currentMessage.is_announcement">
          <el-tag :type="currentMessage.is_expired ? 'info' : 'success'" size="small">
            {{ currentMessage.is_expired ? '已过期' : '未过期' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="过期时间" v-if="currentMessage.expire_time" :span="2">
          {{ currentMessage.expire_time }}
        </el-descriptions-item>
        <el-descriptions-item label="消息内容" :span="2">
          <div style="white-space: pre-wrap; line-height: 1.6;">
            {{ currentMessage.content }}
          </div>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="statsDialogVisible"
      title="消息统计"
      width="900px"
    >
      <div style="margin-bottom: 20px;">
        <el-form :inline="true" :model="statsForm">
          <el-form-item label="时间范围">
            <el-radio-group v-model="statsForm.period">
              <el-radio value="week">本周</el-radio>
              <el-radio value="month">本月</el-radio>
              <el-radio value="quarter">本季度</el-radio>
              <el-radio value="year">本年</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="消息类型">
            <el-select v-model="statsForm.type" placeholder="全部类型" clearable style="width: 140px;">
              <el-option
                v-for="(name, key) in messageTypeOptions"
                :key="key"
                :label="name"
                :value="key"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchStats">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button type="success" @click="exportStats">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <div v-if="statsData.summary" style="margin-bottom: 20px;">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card shadow="hover">
              <div style="text-align: center;">
                <div style="font-size: 12px; color: #999;">总发送量</div>
                <div style="font-size: 28px; font-weight: bold; color: #409eff; margin-top: 8px;">
                  {{ statsData.summary.total }}
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <div style="text-align: center;">
                <div style="font-size: 12px; color: #999;">已读</div>
                <div style="font-size: 28px; font-weight: bold; color: #67c23a; margin-top: 8px;">
                  {{ statsData.summary.read }}
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <div style="text-align: center;">
                <div style="font-size: 12px; color: #999;">未读</div>
                <div style="font-size: 28px; font-weight: bold; color: #f56c6c; margin-top: 8px;">
                  {{ statsData.summary.unread }}
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <div style="text-align: center;">
                <div style="font-size: 12px; color: #999;">已读率</div>
                <div style="font-size: 28px; font-weight: bold; color: #e6a23c; margin-top: 8px;">
                  {{ statsData.summary.read_rate }}%
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
      
      <div v-if="statsData.type_stats" style="margin-bottom: 20px;">
        <h4 style="margin-bottom: 12px; font-weight: 600;">按类型统计</h4>
        <el-table :data="typeStatsList" size="small">
          <el-table-column prop="key" label="类型" />
          <el-table-column prop="name" label="类型名称" />
          <el-table-column prop="count" label="数量">
            <template #default="scope">
              <el-tag v-if="scope.row.count > 0" type="primary" size="small">
                {{ scope.row.count }}
              </el-tag>
              <span v-else>0</span>
            </template>
          </el-table-column>
          <el-table-column prop="percentage" label="占比" width="150">
            <template #default="scope">
              <el-progress
                :percentage="scope.row.percentage"
                :stroke-width="10"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <div v-if="statsData.daily_data?.length">
        <h4 style="margin-bottom: 12px; font-weight: 600;">每日趋势</h4>
        <el-table :data="statsData.daily_data" size="small">
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="total" label="总发送量" width="100">
            <template #default="scope">
              <el-tag type="primary" size="small">{{ scope.row.total }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="read" label="已读" width="100">
            <template #default="scope">
              <el-tag type="success" size="small">{{ scope.row.read }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="unread" label="未读" width="100">
            <template #default="scope">
              <el-tag type="danger" size="small">{{ scope.row.unread }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <template #footer>
        <el-button @click="statsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, DataLine, Search, Refresh, View } from '@element-plus/icons-vue'
import {
  getMessages,
  getMessageDetail,
  createAnnouncement,
  deleteMessage,
  batchDeleteMessages,
  getMessageStats,
  exportMessageStats,
  getConversations
} from '@/api/messages'

const loading = ref(false)
const submitting = ref(false)
const tableData = ref([])
const total = ref(0)
const selectedIds = ref([])
const activeTab = ref('all')
const dateRange = ref([])

const announcementDialogVisible = ref(false)
const previewDialogVisible = ref(false)
const detailVisible = ref(false)
const statsDialogVisible = ref(false)

const currentMessage = ref(null)
const statsData = ref({})

const messageTypeOptions = {
  system: '系统通知',
  order: '订单消息',
  activity: '活动消息',
  announcement: '公告通知'
}

const announcementSubtypeOptions = {
  system: '系统公告',
  activity: '活动公告',
  promotion: '促销公告',
  update: '更新公告'
}

const recipientTypeOptions = {
  all: '全部用户',
  customer: '普通用户',
  teacher: '老师用户',
  specific: '指定用户'
}

const queryParams = reactive({
  page: 1,
  size: 10,
  keyword: '',
  type: '',
  subtype: '',
  recipient_type: '',
  is_read: null,
  is_announcement: null,
  is_expired: null,
  start_date: '',
  end_date: ''
})

const announcementForm = reactive({
  title: '',
  subtype: 'system',
  recipient_type: 'all',
  content: '',
  expire_time: null
})

const announcementRules = {
  title: [
    { required: true, message: '请输入公告标题', trigger: 'blur' },
    { min: 5, message: '标题不能少于5个字符', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入公告内容', trigger: 'blur' },
    { min: 20, message: '内容不能少于20个字符', trigger: 'blur' }
  ]
}

const statsForm = reactive({
  period: 'week',
  type: ''
})

const typeStatsList = computed(() => {
  if (!statsData.value.type_stats) return []
  const total = Object.values(statsData.value.type_stats).reduce((sum, item) => sum + (item.count || 0), 0)
  return Object.entries(statsData.value.type_stats).map(([key, item]) => ({
    key,
    name: item.name,
    count: item.count,
    percentage: total > 0 ? Math.round((item.count / total) * 100) : 0
  }))
})

const getMessageType = (type) => {
  const typeMap = {
    system: 'info',
    order: 'primary',
    activity: 'warning',
    announcement: 'danger'
  }
  return typeMap[type] || 'info'
}

const disabledDate = (time) => {
  return time.getTime() < Date.now() - 8.64e7
}

const formatDate = (date) => {
  if (!date) return ''
  if (typeof date === 'string') return date
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: queryParams.page,
      size: queryParams.size
    }
    if (queryParams.keyword) params.keyword = queryParams.keyword
    if (queryParams.type) params.type = queryParams.type
    if (queryParams.subtype) params.subtype = queryParams.subtype
    if (queryParams.recipient_type) params.recipient_type = queryParams.recipient_type
    if (queryParams.is_read !== null) params.is_read = queryParams.is_read
    if (queryParams.is_announcement !== null) params.is_announcement = queryParams.is_announcement
    if (queryParams.is_expired !== null) params.is_expired = queryParams.is_expired
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]?.toISOString().split('T')[0]
      params.end_date = dateRange.value[1]?.toISOString().split('T')[0]
    }
    
    let res
    if (activeTab.value === 'conversation') {
      res = await getConversations(params)
    } else {
      res = await getMessages(params)
    }
    
    if (res.code === 0) {
      tableData.value = res.data.list || []
      total.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取数据失败:', e)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const handleTabChange = (tab) => {
  if (tab === 'announcement') {
    queryParams.is_announcement = true
    queryParams.type = 'announcement'
  } else if (tab === 'conversation') {
    queryParams.is_announcement = null
    queryParams.type = ''
  } else {
    queryParams.is_announcement = null
    queryParams.type = ''
  }
  queryParams.page = 1
  fetchData()
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const resetQuery = () => {
  queryParams.page = 1
  queryParams.keyword = ''
  queryParams.type = ''
  queryParams.subtype = ''
  queryParams.recipient_type = ''
  queryParams.is_read = null
  queryParams.is_expired = null
  if (activeTab.value === 'announcement') {
    queryParams.is_announcement = true
    queryParams.type = 'announcement'
  } else {
    queryParams.is_announcement = null
    queryParams.type = ''
  }
  dateRange.value = []
  fetchData()
}

const handleSelectionChange = (selection) => {
  selectedIds.value = selection.map(item => item.id)
}

const openAnnouncementDialog = () => {
  announcementForm.title = ''
  announcementForm.subtype = 'system'
  announcementForm.recipient_type = 'all'
  announcementForm.content = ''
  announcementForm.expire_time = null
  announcementDialogVisible.value = true
}

const previewAnnouncement = () => {
  previewDialogVisible.value = true
}

const submitAnnouncement = async () => {
  if (announcementForm.title.length < 5) {
    ElMessage.warning('公告标题不能少于5个字符')
    return
  }
  if (announcementForm.content.length < 20) {
    ElMessage.warning('公告内容不能少于20个字符')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      '确定要发布此公告吗？发布后将同步推送到小程序端。',
      '确认发布',
      {
        confirmButtonText: '确定发布',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    submitting.value = true
    const data = {
      title: announcementForm.title,
      subtype: announcementForm.subtype,
      recipient_type: announcementForm.recipient_type,
      content: announcementForm.content
    }
    if (announcementForm.expire_time) {
      data.expire_time = new Date(announcementForm.expire_time).toISOString()
    }
    
    const res = await createAnnouncement(data)
    if (res.code === 0) {
      ElMessage.success(`公告发布成功，共发送给 ${res.data.recipient_count} 位用户`)
      announcementDialogVisible.value = false
      fetchData()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('发布公告失败:', e)
      ElMessage.error(e.msg || '发布公告失败')
    }
  } finally {
    submitting.value = false
  }
}

const handleView = async (row) => {
  try {
    const res = await getMessageDetail(row.id)
    if (res.code === 0) {
      currentMessage.value = res.data
      detailVisible.value = true
    }
  } catch (e) {
    currentMessage.value = row
    detailVisible.value = true
  }
}

const handleDelete = async (row) => {
  const isAnnouncement = row.is_announcement
  const isExpired = row.is_expired
  
  let confirmMsg = '确定要删除这条消息吗？'
  if (isAnnouncement && !isExpired) {
    confirmMsg = '该公告尚未过期，删除后将无法向用户展示。确定要删除吗？此操作不可恢复！'
  }
  
  try {
    await ElMessageBox.confirm(confirmMsg, '确认删除', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: isAnnouncement && !isExpired ? 'warning' : 'info'
    })
    
    if (isAnnouncement && !isExpired) {
      await ElMessageBox.confirm(
        '二次确认：该公告尚未过期，删除后所有用户将无法再看到这条公告。确定要继续删除吗？',
        '二次确认',
        {
          confirmButtonText: '确认删除',
          cancelButtonText: '取消',
          type: 'error'
        }
      )
    }
    
    const res = await deleteMessage(row.id)
    if (res.code === 0) {
      ElMessage.success('删除成功')
      fetchData()
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleBatchDelete = async () => {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请选择要删除的消息')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.length} 条消息吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const res = await batchDeleteMessages({ message_ids: selectedIds.value })
    if (res.code === 0) {
      ElMessage.success(`已删除 ${res.data.deleted_count} 条消息`)
      fetchData()
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

const openStatsDialog = () => {
  statsDialogVisible.value = true
  fetchStats()
}

const fetchStats = async () => {
  try {
    const params = {
      period: statsForm.period
    }
    if (statsForm.type) params.type = statsForm.type
    
    const res = await getMessageStats(params)
    if (res.code === 0) {
      statsData.value = res.data
    }
  } catch (e) {
    console.error('获取统计数据失败:', e)
    ElMessage.error('获取统计数据失败')
  }
}

const exportStats = async () => {
  try {
    const params = {
      period: statsForm.period
    }
    if (statsForm.type) params.type = statsForm.type
    
    const res = await exportMessageStats(params)
    if (res.code === 0) {
      const { csv_content, filename } = res.data
      const blob = new Blob(['\ufeff' + csv_content], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = filename
      link.click()
      ElMessage.success('导出成功')
    }
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.page-card {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
  align-items: center;
}

.table-wrapper {
  margin-bottom: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.operation-btns {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
</style>
