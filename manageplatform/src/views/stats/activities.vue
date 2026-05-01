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
      <el-col :span="5">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">活动总数</div>
            <div class="stat-value">{{ statsData.summary?.total_activities || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">周期新增</div>
            <div class="stat-value">{{ statsData.summary?.period_activities || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">总报名数</div>
            <div class="stat-value">{{ statsData.summary?.total_registrations || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">周期报名</div>
            <div class="stat-value">{{ statsData.summary?.period_registrations || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">总浏览量</div>
            <div class="stat-value">{{ statsData.summary?.total_views || 0 }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>活动趋势</span>
          </template>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>手工类型分布</span>
          </template>
          <div ref="craftTypeChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>活动类型分布</span>
          </template>
          <div ref="activityTypeChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>热门活动排名（按报名数）</span>
          </template>
          <el-table :data="statsData.top_activities || []" style="width: 100%">
            <el-table-column label="排名" width="80">
              <template #default="{ $index }">
                <el-tag v-if="$index <= 2" :type="getRankType($index + 1)" size="small">
                  {{ getRankLabel($index + 1) }}
                </el-tag>
                <span v-else>{{ $index + 1 }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="活动名称" min-width="200" />
            <el-table-column prop="teacher_name" label="老师" width="120" />
            <el-table-column prop="craft_type" label="手工类型" width="100" />
            <el-table-column prop="activity_type" label="活动类型" width="100" />
            <el-table-column prop="price" label="价格" width="100">
              <template #default="{ row }">
                ¥{{ row.price || 0 }}
              </template>
            </el-table-column>
            <el-table-column prop="view_count" label="浏览量" width="100">
              <template #default="{ row }">
                <span class="highlight">{{ row.view_count || 0 }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="registration_count" label="报名数" width="100">
              <template #default="{ row }">
                <span class="highlight">{{ row.registration_count || 0 }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="max_participants" label="名额" width="100">
              <template #default="{ row }">
                <span :class="getEnrollmentClass(row)">
                  {{ row.registration_count || 0 }}/{{ row.max_participants || '不限' }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { getActivityStats, exportActivityStats } from '@/api/stats'
import { exportStatsToExcel } from '@/utils/export'

const trendChartRef = ref(null)
const craftTypeChartRef = ref(null)
const activityTypeChartRef = ref(null)
let trendChart = null
let craftTypeChart = null
let activityTypeChart = null

const period = ref('week')
const dateRange = ref([])
const loading = ref(false)

const statsData = reactive({
  summary: {
    total_activities: 0,
    period_activities: 0,
    total_registrations: 0,
    period_registrations: 0,
    total_views: 0
  },
  craft_types: {},
  activity_types: {},
  top_activities: [],
  daily_data: []
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

const getEnrollmentClass = (row) => {
  if (!row.max_participants) return ''
  const ratio = (row.registration_count || 0) / row.max_participants
  if (ratio >= 1) return 'enrollment-full'
  if (ratio >= 0.8) return 'enrollment-warning'
  return ''
}

const initCharts = () => {
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
  }
  if (craftTypeChartRef.value) {
    craftTypeChart = echarts.init(craftTypeChartRef.value)
  }
  if (activityTypeChartRef.value) {
    activityTypeChart = echarts.init(activityTypeChartRef.value)
  }
}

const generatePieData = (counts) => {
  const data = []
  for (const [type, count] of Object.entries(counts || {})) {
    if (count === 0) continue
    data.push({
      value: count,
      name: type
    })
  }
  return data.sort((a, b) => b.value - a.value)
}

const updateCharts = () => {
  if (trendChart && statsData.daily_data?.length > 0) {
    const option = {
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: ['新增活动', '报名数']
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
          name: '新增活动',
          type: 'line',
          smooth: true,
          data: statsData.daily_data.map(d => d.new_activities || 0),
          itemStyle: { color: '#409eff' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
            ])
          }
        },
        {
          name: '报名数',
          type: 'line',
          smooth: true,
          data: statsData.daily_data.map(d => d.registrations || 0),
          itemStyle: { color: '#e6a23c' },
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
  
  const craftTypeData = generatePieData(statsData.craft_types)
  if (craftTypeChart && craftTypeData.length > 0) {
    const option = {
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
          data: craftTypeData
        }
      ]
    }
    craftTypeChart.setOption(option)
  }
  
  const activityTypeData = generatePieData(statsData.activity_types)
  if (activityTypeChart && activityTypeData.length > 0) {
    const option = {
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
          data: activityTypeData
        }
      ]
    }
    activityTypeChart.setOption(option)
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
    
    const res = await getActivityStats(params)
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
    
    const res = await exportActivityStats(params)
    if (res.code === 0) {
      exportStatsToExcel(res.data, `activity_stats_${new Date().toISOString().split('T')[0]}.xlsx`)
      ElMessage.success('导出成功')
    }
  } catch (error) {
    console.error('导出失败:', error)
  }
}

const handleResize = () => {
  trendChart?.resize()
  craftTypeChart?.resize()
  activityTypeChart?.resize()
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  trendChart?.dispose()
  craftTypeChart?.dispose()
  activityTypeChart?.dispose()
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

.enrollment-full {
  color: #f56c6c;
  font-weight: bold;
}

.enrollment-warning {
  color: #e6a23c;
  font-weight: 500;
}

.chart-container {
  height: 400px;
  width: 100%;
}
</style>
