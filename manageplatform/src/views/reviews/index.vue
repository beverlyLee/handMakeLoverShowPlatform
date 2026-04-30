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
        style="width: 200px;"
        @keyup.enter="handleSearch"
      />
      <el-select
        v-model="queryParams.rating"
        placeholder="评分筛选"
        clearable
        style="width: 140px;"
      >
        <el-option label="1星" :value="1" />
        <el-option label="2星" :value="2" />
        <el-option label="3星" :value="3" />
        <el-option label="4星" :value="4" />
        <el-option label="5星" :value="5" />
      </el-select>
      <el-select
        v-model="queryParams.is_reported"
        placeholder="是否被举报"
        clearable
        style="width: 140px;"
      >
        <el-option label="已举报" :value="true" />
        <el-option label="未举报" :value="false" />
      </el-select>
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
        <el-table-column label="用户" width="120">
          <template #default="scope">
            <div style="display: flex; align-items: center; gap: 8px;">
              <el-avatar :size="32" :src="scope.row.user_avatar">
                <el-icon :size="16"><User /></el-icon>
              </el-avatar>
              <span>{{ scope.row.user_nickname }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="评分" width="120">
          <template #default="scope">
            <el-rate
              v-model="scope.row.rating"
              disabled
              :max="5"
              size="small"
            />
          </template>
        </el-table-column>
        <el-table-column prop="content" label="评价内容" min-width="200" show-overflow-tooltip />
        <el-table-column label="评价图片" width="150">
          <template #default="scope">
            <div v-if="scope.row.images?.length">
              <el-image
                v-for="(img, index) in scope.row.images.slice(0, 3)"
                :key="index"
                :src="img"
                fit="cover"
                :preview-src-list="scope.row.images"
                style="width: 40px; height: 40px; margin-right: 4px; border-radius: 4px;"
              />
              <span v-if="scope.row.images.length > 3" style="font-size: 12px; color: #999;">
                +{{ scope.row.images.length - 3 }}
              </span>
            </div>
            <span v-else style="color: #999;">无图</span>
          </template>
        </el-table-column>
        <el-table-column label="是否被举报" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_reported ? 'danger' : 'info'" size="small">
              {{ scope.row.is_reported ? '已举报' : '正常' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="是否已读" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.is_read ? 'success' : 'warning'" size="small">
              {{ scope.row.is_read ? '已读' : '未读' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="评价时间" width="160" />
        <el-table-column label="操作" fixed="right" width="200">
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
                标记已读
              </el-button>
              <el-button
                v-if="scope.row.is_reported"
                type="danger"
                link
                @click="handleHandleReport(scope.row)"
              >
                处理举报
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
    
    <el-dialog v-model="detailVisible" title="评价详情" width="600px">
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
          <el-rate v-model="currentReview.rating" disabled :max="5" size="small" />
        </el-descriptions-item>
        <el-descriptions-item label="评价时间">{{ currentReview.create_time }}</el-descriptions-item>
        <el-descriptions-item label="评价内容" :span="2">
          {{ currentReview.content }}
        </el-descriptions-item>
        <el-descriptions-item label="是否被举报" :span="2">
          <el-tag :type="currentReview.is_reported ? 'danger' : 'info'" size="small">
            {{ currentReview.is_reported ? '已举报' : '正常' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
      
      <div v-if="currentReview?.images?.length" style="margin-top: 20px;">
        <h4 style="margin-bottom: 12px; font-weight: 600;">评价图片</h4>
        <el-image
          v-for="(img, index) in currentReview.images"
          :key="index"
          :src="img"
          fit="cover"
          :preview-src-list="currentReview.images"
          style="width: 100px; height: 100px; margin-right: 10px; border-radius: 4px; cursor: pointer;"
        />
      </div>
      
      <div v-if="currentReview?.reply_content" style="margin-top: 20px;">
        <h4 style="margin-bottom: 12px; font-weight: 600;">老师回复</h4>
        <el-card shadow="never" style="background: #fafafa;">
          {{ currentReview.reply_content }}
          <div style="text-align: right; margin-top: 8px; color: #999; font-size: 12px;">
            {{ currentReview.reply_time }}
          </div>
        </el-card>
      </div>
      
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleReply">回复评价</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const detailVisible = ref(false)
const currentReview = ref(null)

const queryParams = reactive({
  page: 1,
  size: 10,
  keyword: '',
  rating: null,
  is_reported: null
})

const fetchData = async () => {
  loading.value = true
  try {
    tableData.value = [
      {
        id: 1,
        user_id: 1,
        user_nickname: '手作爱好者',
        user_avatar: '',
        rating: 5,
        content: '非常棒的手作课程！老师很有耐心，讲解非常细致，我这个零基础的也学会了，成品非常漂亮！强烈推荐给想要学习手工的朋友们。',
        images: [],
        is_reported: false,
        is_read: true,
        create_time: '2024-04-28 15:30:00',
        reply_content: '感谢您的好评！期待下次再见到您~',
        reply_time: '2024-04-28 16:00:00'
      },
      {
        id: 2,
        user_id: 3,
        user_nickname: 'DIY达人',
        user_avatar: '',
        rating: 4,
        content: '整体还不错，就是材料包有点少，希望下次能多配一些。老师教得还是很好的。',
        images: [],
        is_reported: false,
        is_read: false,
        create_time: '2024-04-27 10:15:00'
      },
      {
        id: 3,
        user_id: 6,
        user_nickname: '纸艺小匠',
        user_avatar: '',
        rating: 5,
        content: '超级喜欢这个课程！成品太漂亮了，已经送给朋友当礼物了，朋友很喜欢。老师也很专业，下次还要报名其他课程！',
        images: [],
        is_reported: true,
        is_read: false,
        create_time: '2024-04-26 14:20:00'
      }
    ]
    total.value = 3
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
  queryParams.is_reported = null
  fetchData()
}

const handleView = (row) => {
  currentReview.value = row
  detailVisible.value = true
}

const handleMarkRead = (row) => {
  row.is_read = true
  ElMessage.success('已标记为已读')
}

const handleHandleReport = (row) => {
  ElMessage.info('处理举报功能开发中')
}

const handleReply = () => {
  ElMessage.info('回复评价功能开发中')
}

onMounted(() => {
  fetchData()
})
</script>
