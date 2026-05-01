<template>
  <div class="categories-container">
    <div class="toolbar">
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增分类
      </el-button>
    </div>
    
    <el-table :data="categories" style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="分类名称" width="200" />
      <el-table-column label="图标" width="100">
        <template #default="{ row }">
          <el-image
            v-if="row.icon"
            :src="row.icon"
            :preview-src-list="[row.icon]"
            fit="cover"
            style="width: 40px; height: 40px; border-radius: 4px;"
          />
          <span v-else class="no-icon">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200" />
      <el-table-column prop="product_count" label="作品数" width="100" />
      <el-table-column prop="activity_count" label="活动数" width="100" />
      <el-table-column prop="sort" label="排序" width="100" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
            {{ row.status === 'active' ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
          <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入分类名称" />
        </el-form-item>
        
        <el-form-item label="图标">
          <el-upload
            class="avatar-uploader"
            :action="uploadUrl"
            :headers="uploadHeaders"
            :show-file-list="false"
            :on-success="handleUploadSuccess"
            :before-upload="beforeUpload"
          >
            <el-image v-if="form.icon" :src="form.icon" class="avatar" fit="cover" />
            <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">点击上传图标（建议正方形图片）</div>
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入分类描述"
          />
        </el-form-item>
        
        <el-form-item label="排序" prop="sort">
          <el-input-number v-model="form.sort" :min="0" />
        </el-form-item>
        
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="inactive">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getCategories,
  createCategory,
  updateCategory,
  deleteCategory
} from '@/api/categories'

const loading = ref(false)
const submitLoading = ref(false)
const categories = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增分类')
const isEdit = ref(false)
const formRef = ref(null)

const form = reactive({
  id: null,
  name: '',
  icon: '',
  description: '',
  sort: 0,
  status: 'active'
})

const rules = {
  name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }]
}

const uploadUrl = '/api/upload/image'
const uploadHeaders = {
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`
}

const loadCategories = async () => {
  loading.value = true
  try {
    const res = await getCategories({ size: 100 })
    if (res.code === 0) {
      categories.value = res.data.list || []
    }
  } catch (error) {
    console.error('加载分类失败:', error)
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '新增分类'
  form.id = null
  form.name = ''
  form.icon = ''
  form.description = ''
  form.sort = 0
  form.status = 'active'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  dialogTitle.value = '编辑分类'
  form.id = row.id
  form.name = row.name
  form.icon = row.icon || ''
  form.description = row.description || ''
  form.sort = row.sort || 0
  form.status = row.status
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除分类"${row.name}"吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const res = await deleteCategory(row.id)
    if (res.code === 0) {
      ElMessage.success('删除成功')
      loadCategories()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        const data = {
          name: form.name,
          icon: form.icon,
          description: form.description,
          sort: form.sort,
          status: form.status
        }
        
        let res
        if (isEdit.value) {
          res = await updateCategory(form.id, data)
        } else {
          res = await createCategory(data)
        }
        
        if (res.code === 0) {
          ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
          dialogVisible.value = false
          loadCategories()
        }
      } catch (error) {
        console.error('提交失败:', error)
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  
  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
    return false
  }
  return true
}

const handleUploadSuccess = (response) => {
  if (response.code === 0 || response.url) {
    form.icon = response.url || response.data?.url
    ElMessage.success('上传成功')
  } else {
    ElMessage.error('上传失败')
  }
}

onMounted(() => {
  loadCategories()
})
</script>

<style scoped>
.categories-container {
  padding: 20px;
}

.toolbar {
  margin-bottom: 20px;
}

.no-icon {
  color: #999;
}

.avatar-uploader {
  text-align: center;
}

.avatar {
  width: 80px;
  height: 80px;
  display: block;
  border-radius: 4px;
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 80px;
  height: 80px;
  line-height: 80px;
  text-align: center;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  transition: 0.3s;
}

.avatar-uploader-icon:hover {
  border-color: #409eff;
  color: #409eff;
}

.upload-tip {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}
</style>
