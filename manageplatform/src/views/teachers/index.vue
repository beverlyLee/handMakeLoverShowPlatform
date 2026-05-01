<template>
  <div class="page-card">
    <div class="page-header">
      <span class="page-title">老师管理</span>
    </div>
    
    <div class="filter-wrapper">
      <el-form :inline="true" :model="queryParams" label-width="80px">
        <el-form-item label="老师ID">
          <el-input v-model="queryParams.id" placeholder="精确搜索" clearable style="width: 150px" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="queryParams.name" placeholder="姓名模糊搜索" clearable style="width: 150px" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="擅长领域">
          <el-select v-model="queryParams.specialty" placeholder="选择擅长领域" clearable style="width: 150px">
            <el-option v-for="s in specialties" :key="s.id" :label="s.name" :value="s.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="审核状态">
          <el-select v-model="queryParams.verify_status" placeholder="全部状态" clearable style="width: 120px">
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon> 重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>
    
    <div class="table-wrapper">
      <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="user_info" label="用户信息" width="180">
          <template #default="scope">
            <div class="user-info-cell">
              <el-avatar :size="40" :src="scope.row.user_info?.avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <div class="user-detail">
                <div class="nickname">{{ scope.row.user_info?.nickname || scope.row.real_name || '未知' }}</div>
                <div class="phone">{{ scope.row.phone || scope.row.user_info?.phone || '-' }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="specialties" label="擅长领域" min-width="150">
          <template #default="scope">
            <el-tag v-for="(s, i) in scope.row.specialties" :key="i" size="small" style="margin-right: 4px; margin-bottom: 4px;">
              {{ s }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="verify_status" label="审核状态" width="100">
          <template #default="scope">
            <el-tag v-if="scope.row.verify_status === 'pending'" type="warning">待审核</el-tag>
            <el-tag v-else-if="scope.row.verify_status === 'approved'" type="success">已通过</el-tag>
            <el-tag v-else type="danger">已拒绝</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="账号状态" width="100">
          <template #default="scope">
            <el-tag v-if="scope.row.is_active" type="success">正常</el-tag>
            <el-tag v-else type="danger">已禁用</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="studio_name" label="工作室" width="150" show-overflow-tooltip>
          <template #default="scope">
            <span>{{ scope.row.studio_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="experience_years" label="工作年限" width="90">
          <template #default="scope">
            <span>{{ scope.row.experience_years || 0 }}年</span>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="申请时间" width="180" />
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
                v-if="scope.row.is_active"
                type="danger" 
                link 
                @click="handleToggleStatus(scope.row)"
              >
                禁用
              </el-button>
              <el-button 
                v-else
                type="success" 
                link 
                @click="handleToggleStatus(scope.row)"
              >
                启用
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
    
    <el-dialog v-model="editVisible" :title="'编辑老师信息 - ' + (currentTeacher?.real_name || '未知')" width="600px" :close-on-click-modal="false">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="老师ID">
          <el-input v-model="editForm.id" disabled />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="editForm.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="editForm.phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="擅长领域" prop="specialties">
          <el-select v-model="editForm.specialties" multiple placeholder="请选择擅长领域" style="width: 100%">
            <el-option v-for="s in specialties" :key="s.id" :label="s.name" :value="s.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="工作室名称">
          <el-input v-model="editForm.studio_name" placeholder="请输入工作室名称" />
        </el-form-item>
        <el-form-item label="工作室地址">
          <el-input v-model="editForm.studio_address" placeholder="请输入工作室地址" />
        </el-form-item>
        <el-form-item label="工作年限">
          <el-input-number v-model="editForm.experience_years" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="个人简介" prop="intro">
          <el-input v-model="editForm.intro" type="textarea" :rows="4" placeholder="请输入个人简介" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="detailVisible" :title="'老师详情 - ' + (detailTeacher?.real_name || '未知')" width="1000px" :close-on-click-modal="false">
      <div v-if="detailTeacher">
        <el-tabs v-model="detailTab">
          <el-tab-pane label="基本信息" name="info">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="申请ID">{{ detailTeacher.id }}</el-descriptions-item>
              <el-descriptions-item label="真实姓名">{{ detailTeacher.real_name }}</el-descriptions-item>
              <el-descriptions-item label="联系电话">{{ detailTeacher.phone || '-' }}</el-descriptions-item>
              <el-descriptions-item label="身份证号">{{ detailTeacher.id_card || '-' }}</el-descriptions-item>
              <el-descriptions-item label="工作年限">{{ detailTeacher.experience_years || 0 }}年</el-descriptions-item>
              <el-descriptions-item label="工作室名称">{{ detailTeacher.studio_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="工作室地址">{{ detailTeacher.studio_address || '-' }}</el-descriptions-item>
              <el-descriptions-item label="审核状态">
                <el-tag v-if="detailTeacher.verify_status === 'pending'" type="warning">待审核</el-tag>
                <el-tag v-else-if="detailTeacher.verify_status === 'approved'" type="success">已通过</el-tag>
                <el-tag v-else type="danger">已拒绝</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="账号状态">
                <el-tag v-if="detailTeacher.is_active" type="success">正常</el-tag>
                <el-tag v-else type="danger">已禁用</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="申请时间">{{ detailTeacher.create_time }}</el-descriptions-item>
              <el-descriptions-item label="个人简介" :span="2">
                {{ detailTeacher.intro || detailTeacher.bio || '暂无简介' }}
              </el-descriptions-item>
              <el-descriptions-item label="擅长领域" :span="2">
                <el-tag v-for="(s, i) in detailTeacher.specialties" :key="i" style="margin-right: 8px;">
                  {{ s }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
            
            <div v-if="detailTeacher.verify_status === 'rejected'" style="margin-top: 16px;">
              <el-alert :title="'拒绝理由：' + (detailTeacher.reject_reason || '无')" type="error" :closable="false" />
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="作品列表" name="products">
            <el-table :data="productsList" stripe style="width: 100%" v-loading="productsLoading">
              <el-table-column prop="id" label="ID" width="70" />
              <el-table-column prop="title" label="作品标题" min-width="150" show-overflow-tooltip />
              <el-table-column prop="category" label="分类" width="100" />
              <el-table-column prop="price" label="价格" width="100">
                <template #default="scope">
                  ¥{{ scope.row.price }}
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="80">
                <template #default="scope">
                  <el-tag v-if="scope.row.status === 'active'" type="success">上架</el-tag>
                  <el-tag v-else type="info">下架</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="create_time" label="发布时间" width="180" />
            </el-table>
            <div class="pagination-wrapper" style="margin-top: 16px;">
              <el-pagination
                v-model:current-page="productsPage"
                v-model:page-size="productsSize"
                :page-sizes="[5, 10, 20]"
                :total="productsTotal"
                layout="total, sizes, prev, pager, next"
                @size-change="fetchProducts"
                @current-change="fetchProducts"
                small
              />
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="接单列表" name="orders">
            <el-table :data="ordersList" stripe style="width: 100%" v-loading="ordersLoading">
              <el-table-column prop="id" label="订单ID" width="100" />
              <el-table-column prop="product_title" label="作品" min-width="120" show-overflow-tooltip />
              <el-table-column prop="user_name" label="用户" width="100" />
              <el-table-column prop="total_amount" label="金额" width="100">
                <template #default="scope">
                  ¥{{ scope.row.total_amount }}
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="100">
                <template #default="scope">
                  <el-tag v-if="scope.row.status === 'pending'" type="warning">待处理</el-tag>
                  <el-tag v-else-if="scope.row.status === 'paid'" type="primary">已支付</el-tag>
                  <el-tag v-else-if="scope.row.status === 'processing'" type="info">制作中</el-tag>
                  <el-tag v-else-if="scope.row.status === 'shipped'" type="warning">已发货</el-tag>
                  <el-tag v-else-if="scope.row.status === 'completed'" type="success">已完成</el-tag>
                  <el-tag v-else type="danger">已取消</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="create_time" label="下单时间" width="180" />
            </el-table>
            <div class="pagination-wrapper" style="margin-top: 16px;">
              <el-pagination
                v-model:current-page="ordersPage"
                v-model:page-size="ordersSize"
                :page-sizes="[5, 10, 20]"
                :total="ordersTotal"
                layout="total, sizes, prev, pager, next"
                @size-change="fetchOrders"
                @current-change="fetchOrders"
                small
              />
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="评价列表" name="reviews">
            <el-table :data="reviewsList" stripe style="width: 100%" v-loading="reviewsLoading">
              <el-table-column prop="id" label="ID" width="70" />
              <el-table-column prop="order_id" label="订单ID" width="100" />
              <el-table-column prop="product_title" label="作品" min-width="120" show-overflow-tooltip />
              <el-table-column prop="user_name" label="用户" width="100" />
              <el-table-column prop="rating" label="评分" width="100">
                <template #default="scope">
                  <el-rate v-model="scope.row.rating" disabled />
                </template>
              </el-table-column>
              <el-table-column prop="content" label="评价内容" min-width="150" show-overflow-tooltip />
              <el-table-column prop="create_time" label="评价时间" width="180" />
            </el-table>
            <div class="pagination-wrapper" style="margin-top: 16px;">
              <el-pagination
                v-model:current-page="reviewsPage"
                v-model:page-size="reviewsSize"
                :page-sizes="[5, 10, 20]"
                :total="reviewsTotal"
                layout="total, sizes, prev, pager, next"
                @size-change="fetchReviews"
                @current-change="fetchReviews"
                small
              />
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="点赞统计" name="likes">
            <div v-loading="likesLoading">
              <div v-if="likesStats" style="margin-bottom: 20px;">
                <el-row :gutter="20">
                  <el-col :span="8">
                    <el-card shadow="hover">
                      <div style="text-align: center;">
                        <div style="font-size: 32px; font-weight: bold; color: #409EFF;">
                          {{ likesStats.total_likes || 0 }}
                        </div>
                        <div style="color: #999; margin-top: 8px;">总点赞数</div>
                      </div>
                    </el-card>
                  </el-col>
                  <el-col :span="8">
                    <el-card shadow="hover">
                      <div style="text-align: center;">
                        <div style="font-size: 32px; font-weight: bold; color: #67C23A;">
                          {{ likesStats.total_products || 0 }}
                        </div>
                        <div style="color: #999; margin-top: 8px;">作品数量</div>
                      </div>
                    </el-card>
                  </el-col>
                  <el-col :span="8">
                    <el-card shadow="hover">
                      <div style="text-align: center;">
                        <div style="font-size: 32px; font-weight: bold; color: #E6A23C;">
                          {{ likesStats.total_products > 0 ? (likesStats.total_likes / likesStats.total_products).toFixed(1) : 0 }}
                        </div>
                        <div style="color: #999; margin-top: 8px;">平均点赞/作品</div>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>
              </div>
              
              <div v-if="likesStats?.product_likes?.length > 0" style="margin-bottom: 20px;">
                <h4 style="margin-bottom: 12px; color: #606266;">作品点赞排行</h4>
                <el-table :data="likesStats.product_likes.slice(0, 10)" stripe size="small" style="width: 100%">
                  <el-table-column prop="product_id" label="作品ID" width="80" />
                  <el-table-column prop="product_title" label="作品标题" min-width="200" show-overflow-tooltip />
                  <el-table-column prop="like_count" label="点赞数" width="100" sortable>
                    <template #default="scope">
                      <el-tag type="warning">{{ scope.row.like_count }}</el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              
              <div>
                <h4 style="margin-bottom: 12px; color: #606266;">点赞记录</h4>
                <el-table :data="likesList" stripe style="width: 100%">
                  <el-table-column prop="id" label="ID" width="70" />
                  <el-table-column label="点赞用户" width="150">
                    <template #default="scope">
                      <div class="user-info-cell" style="display: flex; align-items: center; gap: 8px;">
                        <el-avatar :size="32" :src="scope.row.user_avatar" />
                        <span>{{ scope.row.user_nickname || '未知' }}</span>
                      </div>
                    </template>
                  </el-table-column>
                  <el-table-column prop="product_title" label="作品" min-width="150" show-overflow-tooltip />
                  <el-table-column prop="create_time" label="点赞时间" width="180" />
                </el-table>
                <div v-if="likesList.length === 0 && !likesLoading" style="margin-top: 20px;">
                  <el-empty description="暂无点赞记录" />
                </div>
                <div v-if="likesTotal > 0" class="pagination-wrapper" style="margin-top: 16px;">
                  <el-pagination
                    v-model:current-page="likesPage"
                    v-model:page-size="likesSize"
                    :page-sizes="[5, 10, 20]"
                    :total="likesTotal"
                    layout="total, sizes, prev, pager, next"
                    @size-change="fetchLikes"
                    @current-change="fetchLikes"
                    small
                  />
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, watch, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  getTeachers, 
  getTeacherDetail, 
  updateTeacher, 
  checkTeacherPendingOrders, 
  updateTeacherStatus,
  getTeacherProducts,
  getTeacherOrders,
  getTeacherReviews,
  getTeacherLikes,
  getSpecialties
} from '@/api/users'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const total = ref(0)
const specialties = ref([])

const editVisible = ref(false)
const detailVisible = ref(false)
const currentTeacher = ref(null)
const detailTeacher = ref(null)
const editFormRef = ref(null)
const detailTab = ref('info')

const productsLoading = ref(false)
const productsList = ref([])
const productsTotal = ref(0)
const productsPage = ref(1)
const productsSize = ref(10)

const ordersLoading = ref(false)
const ordersList = ref([])
const ordersTotal = ref(0)
const ordersPage = ref(1)
const ordersSize = ref(10)

const reviewsLoading = ref(false)
const reviewsList = ref([])
const reviewsTotal = ref(0)
const reviewsPage = ref(1)
const reviewsSize = ref(10)

const likesLoading = ref(false)
const likesList = ref([])
const likesTotal = ref(0)
const likesPage = ref(1)
const likesSize = ref(10)
const likesStats = ref(null)

const queryParams = reactive({
  page: 1,
  size: 10,
  id: '',
  name: '',
  specialty: '',
  verify_status: ''
})

const editForm = reactive({
  id: '',
  real_name: '',
  phone: '',
  specialties: [],
  studio_name: '',
  studio_address: '',
  experience_years: 0,
  intro: ''
})

const editRules = {
  real_name: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ],
  specialties: [
    { type: 'array', required: true, message: '请选择至少一个擅长领域', trigger: 'change' }
  ]
}

const fetchSpecialties = async () => {
  try {
    const res = await getSpecialties()
    if (res.code === 0) {
      specialties.value = res.data || []
    }
  } catch (e) {
    console.error('获取擅长领域失败:', e)
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = { ...queryParams }
    if (!params.id) delete params.id
    if (!params.name) delete params.name
    if (!params.specialty) delete params.specialty
    if (!params.verify_status) delete params.verify_status
    
    const res = await getTeachers(params)
    if (res.code === 0) {
      tableData.value = res.data.list || []
      total.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取老师列表失败:', e)
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const handleReset = () => {
  queryParams.id = ''
  queryParams.name = ''
  queryParams.specialty = ''
  queryParams.verify_status = ''
  queryParams.page = 1
  fetchData()
}

const handleView = async (row) => {
  detailTab.value = 'info'
  try {
    const res = await getTeacherDetail(row.id)
    if (res.code === 0) {
      detailTeacher.value = res.data
      detailVisible.value = true
      
      await nextTick()
      productsPage.value = 1
      ordersPage.value = 1
      reviewsPage.value = 1
      likesPage.value = 1
      likesStats.value = null
    }
  } catch (e) {
    console.error('获取老师详情失败:', e)
    ElMessage.error('获取详情失败')
  }
}

const fetchProducts = async () => {
  if (!detailTeacher.value) return
  productsLoading.value = true
  try {
    const res = await getTeacherProducts(detailTeacher.value.id, {
      page: productsPage.value,
      size: productsSize.value
    })
    if (res.code === 0) {
      productsList.value = res.data.list || []
      productsTotal.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取作品列表失败:', e)
  } finally {
    productsLoading.value = false
  }
}

const fetchOrders = async () => {
  if (!detailTeacher.value) return
  ordersLoading.value = true
  try {
    const res = await getTeacherOrders(detailTeacher.value.id, {
      page: ordersPage.value,
      size: ordersSize.value
    })
    if (res.code === 0) {
      ordersList.value = res.data.list || []
      ordersTotal.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取订单列表失败:', e)
  } finally {
    ordersLoading.value = false
  }
}

const fetchReviews = async () => {
  if (!detailTeacher.value) return
  reviewsLoading.value = true
  try {
    const res = await getTeacherReviews(detailTeacher.value.id, {
      page: reviewsPage.value,
      size: reviewsSize.value
    })
    if (res.code === 0) {
      reviewsList.value = res.data.list || []
      reviewsTotal.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取评价列表失败:', e)
  } finally {
    reviewsLoading.value = false
  }
}

const fetchLikes = async () => {
  if (!detailTeacher.value) return
  likesLoading.value = true
  try {
    const res = await getTeacherLikes(detailTeacher.value.id, {
      page: likesPage.value,
      size: likesSize.value
    })
    if (res.code === 0) {
      likesList.value = res.data.list || []
      likesTotal.value = res.data.total || 0
      likesStats.value = res.data.stats || null
    }
  } catch (e) {
    console.error('获取点赞列表失败:', e)
  } finally {
    likesLoading.value = false
  }
}

watch(detailTab, (newVal) => {
  if (newVal === 'products') {
    fetchProducts()
  } else if (newVal === 'orders') {
    fetchOrders()
  } else if (newVal === 'reviews') {
    fetchReviews()
  } else if (newVal === 'likes') {
    fetchLikes()
  }
})

const handleEdit = (row) => {
  currentTeacher.value = { ...row }
  editForm.id = row.id
  editForm.real_name = row.real_name || ''
  editForm.phone = row.phone || ''
  editForm.specialties = row.specialties || []
  editForm.studio_name = row.studio_name || ''
  editForm.studio_address = row.studio_address || ''
  editForm.experience_years = row.experience_years || 0
  editForm.intro = row.intro || row.bio || ''
  editVisible.value = true
}

const handleSaveEdit = async () => {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        const res = await updateTeacher(editForm.id, {
          real_name: editForm.real_name,
          phone: editForm.phone,
          specialties: editForm.specialties,
          studio_name: editForm.studio_name,
          studio_address: editForm.studio_address,
          experience_years: editForm.experience_years,
          intro: editForm.intro
        })
        
        if (res.code === 0) {
          ElMessage.success('更新成功')
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

const handleToggleStatus = async (row) => {
  const isActive = row.is_active
  
  if (isActive) {
    try {
      const checkRes = await checkTeacherPendingOrders(row.id)
      
      if (checkRes.code !== 0 || checkRes.data?.has_pending) {
        ElMessage.warning('该老师有未完成的订单，无法禁用')
        return
      }
    } catch (e) {
      console.error('检查订单失败:', e)
      ElMessage.error('检查订单状态失败')
      return
    }
  }
  
  const action = isActive ? '禁用' : '启用'
  const confirmText = isActive 
    ? '确定要禁用该老师账号吗？禁用后老师将无法发布作品和接单。' 
    : '确定要启用该老师账号吗？'
  
  try {
    await ElMessageBox.confirm(confirmText, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: isActive ? 'warning' : 'info'
    })
    
    submitLoading.value = true
    const res = await updateTeacherStatus(row.id, {
      is_active: !isActive
    })
    
    if (res.code === 0) {
      ElMessage.success(`${action}成功`)
      fetchData()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error(`${action}失败:`, e)
      ElMessage.error(e.response?.data?.msg || `${action}失败`)
    }
  } finally {
    submitLoading.value = false
  }
}

onMounted(() => {
  fetchSpecialties()
  fetchData()
})
</script>

<style scoped>
.filter-wrapper {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 16px;
}

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

.operation-btns {
  display: flex;
  gap: 8px;
}
</style>