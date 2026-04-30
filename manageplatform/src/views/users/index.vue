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
        v-model="queryParams.keyword"
        placeholder="搜索用户名/昵称/手机号"
        clearable
        style="width: 200px;"
        @keyup.enter="handleSearch"
      />
      <el-select
        v-model="queryParams.role"
        placeholder="用户角色"
        clearable
        style="width: 140px;"
      >
        <el-option label="普通用户" value="customer" />
        <el-option label="手作老师" value="teacher" />
      </el-select>
      <el-select
        v-model="queryParams.sort"
        placeholder="排序方式"
        clearable
        style="width: 140px;"
      >
        <el-option label="最新注册" value="newest" />
        <el-option label="最早注册" value="oldest" />
        <el-option label="最近活跃" value="active" />
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
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="current_role" label="角色" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.current_role === 'teacher' ? 'primary' : 'info'">
              {{ scope.row.current_role === 'teacher' ? '手作老师' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_teacher" label="是否老师" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_teacher ? 'success' : 'info'">
            {{ scope.row.is_teacher ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="注册时间" width="180" />
        <el-table-column label="操作" fixed="right" width="220">
          <template #default="scope">
            <div class="operation-btns">
              <el-button type="primary" link @click="handleView(scope.row)">
                查看
              </el-button>
              <el-button type="primary" link @click="handleEdit(scope.row)">
                编辑
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
    
    <el-dialog v-model="detailVisible" :title="dialogTitle" width="700px">
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
        <el-descriptions-item label="注册时间">{{ currentUser.create_time }}</el-descriptions-item>
        <el-descriptions-item label="个人简介" :span="2">
          {{ currentUser.bio || '暂无简介' }}
        </el-descriptions-item>
        <el-descriptions-item label="订单数">{{ currentUser.order_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="评价数">{{ currentUser.review_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="点赞数">{{ currentUser.like_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="活跃状态">
          <el-tag type="success">活跃</el-tag>
        </el-descriptions-item>
        <template v-if="currentUser.teacher_info">
          <el-descriptions-item label="老师信息" :span="2">
            <div>真实姓名: {{ currentUser.teacher_info.real_name || '未设置' }}</div>
            <div>评分: {{ currentUser.teacher_info.rating || 0 }}分</div>
            <div>粉丝数: {{ currentUser.teacher_info.follower_count || 0 }}</div>
            <div>作品数: {{ currentUser.teacher_info.total_products || 0 }}</div>
            <div>完成订单数: {{ currentUser.teacher_info.total_orders || 0 }}</div>
            <div>
              认证状态: 
              <el-tag :type="currentUser.teacher_info.is_verified ? 'success' : 'info'">
                {{ currentUser.teacher_info.is_verified ? '已认证' : '未认证' }}
              </el-tag>
            </div>
          </el-descriptions-item>
        </template>
      </el-descriptions>
      
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleEdit(currentUser)">编辑</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="editVisible" title="编辑用户" width="600px">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="editForm.nickname" placeholder="请输入昵称" />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="editForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="editForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-radio-group v-model="editForm.gender">
            <el-radio :value="0">未知</el-radio>
            <el-radio :value="1">男</el-radio>
            <el-radio :value="2">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="当前角色" prop="current_role">
          <el-select v-model="editForm.current_role" style="width: 100%;">
            <el-option label="普通用户" value="customer" />
            <el-option label="手作老师" value="teacher" />
          </el-select>
        </el-form-item>
        <el-form-item label="个人简介" prop="bio">
          <el-input
            v-model="editForm.bio"
            type="textarea"
            :rows="3"
            placeholder="请输入个人简介"
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
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUsers, getUserDetail, updateUser, exportUserStats } from '@/api/users'

const loading = ref(false)
const editLoading = ref(false)
const tableData = ref([])
const total = ref(0)
const detailVisible = ref(false)
const editVisible = ref(false)
const dialogTitle = ref('用户详情')
const currentUser = ref(null)
const editFormRef = ref(null)

const queryParams = reactive({
  page: 1,
  size: 10,
  keyword: '',
  role: '',
  sort: 'newest'
})

const editForm = reactive({
  id: null,
  nickname: '',
  username: '',
  phone: '',
  email: '',
  gender: 0,
  current_role: 'customer',
  bio: ''
})

const editRules = {
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: queryParams.page,
      size: queryParams.size
    }
    if (queryParams.keyword) params.keyword = queryParams.keyword
    if (queryParams.role) params.role = queryParams.role
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

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const resetQuery = () => {
  queryParams.page = 1
  queryParams.keyword = ''
  queryParams.role = ''
  queryParams.sort = 'newest'
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
  detailVisible.value = true
}

const handleEdit = (row) => {
  detailVisible.value = false
  editForm.id = row.id
  editForm.nickname = row.nickname || ''
  editForm.username = row.username || ''
  editForm.phone = row.phone || ''
  editForm.email = row.email || ''
  editForm.gender = row.gender || 0
  editForm.current_role = row.current_role || 'customer'
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
          username: editForm.username,
          phone: editForm.phone || null,
          email: editForm.email || null,
          gender: editForm.gender,
          current_role: editForm.current_role,
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
        ElMessage.error('更新失败')
      } finally {
        editLoading.value = false
      }
    }
  })
}

const handleExport = async () => {
  try {
    const params = {}
    if (queryParams.keyword) params.keyword = queryParams.keyword
    if (queryParams.role) params.role = queryParams.role
    
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
