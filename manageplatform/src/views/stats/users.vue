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
            <div class="stat-label">总用户数</div>
            <div class="stat-value">{{ statsData.total || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">周期新增</div>
            <div class="stat-value">{{ statsData.period_total || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">活跃用户</div>
            <div class="stat-value">{{ statsData.active_users || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">老师总数</div>
            <div class="stat-value">{{ statsData.teachers?.total || 0 }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>用户增长趋势</span>
          </template>
          <div ref="chartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>用户角色分布</span>
          </template>
          <div ref="roleChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>老师认证情况</span>
          </template>
          <div ref="teacherChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { getUserStats, exportUserStats } from '@/api/stats'
import { exportStatsToExcel } from '@/utils/export'

const chartRef = ref(null)
const roleChartRef = ref(null)
const teacherChartRef = ref(null)
let chart = null
let roleChart = null
let teacherChart = null

const period = ref('week')
const dateRange = ref([])
const loading = ref(false)

const statsData = reactive({
  total: 0,
  period_total: 0,
  active_users: 0,
  teachers: { total: 0, verified: 0 },
  daily_data: [],
  period_roles: { customer: 0, teacher: 0 }
})

const disabledDate = (time) => {
  return time.getTime() > Date.now()
}

const initCharts = () => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
  }
  if (roleChartRef.value) {
    roleChart = echarts.init(roleChartRef.value)
  }
  if (teacherChartRef.value) {
    teacherChart = echarts.init(teacherChartRef.value)
  }
}

const updateCharts = () => {
  if (chart && statsData.daily_data.length > 0) {
    const option = {
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: ['新增用户', '活跃用户']
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
          name: '新增用户',
          type: 'line',
          smooth: true,
          data: statsData.daily_data.map(d => d.new_users || 0),
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
            ])
          }
        },
        {
          name: '活跃用户',
          type: 'line',
          smooth: true,
          data: statsData.daily_data.map(d => d.active_users || 0),
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
              { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
            ])
          }
        }
      ]
    }
    chart.setOption(option)
  }
  
  if (roleChart) {
    const roleOption = {
      tooltip: {
        trigger: 'item'
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
            formatter: '{b}: {c} ({d}%)'
          },
          data: [
            { value: statsData.period_roles.customer || 0, name: '普通用户' },
            { value: statsData.period_roles.teacher || 0, name: '老师' }
          ]
        }
      ]
    }
    roleChart.setOption(roleOption)
  }
  
  if (teacherChart) {
    const teacherOption = {
      tooltip: {
        trigger: 'item'
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
            formatter: '{b}: {c} ({d}%)'
          },
          data: [
            { value: statsData.teachers?.verified || 0, name: '已认证' },
            { value: (statsData.teachers?.total || 0) - (statsData.teachers?.verified || 0), name: '未认证' }
          ]
        }
      ]
    }
    teacherChart.setOption(teacherOption)
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
    
    const res = await getUserStats(params)
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
    
    const res = await exportUserStats(params)
    if (res.code === 0) {
      exportStatsToExcel(res.data, `user_stats_${new Date().toISOString().split('T')[0]}.xlsx`)
      ElMessage.success('导出成功')
    }
  } catch (error) {
    console.error('导出失败:', error)
  }
}

const handleResize = () => {
  chart?.resize()
  roleChart?.resize()
  teacherChart?.resize()
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  chart?.dispose()
  roleChart?.dispose()
  teacherChart?.dispose()
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

.chart-container {
  height: 400px;
  width: 100%;
}
</style>
