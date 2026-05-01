<template>
  <div class="page-card">
    <div class="page-header">
      <span class="page-title">活动管理</span>
      <el-button type="primary" @click="handleAddOfficial">
        <el-icon><Plus /></el-icon>
        官方发布活动
      </el-button>
    </div>
    
    <div class="filter-bar">
      <el-input
        v-model="queryParams.keyword"
        placeholder="搜索活动名称"
        clearable
        style="width: 200px;"
        @keyup.enter="handleSearch"
      />
      <el-select
        v-model="queryParams.activity_type"
        placeholder="活动类型"
        clearable
        style="width: 140px;"
      >
        <el-option label="线下课程" value="线下课程" />
        <el-option label="线上直播" value="线上直播" />
        <el-option label="线下体验" value="线下体验" />
        <el-option label="比赛" value="比赛" />
        <el-option label="展览" value="展览" />
        <el-option label="其他" value="其他" />
      </el-select>
      <el-select
        v-model="queryParams.craft_type"
        placeholder="手工种类"
        clearable
        style="width: 140px;"
      >
        <el-option
          v-for="type in craftTypes"
          :key="type"
          :label="type"
          :value="type"
        />
      </el-select>
      <el-select
        v-model="queryParams.publisher_type"
        placeholder="发布人类型"
        clearable
        style="width: 140px;"
      >
        <el-option label="官方" value="official" />
        <el-option label="老师" value="teacher" />
      </el-select>
      <el-select
        v-model="queryParams.computed_status"
        placeholder="活动状态"
        clearable
        style="width: 140px;"
      >
        <el-option label="待审核" value="pending_review" />
        <el-option label="未开始" value="not_started" />
        <el-option label="进行中" value="in_progress" />
        <el-option label="已结束" value="ended" />
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
        <el-table-column prop="id" label="活动ID" width="80" />
        <el-table-column prop="cover_image" label="封面" width="100">
          <template #default="scope">
            <el-image
              :src="scope.row.cover_image"
              :preview-src-list="scope.row.images || [scope.row.cover_image]"
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
        <el-table-column prop="is_official" label="发布类型" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_official ? 'primary' : 'warning'">
              {{ scope.row.is_official ? '官方' : '老师' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="activity_type" label="活动类型" width="100" />
        <el-table-column prop="craft_type" label="手工种类" width="100" />
        <el-table-column prop="price" label="费用" width="100">
          <template #default="scope">
            <span v-if="scope.row.price > 0" style="color: #ff6b35; font-weight: bold;">
              ¥{{ scope.row.price?.toFixed(2) }}
            </span>
            <span v-else style="color: #67c23a;">免费</span>
          </template>
        </el-table-column>
        <el-table-column label="报名情况" width="120">
          <template #default="scope">
            <span>{{ scope.row.current_participants || 0 }} / {{ scope.row.max_participants || 999 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="computed_status" label="活动状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusTagType(scope.row.computed_status, scope.row.verify_status)">
              {{ getStatusText(scope.row.computed_status, scope.row.verify_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="160" />
        <el-table-column label="操作" fixed="right" width="280">
          <template #default="scope">
            <div class="operation-btns">
              <el-button type="primary" link @click="handleView(scope.row)">
                详情
              </el-button>
              <el-button type="primary" link @click="handleStats(scope.row)">
                统计
              </el-button>
              <template v-if="scope.row.verify_status === 'approved'">
                <el-button
                  type="primary"
                  link
                  @click="handleEdit(scope.row)"
                  :disabled="isActivityEnded(scope.row)"
                >
                  编辑
                </el-button>
                <el-button
                  type="danger"
                  link
                  @click="handleDelete(scope.row)"
                >
                  删除
                </el-button>
              </template>
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
    
    <el-dialog v-model="officialVisible" title="官方发布活动" width="800px" :close-on-click-modal="false">
      <el-form
        :model="officialForm"
        :rules="officialRules"
        ref="officialFormRef"
        label-width="120px"
      >
        <el-form-item label="活动标题" prop="title">
          <el-input v-model="officialForm.title" placeholder="请输入活动标题（至少5个字）" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="活动类型" prop="activity_type">
              <el-select v-model="officialForm.activity_type" placeholder="请选择活动类型" style="width: 100%;">
                <el-option label="线下课程" value="线下课程" />
                <el-option label="线上直播" value="线上直播" />
                <el-option label="线下体验" value="线下体验" />
                <el-option label="比赛" value="比赛" />
                <el-option label="展览" value="展览" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手工种类" prop="craft_type">
              <el-select v-model="officialForm.craft_type" placeholder="请选择手工种类" style="width: 100%;">
                <el-option
                  v-for="type in craftTypes"
                  :key="type"
                  :label="type"
                  :value="type"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间" prop="start_time">
              <el-date-picker
                v-model="officialForm.start_time"
                type="datetime"
                placeholder="选择开始时间"
                style="width: 100%;"
                format="YYYY-MM-DD HH:mm:ss"
                value-format="YYYY-MM-DD HH:mm:ss"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间" prop="end_time">
              <el-date-picker
                v-model="officialForm.end_time"
                type="datetime"
                placeholder="选择结束时间"
                style="width: 100%;"
                format="YYYY-MM-DD HH:mm:ss"
                value-format="YYYY-MM-DD HH:mm:ss"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="活动地点" prop="location">
              <el-input v-model="officialForm.location" placeholder="请输入活动地点" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="详细地址" prop="address">
              <el-input v-model="officialForm.address" placeholder="请输入详细地址" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="活动费用" prop="price">
              <el-input-number
                v-model="officialForm.price"
                :min="0"
                :precision="2"
                placeholder="活动费用"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大人数" prop="max_participants">
              <el-input-number
                v-model="officialForm.max_participants"
                :min="1"
                placeholder="最大参与人数"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="活动流程" prop="process">
          <el-input
            v-model="officialForm.process"
            type="textarea"
            :rows="3"
            placeholder="请输入活动流程（至少20个字）"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="报名方式" prop="registration_method">
          <el-input
            v-model="officialForm.registration_method"
            type="textarea"
            :rows="2"
            placeholder="请输入报名方式"
          />
        </el-form-item>
        <el-form-item label="活动描述" prop="description">
          <el-input
            v-model="officialForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入活动描述"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="活动图片" prop="images">
          <div class="upload-images">
            <div
              v-for="(img, index) in officialForm.images"
              :key="index"
              class="upload-image-item"
            >
              <el-image :src="img" fit="cover" class="upload-preview">
                <template #error>
                  <div class="image-slot-small">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
              <el-button
                type="danger"
                link
                class="delete-image-btn"
                @click="removeOfficialImage(index)"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <el-upload
              class="image-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleOfficialUploadSuccess"
              :before-upload="beforeUpload"
              multiple
              :limit="20"
            >
              <div class="upload-image-placeholder">
                <el-icon><Plus /></el-icon>
                <span>添加图片</span>
              </div>
            </el-upload>
          </div>
          <div class="form-tip">提示：至少上传1张活动图片，最多20张</div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="officialVisible = false">取消</el-button>
        <el-button type="primary" @click="submitOfficial" :loading="submitLoading">发布</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="editVisible" title="编辑活动" width="800px" :close-on-click-modal="false">
      <el-form
        :model="editForm"
        :rules="editRules"
        ref="editFormRef"
        label-width="120px"
      >
        <el-form-item label="活动标题" prop="title">
          <el-input v-model="editForm.title" placeholder="请输入活动标题" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="活动类型" prop="activity_type">
              <el-select v-model="editForm.activity_type" placeholder="请选择活动类型" style="width: 100%;">
                <el-option label="线下课程" value="线下课程" />
                <el-option label="线上直播" value="线上直播" />
                <el-option label="线下体验" value="线下体验" />
                <el-option label="比赛" value="比赛" />
                <el-option label="展览" value="展览" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手工种类" prop="craft_type">
              <el-select v-model="editForm.craft_type" placeholder="请选择手工种类" style="width: 100%;">
                <el-option
                  v-for="type in craftTypes"
                  :key="type"
                  :label="type"
                  :value="type"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间" prop="start_time">
              <el-date-picker
                v-model="editForm.start_time"
                type="datetime"
                placeholder="选择开始时间"
                style="width: 100%;"
                format="YYYY-MM-DD HH:mm:ss"
                value-format="YYYY-MM-DD HH:mm:ss"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间" prop="end_time">
              <el-date-picker
                v-model="editForm.end_time"
                type="datetime"
                placeholder="选择结束时间"
                style="width: 100%;"
                format="YYYY-MM-DD HH:mm:ss"
                value-format="YYYY-MM-DD HH:mm:ss"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="活动地点" prop="location">
              <el-input v-model="editForm.location" placeholder="请输入活动地点" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="详细地址" prop="address">
              <el-input v-model="editForm.address" placeholder="请输入详细地址" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="活动费用" prop="price">
              <el-input-number
                v-model="editForm.price"
                :min="0"
                :precision="2"
                placeholder="活动费用"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大人数" prop="max_participants">
              <el-input-number
                v-model="editForm.max_participants"
                :min="1"
                placeholder="最大参与人数"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="活动流程" prop="process">
          <el-input
            v-model="editForm.process"
            type="textarea"
            :rows="3"
            placeholder="请输入活动流程"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="报名方式" prop="registration_method">
          <el-input
            v-model="editForm.registration_method"
            type="textarea"
            :rows="2"
            placeholder="请输入报名方式"
          />
        </el-form-item>
        <el-form-item label="活动描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入活动描述"
          />
        </el-form-item>
        <el-form-item label="活动图片" prop="images">
          <div class="upload-images">
            <div
              v-for="(img, index) in editForm.images"
              :key="index"
              class="upload-image-item"
            >
              <el-image :src="img" fit="cover" class="upload-preview">
                <template #error>
                  <div class="image-slot-small">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
              <el-button
                type="danger"
                link
                class="delete-image-btn"
                @click="removeEditImage(index)"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <el-upload
              class="image-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleEditUploadSuccess"
              :before-upload="beforeUpload"
              multiple
              :limit="20"
            >
              <div class="upload-image-placeholder">
                <el-icon><Plus /></el-icon>
                <span>添加图片</span>
              </div>
            </el-upload>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="statsVisible" title="活动统计" width="900px">
      <div v-if="currentActivity">
        <el-row :gutter="24" style="margin-bottom: 20px;">
          <el-col :span="8">
            <el-card shadow="hover">
              <div class="stat-item">
                <div class="stat-value">{{ statsData.registration_count || 0 }}</div>
                <div class="stat-label">报名人数</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover">
              <div class="stat-item">
                <div class="stat-value">{{ statsData.view_count || 0 }}</div>
                <div class="stat-label">浏览量</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover">
              <div class="stat-item">
                <div class="stat-value">{{ currentActivity.max_participants || '不限' }}</div>
                <div class="stat-label">最大人数</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        
        <div class="section-title" style="margin-bottom: 16px;">
          <el-icon><User /></el-icon> 报名列表（共{{ statsData.registration_count || 0 }}人）
        </div>
        
        <el-table :data="statsData.registrations || []" stripe style="width: 100%">
          <el-table-column prop="user_nickname" label="用户昵称" width="150">
            <template #default="scope">
              <div class="user-cell">
                <el-avatar :size="32" :src="scope.row.user_avatar">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <span class="user-name">{{ scope.row.user_nickname || '用户' + scope.row.user_id }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="报名状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.status === 'confirmed' ? 'success' : 'warning'">
                {{ scope.row.status === 'confirmed' ? '已确认' : '待确认' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="number_of_people" label="人数" width="80" />
          <el-table-column prop="contact_phone" label="联系电话" width="120" />
          <el-table-column prop="contact_name" label="联系人" width="100" />
          <el-table-column prop="created_at" label="报名时间" width="160" />
          <el-table-column prop="special_requests" label="特殊需求" min-width="150" show-overflow-tooltip />
        </el-table>
      </div>
      
      <template #footer>
        <el-button @click="statsVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getActivities,
  getActivityTypes,
  createOfficialActivity,
  adminEditActivity,
  adminDeleteActivity,
  getActivityDetailStats
} from '@/api/activities'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const total = ref(0)
const craftTypes = ref([])
const officialVisible = ref(false)
const editVisible = ref(false)
const statsVisible = ref(false)
const currentActivity = ref(null)
const officialFormRef = ref(null)
const editFormRef = ref(null)
const statsData = ref({
  registration_count: 0,
  view_count: 0,
  registrations: []
})

const queryParams = reactive({
  page: 1,
  size: 10,
  keyword: '',
  activity_type: '',
  craft_type: '',
  publisher_type: '',
  computed_status: ''
})

const officialForm = reactive({
  title: '',
  activity_type: '',
  craft_type: '',
  start_time: '',
  end_time: '',
  location: '',
  address: '',
  price: 0,
  max_participants: 999,
  process: '',
  registration_method: '',
  description: '',
  images: []
})

const editForm = reactive({
  id: null,
  title: '',
  activity_type: '',
  craft_type: '',
  start_time: '',
  end_time: '',
  location: '',
  address: '',
  price: 0,
  max_participants: 999,
  process: '',
  registration_method: '',
  description: '',
  images: []
})

const officialRules = {
  title: [
    { required: true, message: '请输入活动标题', trigger: 'blur' },
    { min: 5, message: '活动标题不能少于5个字', trigger: 'blur' }
  ],
  activity_type: [
    { required: true, message: '请选择活动类型', trigger: 'change' }
  ],
  craft_type: [
    { required: true, message: '请选择手工种类', trigger: 'change' }
  ],
  process: [
    { required: true, message: '请输入活动流程', trigger: 'blur' },
    { min: 20, message: '活动流程不能少于20个字', trigger: 'blur' }
  ],
  start_time: [
    { required: true, message: '请选择开始时间', trigger: 'change' }
  ],
  end_time: [
    { required: true, message: '请选择结束时间', trigger: 'change' }
  ]
}

const editRules = {
  title: [
    { required: true, message: '请输入活动标题', trigger: 'blur' }
  ],
  activity_type: [
    { required: true, message: '请选择活动类型', trigger: 'change' }
  ],
  craft_type: [
    { required: true, message: '请选择手工种类', trigger: 'change' }
  ]
}

const getStatusText = (computedStatus, verifyStatus) => {
  if (verifyStatus === 'pending') return '待审核'
  if (verifyStatus === 'rejected') return '已拒绝'
  const statusMap = {
    not_started: '未开始',
    in_progress: '进行中',
    ended: '已结束'
  }
  return statusMap[computedStatus] || '未知'
}

const getStatusTagType = (computedStatus, verifyStatus) => {
  if (verifyStatus === 'pending') return 'warning'
  if (verifyStatus === 'rejected') return 'danger'
  const typeMap = {
    not_started: 'info',
    in_progress: 'success',
    ended: 'info'
  }
  return typeMap[computedStatus] || 'info'
}

const isActivityEnded = (row) => {
  if (row.computed_status === 'ended') return true
  return false
}

const fetchTypes = async () => {
  try {
    const res = await getActivityTypes()
    if (res.code === 0) {
      craftTypes.value = res.data.craft_types || []
    }
  } catch (e) {
    craftTypes.value = ['编织', '陶艺', '纸艺', '刺绣', '木工', '皮革', '其他']
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: queryParams.page,
      size: queryParams.size
    }
    if (queryParams.keyword) params.keyword = queryParams.keyword
    if (queryParams.activity_type) params.activity_type = queryParams.activity_type
    if (queryParams.craft_type) params.craft_type = queryParams.craft_type
    if (queryParams.publisher_type) params.publisher_type = queryParams.publisher_type
    if (queryParams.computed_status) params.computed_status = queryParams.computed_status
    
    const res = await getActivities(params)
    if (res.code === 0) {
      tableData.value = res.data.list || []
      total.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取活动列表失败:', e)
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
  queryParams.activity_type = ''
  queryParams.craft_type = ''
  queryParams.publisher_type = ''
  queryParams.computed_status = ''
  fetchData()
}

const handleAddOfficial = () => {
  officialForm.title = ''
  officialForm.activity_type = ''
  officialForm.craft_type = ''
  officialForm.start_time = ''
  officialForm.end_time = ''
  officialForm.location = ''
  officialForm.address = ''
  officialForm.price = 0
  officialForm.max_participants = 999
  officialForm.process = ''
  officialForm.registration_method = ''
  officialForm.description = ''
  officialForm.images = []
  officialVisible.value = true
}

const removeOfficialImage = (index) => {
  officialForm.images.splice(index, 1)
}

const submitOfficial = async () => {
  if (!officialFormRef.value) return
  
  await officialFormRef.value.validate(async (valid) => {
    if (valid) {
      if (!officialForm.images || officialForm.images.length < 1) {
        ElMessage.warning('请至少上传1张活动图片')
        return
      }
      
      submitLoading.value = true
      try {
        const data = {
          title: officialForm.title,
          activity_type: officialForm.activity_type,
          craft_type: officialForm.craft_type,
          start_time: officialForm.start_time,
          end_time: officialForm.end_time,
          location: officialForm.location,
          address: officialForm.address,
          price: officialForm.price,
          max_participants: officialForm.max_participants,
          process: officialForm.process,
          registration_method: officialForm.registration_method,
          description: officialForm.description,
          images: officialForm.images
        }
        
        const res = await createOfficialActivity(data)
        if (res.code === 0) {
          ElMessage.success('官方活动发布成功')
          officialVisible.value = false
          fetchData()
        }
      } catch (e) {
        console.error('发布失败:', e)
        ElMessage.error(e.response?.data?.msg || '发布失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleView = (row) => {
  currentActivity.value = { ...row }
  ElMessage.info('活动详情功能开发中')
}

const handleEdit = (row) => {
  if (isActivityEnded(row)) {
    ElMessage.warning('活动已结束，无法编辑')
    return
  }
  
  editForm.id = row.id
  editForm.title = row.title
  editForm.activity_type = row.activity_type
  editForm.craft_type = row.craft_type
  editForm.start_time = row.start_time
  editForm.end_time = row.end_time
  editForm.location = row.location
  editForm.address = row.address
  editForm.price = row.price
  editForm.max_participants = row.max_participants
  editForm.process = row.process
  editForm.registration_method = row.registration_method
  editForm.description = row.description
  editForm.images = row.images ? [...row.images] : []
  editVisible.value = true
}

const removeEditImage = (index) => {
  editForm.images.splice(index, 1)
}

const submitEdit = async () => {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        const data = {
          title: editForm.title,
          activity_type: editForm.activity_type,
          craft_type: editForm.craft_type,
          start_time: editForm.start_time,
          end_time: editForm.end_time,
          location: editForm.location,
          address: editForm.address,
          price: editForm.price,
          max_participants: editForm.max_participants,
          process: editForm.process,
          registration_method: editForm.registration_method,
          description: editForm.description,
          images: editForm.images
        }
        
        const res = await adminEditActivity(editForm.id, data)
        if (res.code === 0) {
          ElMessage.success('活动更新成功')
          editVisible.value = false
          fetchData()
        }
      } catch (e) {
        console.error('更新失败:', e)
        ElMessage.error(e.response?.data?.msg || '更新失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除该活动吗？删除前将校验是否有报名人数，有人则无法删除。',
      '警告',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const res = await adminDeleteActivity(row.id)
    if (res.code === 0) {
      ElMessage.success('活动已删除')
      fetchData()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除失败:', e)
      ElMessage.error(e.response?.data?.msg || '删除失败')
    }
  }
}

const handleStats = async (row) => {
  currentActivity.value = { ...row }
  statsVisible.value = true
  
  try {
    const res = await getActivityDetailStats(row.id)
    if (res.code === 0) {
      statsData.value = res.data || {
        registration_count: 0,
        view_count: 0,
        registrations: []
      }
    }
  } catch (e) {
    console.error('获取统计失败:', e)
  }
}

const uploadUrl = '/api/upload/image'
const uploadHeaders = {
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`
}

const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt10M = file.size / 1024 / 1024 < 10
  
  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过 10MB!')
    return false
  }
  return true
}

const handleOfficialUploadSuccess = (response) => {
  if (response.code === 0 || response.url) {
    const url = response.url || response.data?.url
    if (url && !officialForm.images.includes(url)) {
      officialForm.images.push(url)
      ElMessage.success('上传成功')
    }
  } else {
    ElMessage.error('上传失败: ' + (response.msg || '未知错误'))
  }
}

const handleEditUploadSuccess = (response) => {
  if (response.code === 0 || response.url) {
    const url = response.url || response.data?.url
    if (url && !editForm.images.includes(url)) {
      editForm.images.push(url)
      ElMessage.success('上传成功')
    }
  } else {
    ElMessage.error('上传失败: ' + (response.msg || '未知错误'))
  }
}

onMounted(() => {
  fetchTypes()
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

.image-slot-small {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
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

.upload-images {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.upload-image-item {
  position: relative;
  width: 100px;
  height: 100px;
}

.upload-preview {
  width: 100%;
  height: 100%;
  border-radius: 8px;
  border: 1px solid #eee;
}

.delete-image-btn {
  position: absolute;
  top: -10px;
  right: -10px;
  background: #fff;
  border-radius: 50%;
  padding: 2px;
}

.upload-image-placeholder {
  width: 100px;
  height: 100px;
  border: 1px dashed #dcdfe6;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-image-placeholder:hover {
  border-color: #409eff;
  color: #409eff;
}

.upload-image-placeholder .el-icon {
  font-size: 28px;
  margin-bottom: 4px;
}

.upload-image-placeholder span {
  font-size: 12px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.stat-item {
  text-align: center;
  padding: 10px 0;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-name {
  font-weight: 500;
}
</style>
