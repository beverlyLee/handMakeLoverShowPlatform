<template>
  <div class="page-card">
    <div class="page-header">
      <span class="page-title">活动管理</span>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增活动
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
        v-model="queryParams.craft_type"
        placeholder="手作类型"
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
        v-model="queryParams.status"
        placeholder="活动状态"
        clearable
        style="width: 140px;"
      >
        <el-option label="进行中" value="active" />
        <el-option label="已结束" value="inactive" />
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
        <el-table-column prop="title" label="活动名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="craft_type" label="手作类型" width="100" />
        <el-table-column prop="activity_type" label="活动类型" width="100" />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="scope">
            <span style="color: #ff6b35; font-weight: bold;">
              ¥{{ scope.row.price?.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="报名情况" width="120">
          <template #default="scope">
            <span>{{ scope.row.current_participants || 0 }} / {{ scope.row.max_participants || 999 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="地点" width="120" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'">
              {{ scope.row.status === 'active' ? '进行中' : '已结束' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="160" />
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="scope">
            <div class="operation-btns">
              <el-button type="primary" link @click="handleView(scope.row)">
                详情
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
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getActivities, getActivityTypes } from '@/api/activities'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const craftTypes = ref([])

const queryParams = reactive({
  page: 1,
  size: 10,
  keyword: '',
  craft_type: '',
  status: ''
})

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
    if (queryParams.craft_type) params.craft_type = queryParams.craft_type
    if (queryParams.status) params.status = queryParams.status
    
    const res = await getActivities(params)
    if (res.code === 0) {
      tableData.value = res.data.list || []
      total.value = res.data.total || 0
    }
  } catch (e) {
    tableData.value = [
      {
        id: 1,
        title: '周末编织工坊 - 围巾制作',
        craft_type: '编织',
        activity_type: '线下课程',
        price: 199.00,
        current_participants: 8,
        max_participants: 15,
        location: '深圳市南山区手作空间',
        status: 'active',
        start_time: '2024-05-10 14:00:00',
        cover_image: ''
      },
      {
        id: 2,
        title: '陶艺体验课 - 茶杯制作',
        craft_type: '陶艺',
        activity_type: '线下课程',
        price: 299.00,
        current_participants: 5,
        max_participants: 10,
        location: '广州市天河区陶艺工作室',
        status: 'active',
        start_time: '2024-05-12 10:00:00',
        cover_image: ''
      },
      {
        id: 3,
        title: '纸艺DIY - 立体贺卡',
        craft_type: '纸艺',
        activity_type: '线上直播',
        price: 59.00,
        current_participants: 25,
        max_participants: 50,
        location: '线上直播',
        status: 'inactive',
        start_time: '2024-04-20 19:00:00',
        cover_image: ''
      }
    ]
    total.value = 3
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
  queryParams.craft_type = ''
  queryParams.status = ''
  fetchData()
}

const handleAdd = () => {
  ElMessage.info('新增活动功能开发中')
}

const handleView = (row) => {
  ElMessage.info('查看活动详情功能开发中')
}

const handleEdit = (row) => {
  ElMessage.info('编辑活动功能开发中')
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
</style>
