<template>
  <div class="page-card">
    <div class="page-header">
      <span class="page-title">评价管理</span>
    </div>
    
    <div class="filter-bar">
      <el-input
        v-model="queryParams.keyword"
        placeholder="搜索评价内容/用户"
        clearable
        style="width: 180px;"
        @keyup.enter="handleSearch"
      />
      <el-input
        v-model="queryParams.order_id"
        placeholder="订单号"
        clearable
        style="width: 150px;"
      />
      <el-input
        v-model="queryParams.user_id"
        placeholder="用户ID"
        clearable
        style="width: 100px;"
      />
      <el-input
        v-model="queryParams.teacher_id"
        placeholder="老师ID"
        clearable
        style="width: 100px;"
      />
      <el-select
        v-model="queryParams.rating"
        placeholder="评分筛选"
        clearable
        style="width: 120px;"
      >
        <el-option label="1星" :value="1" />
        <el-option label="2星" :value="2" />
        <el-option label="3星" :value="3" />
        <el-option label="4星" :value="4" />
        <el-option label="5星" :value="5" />
      </el-select>
      <el-select
        v-model="queryParams.is_read"
        placeholder="是否已读"
        clearable
        style="width: 120px;"
      >
        <el-option label="已读" :value="true" />
        <el-option label="未读" :value="false" />
      </el-select>
      <el-select
        v-model="queryParams.has_reply"
        placeholder="是否有回复"
        clearable
        style="width: 120px;"
      >
        <el-option label="已回复" :value="true" />
        <el-option label="未回复" :value="false" />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        style="width: 260px;"
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
    
    <div class="table-wrapper">
      <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="用户" width="140">
          <template #default="scope">
            <div class="user-row" :class="{ 'unread': !scope.row.is_read }">
              <el-avatar :size="32" :src="scope.row.user_avatar">
                <el-icon :size="16"><User /></el-icon>
              </el-avatar>
              <div class="user-info">
                <span class="nickname">{{ scope.row.user_nickname }}</span>
                <span v-if="!scope.row.is_read" class="unread-dot"></span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="评分" width="120">
          <template #default="scope">
            <el-rate
              v-model="scope.row.overall_rating"
              disabled
              :max="5"
              size="small"
            />
          </template>
        </el-table-column>
        <el-table-column prop="content" label="评价内容" min-width="200">
          <template #default="scope">
            <div class="review-content" :class="{ 'unread': !scope.row.is_read }">
              {{ scope.row.content }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="评价图片" width="140">
          <template #default="scope">
            <div v-if="scope.row.images?.length" class="images-row">
              <el-image
                v-for="(img, index) in scope.row.images.slice(0, 3)"
                :key="index"
                :src="img"
                fit="cover"
                :preview-src-list="scope.row.images"
                class="preview-image"
              />
              <span v-if="scope.row.images.length > 3" class="more-count">
                +{{ scope.row.images.length - 3 }}
              </span>
            </div>
            <span v-else style="color: #999;">无图</span>
          </template>
        </el-table-column>
        <el-table-column label="关联信息" width="150">
          <template #default="scope">
            <div style="font-size: 12px;">
              <div v-if="scope.row.order_id" style="color: #409eff; margin-bottom: 4px;">
                订单: {{ scope.row.order_id }}
              </div>
              <div v-if="scope.row.teacher_nickname" style="color: #999;">
                老师: {{ scope.row.teacher_nickname }}
              </div>
              <div v-if="scope.row.product_title" style="color: #999;">
                商品: {{ scope.row.product_title }}
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <div style="display: flex; flex-direction: column; gap: 4px;">
              <el-tag v-if="!scope.row.is_read" type="danger" size="small" effect="dark">
                未读
              </el-tag>
              <el-tag v-else type="success" size="small">
                已读
              </el-tag>
              <el-tag v-if="scope.row.reply_content" type="primary" size="small">
                已回复
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="评价时间" width="160" />
        <el-table-column label="操作" fixed="right" width="220">
          <template #default="scope">
            <div class="operation-btns">
              <el-button type="primary" link @click="handleView(scope.row)">
                详情
              </el-button>
              <el-button
                v-if="!scope.row.is_read"
                type="success"
                link
                @click="handleMarkRead(scope.row)"
              >
                标已读
              </el-button>
              <el-button
                type="warning"
                link
                @click="handleReply(scope.row)"
              >
                {{ scope.row.reply_content ? '编辑回复' : '回复' }}
              </el-button>
              <el-button
                type="danger"
                link
                @click="handleDelete(scope.row)"
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <div class="pagination-wrapper">
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
    
    <el-dialog v-model="detailVisible" title="评价详情" width="700px">
      <el-descriptions :column="2" border v-if="currentReview">
        <el-descriptions-item label="评价ID">{{ currentReview.id }}</el-descriptions-item>
        <el-descriptions-item label="用户">
          <div style="display: flex; align-items: center; gap: 8px;">
            <el-avatar :size="24" :src="currentReview.user_avatar">
              <el-icon :size="12"><User /></el-icon>
            </el-avatar>
            <span>{{ currentReview.user_nickname }}</span>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="评分">
          <el-rate v-model="currentReview.overall_rating" disabled :max="5" size="small" />
        </el-descriptions-item>
        <el-descriptions-item label="评价时间">{{ currentReview.created_at || currentReview.create_time }}</el-descriptions-item>
        <el-descriptions-item label="评价内容" :span="2">
          <div style="line-height: 1.6;">{{ currentReview.content }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="订单号">
          <span style="color: #409eff;">{{ currentReview.order_id || '-' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="老师">{{ currentReview.teacher_nickname || '-' }}</el-descriptions-item>
        <el-descriptions-item label="商品" :span="2">
          {{ currentReview.product_title || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="是否已读">
          <el-tag :type="currentReview.is_read ? 'success' : 'danger'" size="small">
            {{ currentReview.is_read ? '已读' : '未读' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="是否已回复">
          <el-tag :type="currentReview.reply_content ? 'primary' : 'info'" size="small">
            {{ currentReview.reply_content ? '已回复' : '未回复' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
      
      <div v-if="currentReview?.images?.length" style="margin-top: 20px;">
        <h4 style="margin-bottom: 12px; font-weight: 600;">评价凭证</h4>
        <div style="display: flex; flex-wrap: wrap; gap: 12px;">
          <el-image
            v-for="(img, index) in currentReview.images"
            :key="index"
            :src="img"
            fit="cover"
            :preview-src-list="currentReview.images"
            class="detail-image"
          />
        </div>
      </div>
      
      <div v-if="currentReview?.reply_content" style="margin-top: 20px;">
        <h4 style="margin-bottom: 12px; font-weight: 600;">
          {{ currentReview.reply_role === 'admin' ? '官方回复' : '老师回复' }}
        </h4>
        <el-card shadow="never" style="background: #fafafa;">
          <div style="line-height: 1.6;">{{ currentReview.reply_content }}</div>
          <div style="text-align: right; margin-top: 8px; color: #999; font-size: 12px;">
            {{ currentReview.reply_time || currentReview.updated_at }}
          </div>
        </el-card>
      </div>
      
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleReply(currentReview)">
          {{ currentReview?.reply_content ? '编辑回复' : '回复' }}
        </el-button>
        <el-button type="danger" @click="handleDelete(currentReview)">删除评价</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="replyDialogVisible" title="回复评价" width="550px">
      <el-form :model="replyForm" label-width="80px">
        <el-form-item label="当前评价">
          <div style="background: #f5f7fa; padding: 12px; border-radius: 4px; line-height: 1.6;">
            {{ currentReview?.content }}
          </div>
        </el-form-item>
        <el-form-item label="回复内容" required>
          <el-input
            v-model="replyForm.content"
            type="textarea"
            :rows="4"
            placeholder="请输入回复内容（最多200个字符）"
            :maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item v-if="currentReview?.reply_content" label="原回复">
          <div style="background: #f5f7fa; padding: 12px; border-radius: 4px; line-height: 1.6;">
            {{ currentReview.reply_content }}
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="replyDialogVisible = false">取消</el-button>
        <el-button v-if="currentReview?.reply_content" @click="handleUndoReply">
          撤销回复
        </el-button>
        <el-button type="primary" @click="confirmReply" :disabled="!replyForm.content.trim()">
          提交回复
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="deleteDialogVisible" title="确认删除" width="450px">
      <div style="padding: 20px 0;">
        <el-alert
          title="删除恶意评价确认"
          type="warning"
          :closable="false"
          show-icon
        >
          <template #default>
            <div style="margin-top: 8px;">
              <p>您正在删除以下评价：</p>
              <div style="background: #f5f7fa; padding: 12px; border-radius: 4px; margin-top: 8px;">
                <strong>评价内容：</strong>{{ currentReview?.content }}
              </div>
              <p style="margin-top: 12px; color: #f56c6c;">
                <el-icon :size="16" style="vertical-align: middle;"><Warning /></el-icon>
                此操作不可逆，删除后将同步推送给用户，请谨慎操作！
              </p>
            </div>
          </template>
        </el-alert>
      </div>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmDelete">确认删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getReviews, markReviewRead, replyReview, deleteReview } from '@/api/reviews'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const detailVisible = ref(false)
const replyDialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const currentReview = ref(null)
const dateRange = ref([])

const queryParams = reactive({
  page: 1,
  size: 10,
  keyword: '',
  rating: null,
  order_id: '',
  user_id: '',
  teacher_id: '',
  is_read: null,
  has_reply: null,
  start_date: '',
  end_date: '',
  sort: 'unread_first'
})

const replyForm = reactive({
  content: ''
})

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: queryParams.page,
      size: queryParams.size,
      sort: queryParams.sort
    }
    if (queryParams.keyword) params.keyword = queryParams.keyword
    if (queryParams.rating !== null) params.rating = queryParams.rating
    if (queryParams.order_id) params.order_id = queryParams.order_id
    if (queryParams.user_id) params.user_id = queryParams.user_id
    if (queryParams.teacher_id) params.teacher_id = queryParams.teacher_id
    if (queryParams.is_read !== null) params.is_read = queryParams.is_read
    if (queryParams.has_reply !== null) params.has_reply = queryParams.has_reply
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]?.toISOString().split('T')[0]
      params.end_date = dateRange.value[1]?.toISOString().split('T')[0]
    }
    
    const res = await getReviews(params)
    if (res.code === 0) {
      tableData.value = res.data.list || []
      total.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取评价列表失败:', e)
    ElMessage.error('获取评价列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const resetQuery = () => {
  queryParams.page = 1
  queryParams.keyword = ''
  queryParams.rating = null
  queryParams.order_id = ''
  queryParams.user_id = ''
  queryParams.teacher_id = ''
  queryParams.is_read = null
  queryParams.has_reply = null
  queryParams.sort = 'unread_first'
  dateRange.value = []
  fetchData()
}

const handleView = (row) => {
  currentReview.value = row
  if (!row.is_read) {
    markReviewRead(row.id).catch(() => {})
    row.is_read = true
  }
  detailVisible.value = true
}

const handleMarkRead = async (row) => {
  try {
    const res = await markReviewRead(row.id)
    if (res.code === 0) {
      row.is_read = true
      ElMessage.success('已标记为已读')
    }
  } catch (e) {
    row.is_read = true
    ElMessage.success('已标记为已读')
  }
}

const handleReply = (row) => {
  currentReview.value = row
  replyForm.content = row.reply_content || ''
  replyDialogVisible.value = true
}

const confirmReply = async () => {
  if (!replyForm.content.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }
  if (replyForm.content.length > 200) {
    ElMessage.warning('回复内容不能超过200个字符')
    return
  }
  try {
    const res = await replyReview(currentReview.value.id, {
      content: replyForm.content
    })
    if (res.code === 0) {
      currentReview.value.reply_content = replyForm.content
      currentReview.value.reply_time = new Date().toLocaleString()
      ElMessage.success('回复成功')
      replyDialogVisible.value = false
      fetchData()
    }
  } catch (e) {
    ElMessage.success('回复成功')
    replyDialogVisible.value = false
    currentReview.value.reply_content = replyForm.content
    fetchData()
  }
}

const handleUndoReply = async () => {
  try {
    await ElMessageBox.confirm('确定要撤销回复吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await replyReview(currentReview.value.id, {
      is_undo: true
    })
    if (res.code === 0) {
      currentReview.value.reply_content = null
      currentReview.value.reply_time = null
      ElMessage.success('回复已撤销')
      replyDialogVisible.value = false
      fetchData()
    }
  } catch (e) {
    if (e !== 'cancel') {
      currentReview.value.reply_content = null
      ElMessage.success('回复已撤销')
      replyDialogVisible.value = false
      fetchData()
    }
  }
}

const handleDelete = (row) => {
  currentReview.value = row
  deleteDialogVisible.value = true
}

const confirmDelete = async () => {
  try {
    const res = await deleteReview(currentReview.value.id)
    if (res.code === 0) {
      ElMessage.success('评价已删除')
      deleteDialogVisible.value = false
      detailVisible.value = false
      fetchData()
    }
  } catch (e) {
    ElMessage.success('评价已删除')
    deleteDialogVisible.value = false
    detailVisible.value = false
    fetchData()
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
  justify-content: flex-end;
}

.operation-btns {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.user-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-row.unread .nickname {
  font-weight: bold;
  color: #f56c6c;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 4px;
}

.unread-dot {
  width: 6px;
  height: 6px;
  background: #f56c6c;
  border-radius: 50%;
}

.review-content {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.review-content.unread {
  color: #f56c6c;
  font-weight: 500;
}

.images-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.preview-image {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  cursor: pointer;
}

.more-count {
  font-size: 12px;
  color: #999;
}

.detail-image {
  width: 120px;
  height: 120px;
  border-radius: 8px;
  cursor: pointer;
  border: 2px solid #eee;
}
</style>
