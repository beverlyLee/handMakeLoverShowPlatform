<template>
  <div class="page-card">
    <div class="page-header">
      <span class="page-title">作品管理</span>
    </div>
    
    <div class="filter-bar">
      <el-input
        v-model="queryParams.keyword"
        placeholder="搜索作品名称"
        clearable
        style="width: 200px;"
        @keyup.enter="handleSearch"
      />
      <el-input
        v-model="queryParams.product_id"
        placeholder="作品ID"
        clearable
        style="width: 120px;"
        @keyup.enter="handleSearch"
      />
      <el-input
        v-model="queryParams.teacher_id"
        placeholder="老师ID"
        clearable
        style="width: 120px;"
        @keyup.enter="handleSearch"
      />
      <el-select
        v-model="queryParams.category"
        placeholder="作品分类"
        clearable
        style="width: 140px;"
      >
        <el-option
          v-for="cat in categories"
          :key="cat.id"
          :label="cat.name"
          :value="cat.id"
        />
      </el-select>
      <el-select
        v-model="queryParams.verify_status"
        placeholder="审核状态"
        clearable
        style="width: 120px;"
      >
        <el-option label="待审核" value="pending" />
        <el-option label="已通过" value="approved" />
        <el-option label="已拒绝" value="rejected" />
      </el-select>
      <el-select
        v-model="queryParams.is_online"
        placeholder="上下架状态"
        clearable
        style="width: 120px;"
      >
        <el-option label="已上架" :value="true" />
        <el-option label="已下架" :value="false" />
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
        <el-table-column prop="id" label="作品ID" width="80" />
        <el-table-column prop="teacher_name" label="老师昵称" width="100">
          <template #default="scope">
            <span>{{ scope.row.teacher_name || '未知' }}</span>
          </template>
        </el-table-column>
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
        <el-table-column prop="title" label="作品名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="category_name" label="种类" width="100" />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="scope">
            <span style="color: #ff6b35; font-weight: bold;">
              ¥{{ scope.row.price?.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="verify_status" label="审核状态" width="100">
          <template #default="scope">
            <el-tag :type="getVerifyTagType(scope.row.verify_status)">
              {{ getVerifyStatusText(scope.row.verify_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_online" label="上下架状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_online ? 'success' : 'info'">
              {{ scope.row.is_online ? '已上架' : '已下架' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" fixed="right" width="280">
          <template #default="scope">
            <div class="operation-btns">
              <el-button type="primary" link @click="handleView(scope.row)">
                查看
              </el-button>
              <template v-if="scope.row.verify_status === 'approved'">
                <el-button
                  :type="scope.row.is_online ? 'warning' : 'success'"
                  link
                  @click="handleOnlineToggle(scope.row)"
                >
                  {{ scope.row.is_online ? '下架' : '上架' }}
                </el-button>
                <el-button
                  type="primary"
                  link
                  @click="handleEdit(scope.row)"
                  :disabled="!scope.row.is_online"
                >
                  编辑
                </el-button>
              </template>
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
    
    <el-dialog v-model="viewVisible" title="作品详情" width="800px">
      <div v-if="currentProduct">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="作品ID">{{ currentProduct.id }}</el-descriptions-item>
          <el-descriptions-item label="老师ID">{{ currentProduct.teacher_id }}</el-descriptions-item>
          <el-descriptions-item label="作品名称">{{ currentProduct.title }}</el-descriptions-item>
          <el-descriptions-item label="价格">¥{{ currentProduct.price?.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="种类">{{ currentProduct.category_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="库存">{{ currentProduct.stock || 0 }}</el-descriptions-item>
          <el-descriptions-item label="审核状态">
            <el-tag :type="getVerifyTagType(currentProduct.verify_status)">
              {{ getVerifyStatusText(currentProduct.verify_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="上下架状态">
            <el-tag :type="currentProduct.is_online ? 'success' : 'info'">
              {{ currentProduct.is_online ? '已上架' : '已下架' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ currentProduct.created_at }}</el-descriptions-item>
          <el-descriptions-item label="审核时间">{{ currentProduct.verify_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="拒绝理由" :span="2">
            {{ currentProduct.reject_reason || '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="作品描述" :span="2">
            <div class="description-text">{{ currentProduct.description || '暂无描述' }}</div>
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="section-title" style="margin-top: 20px; margin-bottom: 16px;">
          <el-icon><Picture /></el-icon> 作品图片（共{{ currentProduct.images?.length || 0 }}张）
        </div>
        
        <div v-if="currentProduct.images && currentProduct.images.length > 0" class="images-grid">
          <el-image
            v-for="(img, index) in currentProduct.images"
            :key="index"
            :src="img"
            :preview-src-list="currentProduct.images"
            :initial-index="index"
            fit="cover"
            class="image-item"
          >
            <template #error>
              <div class="image-slot">
                <el-icon :size="24"><Picture /></el-icon>
              </div>
            </template>
          </el-image>
        </div>
        <el-empty v-else description="暂无图片" />
      </div>
    </el-dialog>
    
    <el-dialog v-model="editVisible" title="编辑作品" width="700px" :close-on-click-modal="false">
      <el-form
        :model="editForm"
        :rules="editRules"
        ref="editFormRef"
        label-width="100px"
      >
        <el-form-item label="作品名称" prop="title">
          <el-input v-model="editForm.title" placeholder="请输入作品名称" />
        </el-form-item>
        <el-form-item label="价格" prop="price">
          <el-input-number
            v-model="editForm.price"
            :min="0.01"
            :precision="2"
            placeholder="请输入价格"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="种类" prop="category_id">
          <el-select
            v-model="editForm.category_id"
            placeholder="请选择种类"
            style="width: 100%;"
          >
            <el-option
              v-for="cat in categories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="作品描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入作品描述"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="轮播图" prop="images">
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
                @click="removeImage(index)"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <el-upload
              class="image-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleUploadSuccess"
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
          <div class="form-tip">提示：点击添加图片可上传新图片</div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getProducts,
  getCategories,
  setProductOnline,
  adminEditProduct,
  adminDeleteProduct
} from '@/api/products'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const total = ref(0)
const categories = ref([])
const viewVisible = ref(false)
const editVisible = ref(false)
const currentProduct = ref(null)
const editFormRef = ref(null)

const queryParams = reactive({
  page: 1,
  size: 10,
  keyword: '',
  product_id: '',
  teacher_id: '',
  category: null,
  verify_status: '',
  is_online: null
})

const editForm = reactive({
  id: null,
  title: '',
  price: 0,
  category_id: null,
  description: '',
  images: []
})

const editRules = {
  title: [
    { required: true, message: '请输入作品名称', trigger: 'blur' }
  ],
  price: [
    { required: true, message: '请输入价格', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value <= 0) {
          callback(new Error('价格必须大于0'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const getVerifyStatusText = (status) => {
  const statusMap = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝'
  }
  return statusMap[status] || '未知'
}

const getVerifyTagType = (status) => {
  const typeMap = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return typeMap[status] || 'info'
}

const fetchCategories = async () => {
  try {
    const res = await getCategories()
    if (res.code === 0) {
      categories.value = res.data || []
    }
  } catch (e) {
    console.error('获取分类失败:', e)
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
    if (queryParams.product_id) params.product_id = queryParams.product_id
    if (queryParams.teacher_id) params.teacher_id = queryParams.teacher_id
    if (queryParams.category) params.category = queryParams.category
    if (queryParams.verify_status) params.verify_status = queryParams.verify_status
    if (queryParams.is_online !== null) params.is_online = queryParams.is_online
    
    const res = await getProducts(params)
    if (res.code === 0) {
      tableData.value = res.data.list || []
      total.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取作品列表失败:', e)
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
  queryParams.product_id = ''
  queryParams.teacher_id = ''
  queryParams.category = null
  queryParams.verify_status = ''
  queryParams.is_online = null
  fetchData()
}

const handleView = (row) => {
  currentProduct.value = { ...row }
  viewVisible.value = true
}

const handleOnlineToggle = async (row) => {
  const isOnline = row.is_online
  const actionText = isOnline ? '下架' : '上架'
  const message = isOnline
    ? '确定要下架该作品吗？下架后用户将无法在小程序中看到该作品。'
    : '确定要上架该作品吗？上架后用户将能在小程序中看到该作品。'
  
  try {
    await ElMessageBox.confirm(message, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await setProductOnline(row.id, !isOnline)
    if (res.code === 0) {
      ElMessage.success(`作品已${actionText}`)
      fetchData()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error(`${actionText}失败:`, e)
      ElMessage.error(e.response?.data?.msg || '操作失败')
    }
  }
}

const handleEdit = (row) => {
  if (!row.is_online) {
    ElMessage.warning('仅已上架的作品才能编辑')
    return
  }
  
  editForm.id = row.id
  editForm.title = row.title
  editForm.price = row.price
  editForm.category_id = row.category_id
  editForm.description = row.description
  editForm.images = row.images ? [...row.images] : []
  editVisible.value = true
}

const removeImage = (index) => {
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
          price: editForm.price,
          description: editForm.description,
          images: editForm.images
        }
        if (editForm.category_id) {
          data.category_id = editForm.category_id
        }
        
        const res = await adminEditProduct(editForm.id, data)
        if (res.code === 0) {
          ElMessage.success('作品更新成功')
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
      '确定要删除该作品吗？删除前将校验是否有关联订单、评价、点赞，有关联则无法删除。此操作不可恢复。',
      '警告',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const res = await adminDeleteProduct(row.id)
    if (res.code === 0) {
      ElMessage.success('作品已删除')
      fetchData()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除失败:', e)
      ElMessage.error(e.response?.data?.msg || '删除失败')
    }
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

const handleUploadSuccess = (response) => {
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
  fetchCategories()
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

.description-text {
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.6;
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

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.image-item {
  width: 100%;
  height: 120px;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid #eee;
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
</style>
