<template>
  <div class="stats-container">
    <div class="toolbar">
      <el-radio-group v-model="period" @change="loadStats">
        <el-radio-button value="day">日</el-radio-button>
        <el-radio-button value="week">周</el-radio-button>
        <el-radio-button value="month">月</el-radio-button>
        <el-radio-button value="quarter">季度</el-radio-button>
        <el-radio-button value="custom">自定义</el-radio-button>
      </el-radio-group>
      
      <el-date-picker
        v-if="period === 'custom'"
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        :disabled-date="disabledDate"
        style="margin-left: 10px;"
      />
      
      <el-button 
        v-if="period === 'custom'" 
        type="primary" 
        @click="loadStats" 
        style="margin-left: 10px;"
      >
        确定
      </el-button>
      
      <el-button type="primary" @click="handleExport" style="margin-left: 10px;">
        导出Excel
      </el-button>
    </div>
    
    <el-row :gutter="20" class="stats-summary">
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">老师总数</div>
            <div class="stat-value">{{ statsData.summary?.total_teachers || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">已认证老师</div>
            <div class="stat-value">{{ statsData.summary?.verified_teachers || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">周期订单数</div>
            <div class="stat-value">{{ statsData.summary?.period_orders || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">周期收入</div>
            <div class="stat-value">¥{{ statsData.summary?.period_revenue || 0 }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>老师排名榜</span>
          </template>
          
          <el-table :data="statsData.ranking || []" style="width: 100%">
            <el-table-column label="排名" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.rank <= 3" :type="getRankType(row.rank)" size="large">
                  {{ getRankLabel(row.rank) }}
                </el-tag>
                <span v-else>{{ row.rank }}</span>
              </template>
            </el-table-column>
            <el-table-column label="老师" width="200">
              <template #default="{ row }">
                <div class="teacher-info">
                  <el-avatar :size="40" :src="row.avatar">
                    <el-icon><User /></el-icon>
                  </el-avatar>
                  <div class="teacher-detail">
                    <div class="teacher-name">{{ row.nickname }}</div>
                    <div class="teacher-real-name" v-if="row.real_name">{{ row.real_name }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="rating" label="评分" width="100">
              <template #default="{ row }">
                <el-rate v-model="row.rating" disabled :max="5" show-text />
              </template>
            </el-table-column>
            <el-table-column prop="follower_count" label="粉丝数" width="100" />
            <el-table-column prop="period_orders" label="周期订单" width="100">
              <template #default="{ row }">
                <span class="highlight">{{ row.period_orders }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="period_revenue" label="周期收入" width="120">
              <template #default="{ row }">
                <span class="highlight">¥{{ row.period_revenue }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="period_products" label="周期作品" width="100" />
            <el-table-column prop="total_products" label="总作品" width="100" />
            <el-table-column prop="total_orders" label="总订单" width="100" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>订单分布</span>
          </template>
          <div ref="orderChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>收入分布</span>
          </template>
          <div ref="revenueChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { getTeacherStats, exportTeacherStats } from '@/api/stats'
import { exportStatsToExcel } from '@/utils/export'

const orderChartRef = ref(null)
const revenueChartRef = ref(null)
let orderChart = null
let revenueChart = null

const period = ref('week')
const dateRange = ref([])
const loading = ref(false)

const statsData = reactive({
  summary: {
    total_teachers: 0,
    verified_teachers: 0,
    period_orders: 0,
    period_revenue: 0
  },
  ranking: []
})

const disabledDate = (time) => {
  return time.getTime() > Date.now()
}

const getRankType = (rank) => {
  if (rank === 1) return 'danger'
  if (rank === 2) return 'warning'
  if (rank === 3) return 'success'
  return 'info'
}

const getRankLabel = (rank) => {
  if (rank === 1) return '冠军'
  if (rank === 2) return '亚军'
  if (rank === 3) return '季军'
  return rank
}

const initCharts = () => {
  if (orderChartRef.value) {
    orderChart = echarts.init(orderChartRef.value)
  }
  if (revenueChartRef.value) {
    revenueChart = echarts.init(revenueChartRef.value)
  }
}

const updateCharts = () => {
  const top10 = statsData.ranking?.slice(0, 10) || []
  
  if (orderChart && top10.length > 0) {
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: top10.map(t => t.nickname || t.real_name),
        axisLabel: {
          rotate: 30
        }
      },
      yAxis: {
        type: 'value',
        name: '订单数'
      },
      series: [
        {
          name: '周期订单',
          type: 'bar',
          data: top10.map(t => t.period_orders || 0),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#83bff6' },
              { offset: 0.5, color: '#188df0' },
              { offset: 1, color: '#188df0' }
            ])
          }
        }
      ]
    }
    orderChart.setOption(option)
  }
  
  if (revenueChart && top10.length > 0) {
    const revenueOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: top10.map(t => t.nickname || t.real_name),
        axisLabel: {
          rotate: 30
        }
      },
      yAxis: {
        type: 'value',
        name: '收入(元)'
      },
      series: [
        {
          name: '周期收入',
          type: 'bar',
          data: top10.map(t => t.period_revenue || 0),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#67e0e3' },
              { offset: 0.5, color: '#36cfc9' },
              { offset: 1, color: '#36cfc9' }
            ])
          }
        }
      ]
    }
    revenueChart.setOption(revenueOption)
  }
}

const loadStats = async () => {
  loading.value = true
  try {
    const params = { period: period.value }
    if (period.value === 'custom' && dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    
    const res = await getTeacherStats(params)
    if (res.code === 0) {
      Object.assign(statsData, res.data)
      nextTick(() => {
        initCharts()
        updateCharts()
      })
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  } finally {
    loading.value = false
  }
}

const handleExport = async () => {
  try {
    const params = { period: period.value }
    if (period.value === 'custom' && dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    
    const res = await exportTeacherStats(params)
    if (res.code === 0) {
      exportStatsToExcel(res.data, `teacher_stats_${new Date().toISOString().split('T')[0]}.xlsx`)
      ElMessage.success('导出成功')
    }
  } catch (error) {
    console.error('导出失败:', error)
  }
}

const handleResize = () => {
  orderChart?.resize()
  revenueChart?.resize()
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  orderChart?.dispose()
  revenueChart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.stats-container {
  padding: 20px;
}

.toolbar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.stats-summary {
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  color: #909399;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  color: #303133;
  font-size: 28px;
  font-weight: bold;
}

.teacher-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.teacher-detail {
  text-align: left;
}

.teacher-name {
  font-weight: 500;
  color: #303133;
}

.teacher-real-name {
  font-size: 12px;
  color: #909399;
}

.highlight {
  color: #409eff;
  font-weight: 500;
}

.chart-container {
  height: 400px;
  width: 100%;
}
</style>
