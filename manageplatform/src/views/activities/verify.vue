<template>
  <div class="page-card">
    <div class="page-header">
      <span class="page-title">活动审核</span>
    </div>
    
    <div class="filter-bar">
      <el-input
        v-model="queryParams.keyword"
        placeholder="搜索活动名称"
        clearable
        style="width: 200px;"
        @keyup.enter="handleSearch"
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
        <el-table-column prop="id" label="活动ID" width="80" />
        <el-table-column prop="cover_image" label="封面" width="100">
          <template #default="scope">
            <el-image
              :src="scope.row.cover_image"
              :preview-src-list="[scope.row.cover_image]"
              fit="cover"
              style="width: 60px; height: 60px; border-radius: 4px;"
            >
              <template #error>
                <div class="image-slot">
                  <el-icon :size="24"><Picture /></el-icon>
                </div>
              </template>
            </el-image>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="活动名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="activity_type" label="类型" width="100" />
        <el-table-column prop="craft_type" label="种类" width="100" />
        <el-table-column prop="teacher_name" label="发布老师" width="120" />
        <el-table-column prop="price" label="费用" width="100">
          <template #default="scope">
            <span v-if="scope.row.price > 0" style="color: #ff6b35; font-weight: bold;">
              ¥{{ scope.row.price?.toFixed(2) }}
            </span>
            <span v-else style="color: #67c23a;">免费</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="180" />
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="scope">
            <div class="operation-btns">
              <el-button type="primary" link @click="handleView(scope.row)">
                审核
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
        :page-sizes="[10, 20, 50]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchData"
        @current-change="fetchData"
      />
    </div>
    
    <el-dialog v-model="detailVisible" :title="'活动审核详情'" width="900px" :close-on-click-modal="false">
      <div v-if="currentActivity">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="活动ID">{{ currentActivity.id }}</el-descriptions-item>
          <el-descriptions-item label="活动名称">{{ currentActivity.title }}</el-descriptions-item>
          <el-descriptions-item label="活动类型">{{ currentActivity.activity_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="手工种类">{{ currentActivity.craft_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="发布老师">{{ currentActivity.teacher_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="费用">
            <span v-if="currentActivity.price > 0">¥{{ currentActivity.price?.toFixed(2) }}</span>
            <span v-else style="color: #67c23a;">免费</span>
          </el-descriptions-item>
          <el-descriptions-item label="活动地点">{{ currentActivity.location || currentActivity.city || '-' }}</el-descriptions-item>
          <el-descriptions-item label="详细地址">{{ currentActivity.address || '-' }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ currentActivity.start_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ currentActivity.end_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="报名截止">{{ currentActivity.registration_deadline || '-' }}</el-descriptions-item>
          <el-descriptions-item label="最大人数">{{ currentActivity.max_participants || '不限' }}</el-descriptions-item>
          <el-descriptions-item label="活动描述" :span="2">
            <div class="description-text">{{ currentActivity.description || '暂无描述' }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="活动流程" :span="2">
            <div class="description-text">{{ currentActivity.process || '暂无流程说明' }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="报名方式" :span="2">
            <div class="description-text">{{ currentActivity.registration_method || '-' }}</div>
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="section-title" style="margin-top: 20px; margin-bottom: 16px;">
          <el-icon><Picture /></el-icon> 活动图片（共{{ currentActivity.images?.length || 0 }}张）
        </div>
        
        <div v-if="currentActivity.images && currentActivity.images.length > 0">
          <div class="carousel-wrapper">
            <el-carousel :interval="5000" arrow="always" height="400px">
              <el-carousel-item v-for="(img, index) in currentActivity.images" :key="index">
                <div class="carousel-img-wrapper">
                  <el-image
                    :src="img"
                    :preview-src-list="currentActivity.images"
                    :initial-index="index"
                    fit="contain"
                    class="carousel-img"
                  >
                    <template #error>
                      <div class="image-error">
                        <el-icon :size="48"><PictureFilled /></el-icon>
                        <span>图片加载失败</span>
                      </div>
                    </template>
                  </el-image>
                </div>
              </el-carousel-item>
            </el-carousel>
            <div class="image-indicators">
              <div
                v-for="(img, index) in currentActivity.images"
                :key="index"
                class="image-thumb"
                :class="{ active: activeImageIndex === index }"
                @click="activeImageIndex = index"
              >
                <el-image :src="img" fit="cover" class="thumb-img" />
              </div>
            </div>
          </div>
        </div>
        <el-empty v-else description="该活动暂无图片" />
      </div>
      
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="danger" @click="handleReject" :disabled="verifyLoading">
          <el-icon><Close /></el-icon> 拒绝
        </el-button>
        <el-button type="success" @click="handleApprove" :loading="verifyLoading">
          <el-icon><Check /></el-icon> 通过
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="rejectVisible" title="拒绝理由" width="500px">
      <el-form :model="rejectForm" :rules="rejectRules" ref="rejectFormRef" label-width="0">
        <el-form-item prop="reason">
          <el-input
            v-model="rejectForm.reason"
            type="textarea"
            :rows="4"
            placeholder="请输入拒绝理由（至少10个字）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" @click="submitReject" :loading="verifyLoading">确认拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPendingReviewActivities, reviewActivity } from '@/api/activities'
import { processActivityList, processActivityImages } from '@/utils/image'

const loading = ref(false)
const verifyLoading = ref(false)
const tableData = ref([])
const total = ref(0)
const detailVisible = ref(false)
const rejectVisible = ref(false)
const currentActivity = ref(null)
const rejectFormRef = ref(null)
const activeImageIndex = ref(0)

const queryParams = reactive({
  page: 1,
  size: 10,
  keyword: ''
})

const rejectForm = reactive({
  reason: ''
})

const rejectRules = {
  reason: [
    { required: true, message: '请输入拒绝理由', trigger: 'blur' },
    { min: 10, message: '拒绝理由不能少于10个字', trigger: 'blur' }
  ]
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: queryParams.page,
      size: queryParams.size
    }
    if (queryParams.keyword) params.keyword = queryParams.keyword
    
    const res = await getPendingReviewActivities(params)
    if (res.code === 0) {
      const rawList = res.data.list || []
      tableData.value = processActivityList(rawList)
      total.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取待审核活动列表失败:', e)
    ElMessage.error('获取列表失败')
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
  fetchData()
}

const handleView = (row) => {
  currentActivity.value = processActivityImages({ ...row })
  activeImageIndex.value = 0
  detailVisible.value = true
}

const handleApprove = async () => {
  if (!currentActivity.value) return
  
  try {
    await ElMessageBox.confirm('确定要通过该活动的审核吗？通过后活动将可被用户报名。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    verifyLoading.value = true
    const res = await reviewActivity(currentActivity.value.id, {
      action: 'approve'
    })
    
    if (res.code === 0) {
      ElMessage.success('审核通过')
      detailVisible.value = false
      fetchData()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('审核失败:', e)
      ElMessage.error(e.response?.data?.msg || '审核失败')
    }
  } finally {
    verifyLoading.value = false
  }
}

const handleReject = () => {
  rejectForm.reason = ''
  rejectVisible.value = true
}

const submitReject = async () => {
  if (!rejectFormRef.value || !currentActivity.value) return
  
  await rejectFormRef.value.validate(async (valid) => {
    if (valid) {
      verifyLoading.value = true
      try {
        const res = await reviewActivity(currentActivity.value.id, {
          action: 'reject',
          reason: rejectForm.reason
        })
        
        if (res.code === 0) {
          ElMessage.success('已拒绝该活动')
          rejectVisible.value = false
          detailVisible.value = false
          fetchData()
        }
      } catch (e) {
        console.error('拒绝失败:', e)
        ElMessage.error(e.response?.data?.msg || '操作失败')
      } finally {
        verifyLoading.value = false
      }
    }
  })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.image-slot {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 60px;
  height: 60px;
  background: #f5f7fa;
  color: #909399;
  border-radius: 4px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.description-text {
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.6;
}

.carousel-wrapper {
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
}

.carousel-img-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  background: #f5f7fa;
}

.carousel-img {
  width: 100%;
  height: 100%;
}

.image-indicators {
  display: flex;
  gap: 8px;
  padding: 16px;
  background: #f5f7fa;
  overflow-x: auto;
}

.image-thumb {
  width: 80px;
  height: 80px;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  flex-shrink: 0;
}

.image-thumb.active {
  border-color: #409eff;
}

.thumb-img {
  width: 100%;
  height: 100%;
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: #f5f7fa;
  color: #999;
  font-size: 14px;
  gap: 12px;
}
</style>
