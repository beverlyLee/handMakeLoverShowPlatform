<template>
  <div class="page-card">
    <div class="page-header">
      <span class="page-title">用户管理</span>
      <el-button type="primary" @click="handleExport">
        <el-icon><Download /></el-icon>
        导出报表
      </el-button>
    </div>
    
    <div class="filter-bar">
      <el-input
        v-model="queryParams.user_id"
        placeholder="用户ID（精确搜索）"
        clearable
        style="width: 150px;"
        @keyup.enter="handleSearch"
      />
      <el-input
        v-model="queryParams.keyword"
        placeholder="昵称/手机号（模糊搜索）"
        clearable
        style="width: 200px;"
        @keyup.enter="handleSearch"
      />
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="注册开始日期"
        end-placeholder="注册结束日期"
        value-format="YYYY-MM-DD"
        style="width: 280px;"
      />
      <el-select
        v-model="queryParams.status"
        placeholder="账号状态"
        clearable
        style="width: 120px;"
      >
        <el-option label="启用" value="active" />
        <el-option label="禁用" value="inactive" />
      </el-select>
      <el-select
        v-model="queryParams.role"
        placeholder="用户角色"
        clearable
        style="width: 120px;"
      >
        <el-option label="普通用户" value="customer" />
        <el-option label="手作老师" value="teacher" />
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
        <el-table-column prop="avatar" label="头像" width="80">
          <template #default="scope">
            <el-avatar :size="40" :src="scope.row.avatar">
              <el-icon><User /></el-icon>
            </el-avatar>
          </template>
        </el-table-column>
        <el-table-column prop="nickname" label="昵称" width="120" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="current_role" label="角色" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.current_role === 'teacher' ? 'primary' : 'info'">
              {{ scope.row.current_role === 'teacher' ? '手作老师' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="90">
          <template #default="scope">
            <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
              {{ scope.row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="注册时间" width="180" />
        <el-table-column label="操作" fixed="right" width="260">
          <template #default="scope">
            <div class="operation-btns">
              <el-button type="primary" link @click="handleView(scope.row)">
                详情
              </el-button>
              <el-button type="primary" link @click="handleEdit(scope.row)">
                编辑
              </el-button>
              <el-button
                :type="scope.row.is_active ? 'danger' : 'success'"
                link
                @click="handleToggleStatus(scope.row)"
              >
                {{ scope.row.is_active ? '禁用' : '启用' }}
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
    
    <el-dialog v-model="detailVisible" :title="dialogTitle" width="900px" :close-on-click-modal="false">
      <el-descriptions :column="2" border v-if="currentUser">
        <el-descriptions-item label="ID">{{ currentUser.id }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ currentUser.nickname }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ currentUser.username }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ currentUser.phone || '未设置' }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ currentUser.email || '未设置' }}</el-descriptions-item>
        <el-descriptions-item label="性别">
          {{ currentUser.gender === 1 ? '男' : currentUser.gender === 2 ? '女' : '未知' }}
        </el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag :type="currentUser.current_role === 'teacher' ? 'primary' : 'info'">
            {{ currentUser.current_role === 'teacher' ? '手作老师' : '普通用户' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="账号状态">
          <el-tag :type="currentUser.is_active ? 'success' : 'danger'">
            {{ currentUser.is_active ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ currentUser.create_time }}</el-descriptions-item>
        <el-descriptions-item label="个人简介" :span="2">
          {{ currentUser.bio || '暂无简介' }}
        </el-descriptions-item>
      </el-descriptions>
      
      <el-tabs v-model="detailTab" class="detail-tabs" style="margin-top: 20px;">
        <el-tab-pane label="点赞记录" name="likes">
          <el-table :data="likesList" stripe v-loading="likesLoading" style="width: 100%;">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="product_image" label="商品" width="100">
              <template #default="scope">
                <el-image
                  :src="scope.row.product_image"
                  :preview-src-list="[scope.row.product_image]"
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
            <el-table-column prop="product_title" label="商品名称" min-width="200" />
            <el-table-column prop="product_price" label="价格" width="100">
              <template #default="scope">
                ¥{{ scope.row.product_price?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="create_time" label="点赞时间" width="180" />
          </el-table>
          <div class="pagination-wrapper" v-if="likesTotal > 0">
            <el-pagination
              v-model:current-page="likesPage"
              :page-sizes="[5, 10]"
              :page-size="10"
              :total="likesTotal"
              layout="total, prev, pager, next"
              @current-change="fetchLikes"
            />
          </div>
          <el-empty v-if="likesList.length === 0 && !likesLoading" description="暂无点赞记录" />
        </el-tab-pane>
        
        <el-tab-pane label="订单记录" name="orders">
          <el-table :data="ordersList" stripe v-loading="ordersLoading" style="width: 100%;">
            <el-table-column prop="id" label="订单号" min-width="180" />
            <el-table-column prop="teacher_nickname" label="接单老师" width="100" />
            <el-table-column prop="total_amount" label="订单金额" width="100">
              <template #default="scope">
                ¥{{ scope.row.total_amount?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="pay_amount" label="实付金额" width="100">
              <template #default="scope">
                ¥{{ scope.row.pay_amount?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="status_name" label="订单状态" width="100">
              <template #default="scope">
                <el-tag :type="getOrderStatusType(scope.row.status)">
                  {{ scope.row.status_name }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="create_time" label="下单时间" width="180" />
          </el-table>
          <div class="pagination-wrapper" v-if="ordersTotal > 0">
            <el-pagination
              v-model:current-page="ordersPage"
              :page-sizes="[5, 10]"
              :page-size="10"
              :total="ordersTotal"
              layout="total, prev, pager, next"
              @current-change="fetchOrders"
            />
          </div>
          <el-empty v-if="ordersList.length === 0 && !ordersLoading" description="暂无订单记录" />
        </el-tab-pane>
        
        <el-tab-pane label="评价记录" name="reviews">
          <el-table :data="reviewsList" stripe v-loading="reviewsLoading" style="width: 100%;">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="product_image" label="商品" width="100">
              <template #default="scope">
                <el-image
                  :src="scope.row.product_image"
                  :preview-src-list="[scope.row.product_image]"
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
            <el-table-column prop="product_title" label="商品名称" min-width="150" />
            <el-table-column prop="overall_rating" label="评分" width="120">
              <template #default="scope">
                <el-rate v-model="scope.row.overall_rating" disabled :max="5" size="small" />
              </template>
            </el-table-column>
            <el-table-column prop="content" label="评价内容" min-width="200" show-overflow-tooltip />
            <el-table-column prop="create_time" label="评价时间" width="180" />
          </el-table>
          <div class="pagination-wrapper" v-if="reviewsTotal > 0">
            <el-pagination
              v-model:current-page="reviewsPage"
              :page-sizes="[5, 10]"
              :page-size="10"
              :total="reviewsTotal"
              layout="total, prev, pager, next"
              @current-change="fetchReviews"
            />
          </div>
          <el-empty v-if="reviewsList.length === 0 && !reviewsLoading" description="暂无评价记录" />
        </el-tab-pane>
      </el-tabs>
      
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleEdit(currentUser)">编辑</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="editVisible" title="编辑用户" width="500px" :close-on-click-modal="false">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="ID">
          <el-input v-model="editForm.id" disabled />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="editForm.nickname" placeholder="请输入昵称" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="editForm.phone" placeholder="请输入手机号" maxlength="11" />
        </el-form-item>
        <el-form-item label="个人简介" prop="bio">
          <el-input
            v-model="editForm.bio"
            type="textarea"
            :rows="3"
            placeholder="请输入个人简介"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="editLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getUsers,
  getUserDetail,
  updateUser,
  updateUserStatus,
  getUserLikes,
  getUserOrders,
  getUserReviews,
  exportUserStats
} from '@/api/users'

const loading = ref(false)
const editLoading = ref(false)
const tableData = ref([])
const total = ref(0)
const detailVisible = ref(false)
const editVisible = ref(false)
const dialogTitle = ref('用户详情')
const currentUser = ref(null)
const editFormRef = ref(null)

const dateRange = ref([])

const queryParams = reactive({
  page: 1,
  size: 10,
  user_id: null,
  keyword: '',
  role: '',
  status: '',
  sort: 'newest'
})

const editForm = reactive({
  id: null,
  nickname: '',
  phone: '',
  bio: ''
})

const validatePhone = (rule, value, callback) => {
  if (value && !/^1\d{10}$/.test(value)) {
    callback(new Error('请输入正确的11位手机号'))
  } else {
    callback()
  }
}

const editRules = {
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  phone: [{ validator: validatePhone, trigger: 'blur' }]
}

const detailTab = ref('likes')

const likesList = ref([])
const likesLoading = ref(false)
const likesTotal = ref(0)
const likesPage = ref(1)

const ordersList = ref([])
const ordersLoading = ref(false)
const ordersTotal = ref(0)
const ordersPage = ref(1)

const reviewsList = ref([])
const reviewsLoading = ref(false)
const reviewsTotal = ref(0)
const reviewsPage = ref(1)

const getOrderStatusType = (status) => {
  const statusTypeMap = {
    'completed': 'success',
    'paid': 'primary',
    'shipped': 'primary',
    'delivered': 'primary',
    'cancelled': 'info',
    'rejected': 'danger',
    'pending': 'warning',
    'pending_accept': 'warning',
    'accepted': 'warning',
    'in_progress': 'warning'
  }
  return statusTypeMap[status] || 'info'
}

watch(dateRange, (newVal) => {
  if (newVal && newVal.length === 2) {
    queryParams.start_date = newVal[0]
    queryParams.end_date = newVal[1]
  } else {
    delete queryParams.start_date
    delete queryParams.end_date
  }
})

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: queryParams.page,
      size: queryParams.size
    }
    if (queryParams.user_id) params.user_id = queryParams.user_id
    if (queryParams.keyword) params.keyword = queryParams.keyword
    if (queryParams.start_date) params.start_date = queryParams.start_date
    if (queryParams.end_date) params.end_date = queryParams.end_date
    if (queryParams.role) params.role = queryParams.role
    if (queryParams.status) params.status = queryParams.status
    if (queryParams.sort) params.sort = queryParams.sort
    
    const res = await getUsers(params)
    if (res.code === 0) {
      tableData.value = res.data.list || []
      total.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取用户列表失败:', e)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const fetchLikes = async () => {
  if (!currentUser.value) return
  likesLoading.value = true
  try {
    const res = await getUserLikes(currentUser.value.id, {
      page: likesPage.value,
      size: 10
    })
    if (res.code === 0) {
      likesList.value = res.data.list || []
      likesTotal.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取点赞记录失败:', e)
  } finally {
    likesLoading.value = false
  }
}

const fetchOrders = async () => {
  if (!currentUser.value) return
  ordersLoading.value = true
  try {
    const res = await getUserOrders(currentUser.value.id, {
      page: ordersPage.value,
      size: 10
    })
    if (res.code === 0) {
      ordersList.value = res.data.list || []
      ordersTotal.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取订单记录失败:', e)
  } finally {
    ordersLoading.value = false
  }
}

const fetchReviews = async () => {
  if (!currentUser.value) return
  reviewsLoading.value = true
  try {
    const res = await getUserReviews(currentUser.value.id, {
      page: reviewsPage.value,
      size: 10
    })
    if (res.code === 0) {
      reviewsList.value = res.data.list || []
      reviewsTotal.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取评价记录失败:', e)
  } finally {
    reviewsLoading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const resetQuery = () => {
  queryParams.page = 1
  queryParams.user_id = null
  queryParams.keyword = ''
  queryParams.role = ''
  queryParams.status = ''
  queryParams.sort = 'newest'
  dateRange.value = []
  delete queryParams.start_date
  delete queryParams.end_date
  fetchData()
}

const handleView = async (row) => {
  try {
    const res = await getUserDetail(row.id)
    if (res.code === 0) {
      currentUser.value = res.data
    }
  } catch (e) {
    currentUser.value = row
  }
  dialogTitle.value = '用户详情'
  detailTab.value = 'likes'
  likesPage.value = 1
  ordersPage.value = 1
  reviewsPage.value = 1
  fetchLikes()
  fetchOrders()
  fetchReviews()
  detailVisible.value = true
}

const handleEdit = (row) => {
  detailVisible.value = false
  editForm.id = row.id
  editForm.nickname = row.nickname || ''
  editForm.phone = row.phone || ''
  editForm.bio = row.bio || ''
  editVisible.value = true
}

const submitEdit = async () => {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      editLoading.value = true
      try {
        const data = {
          nickname: editForm.nickname,
          phone: editForm.phone || null,
          bio: editForm.bio
        }
        
        const res = await updateUser(editForm.id, data)
        if (res.code === 0) {
          ElMessage.success('更新成功')
          editVisible.value = false
          fetchData()
        }
      } catch (e) {
        console.error('更新用户失败:', e)
        ElMessage.error(e.response?.data?.msg || '更新失败')
      } finally {
        editLoading.value = false
      }
    }
  })
}

const handleToggleStatus = async (row) => {
  const action = row.is_active ? '禁用' : '启用'
  const confirmText = row.is_active 
    ? '确定要禁用该用户吗？禁用后用户将无法登录。' 
    : '确定要启用该用户吗？'
  
  try {
    await ElMessageBox.confirm(confirmText, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: row.is_active ? 'warning' : 'info'
    })
    
    const res = await updateUserStatus(row.id, { is_active: !row.is_active })
    if (res.code === 0) {
      ElMessage.success(`用户已${action}`)
      fetchData()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('操作失败:', e)
      ElMessage.error(e.response?.data?.msg || '操作失败')
    }
  }
}

const handleExport = async () => {
  try {
    const params = {}
    if (queryParams.user_id) params.user_id = queryParams.user_id
    if (queryParams.keyword) params.keyword = queryParams.keyword
    if (queryParams.start_date) params.start_date = queryParams.start_date
    if (queryParams.end_date) params.end_date = queryParams.end_date
    if (queryParams.role) params.role = queryParams.role
    if (queryParams.status) params.status = queryParams.status
    
    const res = await exportUserStats(params)
    if (res.code === 0) {
      const blob = new Blob([res.data.csv_content], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', res.data.filename)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      ElMessage.success('导出成功')
    }
  } catch (e) {
    console.error('导出失败:', e)
    ElMessage.error('导出失败')
  }
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

.detail-tabs {
  margin-top: 20px;
}
</style>