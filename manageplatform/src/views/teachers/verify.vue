<template>
  <div class="page-card">
    <div class="page-header">
      <span class="page-title">老师入驻审核</span>
    </div>
    
    <div class="table-wrapper">
      <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="user_info" label="用户信息" width="180">
          <template #default="scope">
            <div class="user-info-cell">
              <el-avatar :size="40" :src="scope.row.user_info?.avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <div class="user-detail">
                <div class="nickname">{{ scope.row.user_info?.nickname || '未知' }}</div>
                <div class="phone">{{ scope.row.user_info?.phone || '-' }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="real_name" label="真实姓名" width="100" />
        <el-table-column prop="specialties" label="擅长领域" min-width="150">
          <template #default="scope">
            <el-tag v-for="(s, i) in scope.row.specialties" :key="i" size="small" style="margin-right: 4px; margin-bottom: 4px;">
              {{ s }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="work_photos" label="案例图片" width="100">
          <template #default="scope">
            <span v-if="scope.row.work_photos && scope.row.work_photos.length > 0">
              {{ scope.row.work_photos.length }}张
            </span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="verify_status" label="审核状态" width="100">
          <template #default="scope">
            <el-tag type="warning">待审核</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="申请时间" width="180" />
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="scope">
            <div class="operation-btns">
              <el-button type="primary" link @click="handleView(scope.row)">
                查看
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
    
    <el-dialog v-model="detailVisible" :title="'审核详情 - ' + (currentTeacher?.real_name || '未知')" width="900px" :close-on-click-modal="false">
      <div v-if="currentTeacher">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="申请ID">{{ currentTeacher.id }}</el-descriptions-item>
          <el-descriptions-item label="真实姓名">{{ currentTeacher.real_name }}</el-descriptions-item>
          <el-descriptions-item label="身份证号">{{ currentTeacher.id_card || '-' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ currentTeacher.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="工作年限">{{ currentTeacher.experience_years || 0 }}年</el-descriptions-item>
          <el-descriptions-item label="工作室名称">{{ currentTeacher.studio_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="工作室地址">{{ currentTeacher.studio_address || '-' }}</el-descriptions-item>
          <el-descriptions-item label="申请时间">{{ currentTeacher.create_time }}</el-descriptions-item>
          <el-descriptions-item label="个人简介" :span="2">
            {{ currentTeacher.intro || currentTeacher.bio || '暂无简介' }}
          </el-descriptions-item>
          <el-descriptions-item label="擅长领域" :span="2">
            <el-tag v-for="(s, i) in currentTeacher.specialties" :key="i" style="margin-right: 8px;">
              {{ s }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="section-title" style="margin-top: 20px; margin-bottom: 16px;">
          <el-icon><Picture /></el-icon> 案例作品（共{{ currentTeacher.work_photos?.length || 0 }}张）
        </div>
        
        <div class="work-photos-grid" v-if="currentTeacher.work_photos && currentTeacher.work_photos.length > 0">
          <el-image
            v-for="(img, index) in currentTeacher.work_photos"
            :key="index"
            :src="img"
            :preview-src-list="currentTeacher.work_photos"
            :initial-index="index"
            fit="cover"
            class="work-photo-item"
          >
            <template #error>
              <div class="image-error">
                <el-icon :size="32"><PictureFilled /></el-icon>
                <span>加载失败</span>
              </div>
            </template>
          </el-image>
        </div>
        <el-empty v-else description="暂无案例图片" />
        
        <div class="section-title" style="margin-top: 20px; margin-bottom: 16px;">
          <el-icon><OfficeBuilding /></el-icon> 工作室图片
        </div>
        
        <div class="work-photos-grid" v-if="currentTeacher.studio_images && currentTeacher.studio_images.length > 0">
          <el-image
            v-for="(img, index) in currentTeacher.studio_images"
            :key="index"
            :src="img"
            :preview-src-list="currentTeacher.studio_images"
            :initial-index="index"
            fit="cover"
            class="work-photo-item"
          >
            <template #error>
              <div class="image-error">
                <el-icon :size="32"><PictureFilled /></el-icon>
                <span>加载失败</span>
              </div>
            </template>
          </el-image>
        </div>
        <el-empty v-else description="暂无工作室图片" />
        
        <div class="section-title" style="margin-top: 20px; margin-bottom: 16px;">
          <el-icon><Medal /></el-icon> 资质证书
        </div>
        
        <div class="work-photos-grid" v-if="currentTeacher.certifications && currentTeacher.certifications.length > 0">
          <el-image
            v-for="(img, index) in currentTeacher.certifications"
            :key="index"
            :src="img"
            :preview-src-list="currentTeacher.certifications"
            :initial-index="index"
            fit="cover"
            class="work-photo-item"
          >
            <template #error>
              <div class="image-error">
                <el-icon :size="32"><PictureFilled /></el-icon>
                <span>加载失败</span>
              </div>
            </template>
          </el-image>
        </div>
        <el-empty v-else description="暂无资质证书" />
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
import { getPendingTeachers, verifyTeacher } from '@/api/users'

const loading = ref(false)
const verifyLoading = ref(false)
const tableData = ref([])
const total = ref(0)
const detailVisible = ref(false)
const rejectVisible = ref(false)
const currentTeacher = ref(null)
const rejectFormRef = ref(null)

const queryParams = reactive({
  page: 1,
  size: 10
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
    const res = await getPendingTeachers({
      page: queryParams.page,
      size: queryParams.size
    })
    if (res.code === 0) {
      tableData.value = res.data.list || []
      total.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取待审核老师列表失败:', e)
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

const handleView = (row) => {
  currentTeacher.value = { ...row }
  detailVisible.value = true
}

const handleApprove = async () => {
  if (!currentTeacher.value) return
  
  try {
    await ElMessageBox.confirm('确定要通过该老师的入驻申请吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    verifyLoading.value = true
    const res = await verifyTeacher(currentTeacher.value.id, {
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
  if (!rejectFormRef.value || !currentTeacher.value) return
  
  await rejectFormRef.value.validate(async (valid) => {
    if (valid) {
      verifyLoading.value = true
      try {
        const res = await verifyTeacher(currentTeacher.value.id, {
          action: 'reject',
          reason: rejectForm.reason
        })
        
        if (res.code === 0) {
          ElMessage.success('已拒绝该申请')
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
.user-info-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-detail {
  display: flex;
  flex-direction: column;
}

.nickname {
  font-weight: 500;
  color: #333;
}

.phone {
  font-size: 12px;
  color: #999;
}

.text-gray {
  color: #999;
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

.work-photos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
}

.work-photo-item {
  width: 100%;
  height: 150px;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid #eee;
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: #f5f7fa;
  color: #999;
  font-size: 12px;
  gap: 8px;
}
</style>