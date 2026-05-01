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
      <el-col :span="4">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">上架作品</div>
            <div class="stat-value">{{ statsData.summary?.total_active || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">下架作品</div>
            <div class="stat-value">{{ statsData.summary?.total_inactive || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">周期新增</div>
            <div class="stat-value">{{ statsData.summary?.period_new || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">总点赞数</div>
            <div class="stat-value">{{ statsData.summary?.total_likes || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">总评价数</div>
            <div class="stat-value">{{ statsData.summary?.total_reviews || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">分类数量</div>
            <div class="stat-value">{{ (statsData.categories || []).length }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>作品增长趋势</span>
          </template>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>分类作品分布</span>
          </template>
          <div ref="categoryChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>分类点赞排名</span>
          </template>
          <el-table :data="categoryTableData" style="width: 100%" max-height="350">
            <el-table-column prop="rank" label="排名" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.rank <= 3" :type="getRankType(row.rank)" size="small">
                  {{ getRankLabel(row.rank) }}
                </el-tag>
                <span v-else>{{ row.rank }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="name" label="分类名称" />
            <el-table-column prop="product_count" label="作品数" width="100" />
            <el-table-column prop="total_likes" label="点赞数" width="100">
              <template #default="{ row }">
                <span class="highlight">{{ row.total_likes }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="total_reviews" label="评价数" width="100" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { getProductStats, exportProductStats } from '@/api/stats'
import { exportStatsToExcel } from '@/utils/export'

const trendChartRef = ref(null)
const categoryChartRef = ref(null)
let trendChart = null
let categoryChart = null

const period = ref('week')
const dateRange = ref([])
const loading = ref(false)

const statsData = reactive({
  summary: {
    total_active: 0,
    total_inactive: 0,
    period_new: 0,
    total_likes: 0,
    total_reviews: 0
  },
  categories: [],
  daily_data: []
})

const categoryTableData = computed(() => {
  const cats = statsData.categories || []
  const sorted = [...cats].sort((a, b) => (b.total_likes || 0) - (a.total_likes || 0))
  return sorted.map((cat, index) => ({
    ...cat,
    rank: index + 1
  }))
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
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
  }
  if (categoryChartRef.value) {
    categoryChart = echarts.init(categoryChartRef.value)
  }
}

const updateCharts = () => {
  if (trendChart && statsData.daily_data?.length > 0) {
    const option = {
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: ['新增作品', '销量']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: statsData.daily_data.map(d => d.date)
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '新增作品',
          type: 'line',
          smooth: true,
          data: statsData.daily_data.map(d => d.new_products || 0),
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
              { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
            ])
          }
        },
        {
          name: '销量',
          type: 'line',
          smooth: true,
          data: statsData.daily_data.map(d => d.sales_volume || 0),
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(230, 162, 60, 0.3)' },
              { offset: 1, color: 'rgba(230, 162, 60, 0.05)' }
            ])
          }
        }
      ]
    }
    trendChart.setOption(option)
  }
  
  if (categoryChart && (statsData.categories || []).length > 0) {
    const cats = statsData.categories || []
    const categoryOption = {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: true,
            formatter: '{b}: {c}'
          },
          data: cats.map(cat => ({
            value: cat.product_count || 0,
            name: cat.name
          }))
        }
      ]
    }
    categoryChart.setOption(categoryOption)
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
    
    const res = await getProductStats(params)
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
    
    const res = await exportProductStats(params)
    if (res.code === 0) {
      exportStatsToExcel(res.data, `product_stats_${new Date().toISOString().split('T')[0]}.xlsx`)
      ElMessage.success('导出成功')
    }
  } catch (error) {
    console.error('导出失败:', error)
  }
}

const handleResize = () => {
  trendChart?.resize()
  categoryChart?.resize()
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  trendChart?.dispose()
  categoryChart?.dispose()
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

.highlight {
  color: #409eff;
  font-weight: 500;
}

.chart-container {
  height: 400px;
  width: 100%;
}
</style>
