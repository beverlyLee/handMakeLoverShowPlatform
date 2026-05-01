<template>
  <div class="activity-types-container">
    <div class="toolbar">
      <el-select
        v-model="filterCraftTypeId"
        placeholder="选择手工分类筛选"
        clearable
        style="width: 200px; margin-right: 10px;"
        @change="loadActivityTypes"
      >
        <el-option
          v-for="cat in categories"
          :key="cat.id"
          :label="cat.name"
          :value="cat.id"
        />
      </el-select>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增活动类型
      </el-button>
    </div>
    
    <el-table :data="activityTypes" style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="活动类型名称" width="200" />
      <el-table-column prop="craft_type_name" label="关联手工分类" width="150" />
      <el-table-column prop="description" label="描述" min-width="200" />
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
        label-width="100px"
      >
        <el-form-item label="活动类型名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入活动类型名称" />
        </el-form-item>
        
        <el-form-item label="关联手工分类" prop="craft_type_id">
          <el-select
            v-model="form.craft_type_id"
            placeholder="请选择关联的手工分类"
            clearable
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
        
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入活动类型描述"
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
  getActivityTypes,
  createActivityType,
  updateActivityType,
  deleteActivityType
} from '@/api/activityTypes'
import { getAllCategories } from '@/api/categories'

const loading = ref(false)
const submitLoading = ref(false)
const activityTypes = ref([])
const categories = ref([])
const filterCraftTypeId = ref(null)
const dialogVisible = ref(false)
const dialogTitle = ref('新增活动类型')
const isEdit = ref(false)
const formRef = ref(null)

const form = reactive({
  id: null,
  name: '',
  craft_type_id: null,
  description: '',
  sort: 0,
  status: 'active'
})

const rules = {
  name: [{ required: true, message: '请输入活动类型名称', trigger: 'blur' }]
}

const loadCategories = async () => {
  try {
    const res = await getAllCategories()
    if (res.code === 0) {
      categories.value = res.data || []
    }
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

const loadActivityTypes = async () => {
  loading.value = true
  try {
    const params = { size: 100 }
    if (filterCraftTypeId.value) {
      params.craft_type_id = filterCraftTypeId.value
    }
    const res = await getActivityTypes(params)
    if (res.code === 0) {
      activityTypes.value = res.data.list || []
    }
  } catch (error) {
    console.error('加载活动类型失败:', error)
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '新增活动类型'
  form.id = null
  form.name = ''
  form.craft_type_id = null
  form.description = ''
  form.sort = 0
  form.status = 'active'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  dialogTitle.value = '编辑活动类型'
  form.id = row.id
  form.name = row.name
  form.craft_type_id = row.craft_type_id
  form.description = row.description || ''
  form.sort = row.sort || 0
  form.status = row.status
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除活动类型"${row.name}"吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const res = await deleteActivityType(row.id)
    if (res.code === 0) {
      ElMessage.success('删除成功')
      loadActivityTypes()
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
          craft_type_id: form.craft_type_id || undefined,
          description: form.description,
          sort: form.sort,
          status: form.status
        }
        
        let res
        if (isEdit.value) {
          res = await updateActivityType(form.id, data)
        } else {
          res = await createActivityType(data)
        }
        
        if (res.code === 0) {
          ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
          dialogVisible.value = false
          loadActivityTypes()
        }
      } catch (error) {
        console.error('提交失败:', error)
      } finally {
        submitLoading.value = false
      }
    }
  })
}

onMounted(() => {
  loadCategories()
  loadActivityTypes()
})
</script>

<style scoped>
.activity-types-container {
  padding: 20px;
}

.toolbar {
  margin-bottom: 20px;
}
</style>
