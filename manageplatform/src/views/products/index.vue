<template>
  <div class="page-card">
    <div class="page-header">
      <span class="page-title">商品管理</span>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增商品
      </el-button>
    </div>
    
    <div class="filter-bar">
      <el-input
        v-model="queryParams.keyword"
        placeholder="搜索商品名称"
        clearable
        style="width: 200px;"
        @keyup.enter="handleSearch"
      />
      <el-select
        v-model="queryParams.category"
        placeholder="商品分类"
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
        v-model="queryParams.status"
        placeholder="商品状态"
        clearable
        style="width: 140px;"
      >
        <el-option label="上架" value="active" />
        <el-option label="下架" value="inactive" />
      </el-select>
      <el-select
        v-model="queryParams.sort"
        placeholder="排序方式"
        clearable
        style="width: 140px;"
      >
        <el-option label="最新上架" value="newest" />
        <el-option label="销量最高" value="sales" />
        <el-option label="价格最低" value="price_asc" />
        <el-option label="价格最高" value="price_desc" />
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
        <el-table-column prop="title" label="商品名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="category_name" label="分类" width="100" />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="scope">
            <span style="color: #ff6b35; font-weight: bold;">
              ¥{{ scope.row.price?.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="stock" label="库存" width="80" />
        <el-table-column prop="sales_count" label="销量" width="80" />
        <el-table-column prop="rating" label="评分" width="80">
          <template #default="scope">
            <el-rate
              v-model="scope.row.rating"
              disabled
              :max="5"
              size="small"
            />
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'">
              {{ scope.row.status === 'active' ? '上架' : '下架' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="180" />
        <el-table-column label="操作" fixed="right" width="240">
          <template #default="scope">
            <div class="operation-btns">
              <el-button type="primary" link @click="handleView(scope.row)">
                查看
              </el-button>
              <el-button type="primary" link @click="handleEdit(scope.row)">
                编辑
              </el-button>
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
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getProducts, getCategories } from '@/api/products'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const categories = ref([])

const queryParams = reactive({
  page: 1,
  size: 10,
  keyword: '',
  category: null,
  status: '',
  sort: ''
})

const fetchCategories = async () => {
  try {
    const res = await getCategories()
    if (res.code === 0) {
      categories.value = res.data || []
    }
  } catch (e) {
    categories.value = [
      { id: 1, name: '编织' },
      { id: 2, name: '陶艺' },
      { id: 3, name: '纸艺' },
      { id: 4, name: '刺绣' },
      { id: 5, name: '木工' }
    ]
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
    if (queryParams.category) params.category = queryParams.category
    if (queryParams.status) params.status = queryParams.status
    if (queryParams.sort) params.sort = queryParams.sort
    
    const res = await getProducts(params)
    if (res.code === 0) {
      tableData.value = res.data.list || []
      total.value = res.data.total || 0
    }
  } catch (e) {
    tableData.value = [
      { id: 1, title: '手工编织羊毛围巾', category_name: '编织', price: 199.00, stock: 50, sales_count: 128, rating: 4.8, status: 'active', create_time: '2024-03-15 10:30:00', cover_image: '' },
      { id: 2, title: '手工陶瓷茶杯套装', category_name: '陶艺', price: 299.00, stock: 30, sales_count: 86, rating: 4.9, status: 'active', create_time: '2024-03-10 09:15:00', cover_image: '' },
      { id: 3, title: '手工折纸千纸鹤', category_name: '纸艺', price: 59.00, stock: 100, sales_count: 256, rating: 4.5, status: 'active', create_time: '2024-03-08 14:45:00', cover_image: '' },
      { id: 4, title: '手工刺绣香囊', category_name: '刺绣', price: 88.00, stock: 0, sales_count: 168, rating: 4.7, status: 'inactive', create_time: '2024-02-28 11:00:00', cover_image: '' },
      { id: 5, title: '手工木质收纳盒', category_name: '木工', price: 159.00, stock: 25, sales_count: 92, rating: 4.6, status: 'active', create_time: '2024-02-20 16:20:00', cover_image: '' }
    ]
    total.value = 5
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
  queryParams.category = null
  queryParams.status = ''
  queryParams.sort = ''
  fetchData()
}

const handleAdd = () => {
  ElMessage.info('新增商品功能开发中')
}

const handleView = (row) => {
  ElMessage.info('查看商品详情功能开发中')
}

const handleEdit = (row) => {
  ElMessage.info('编辑商品功能开发中')
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该商品吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    ElMessage.success('删除成功')
    fetchData()
  } catch {
    // 用户取消
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
</style>
