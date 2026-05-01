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
            <div class="stat-label">总订单数</div>
            <div class="stat-value">{{ statsData.summary?.total_orders || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">总收入</div>
            <div class="stat-value">¥{{ statsData.summary?.total_revenue || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">周期订单</div>
            <div class="stat-value">{{ statsData.summary?.period_orders || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">周期收入</div>
            <div class="stat-value">¥{{ statsData.summary?.period_revenue || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">周期取消</div>
            <div class="stat-value">{{ statsData.summary?.period_cancelled || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card>
          <div class="stat-item">
            <div class="stat-label">退款率</div>
            <div class="stat-value">{{ statsData.summary?.refund_rate || 0 }}%</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>订单趋势</span>
          </template>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>订单状态分布（全部）</span>
          </template>
          <div ref="statusPieChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>周期订单状态分布</span>
          </template>
          <div ref="periodPieChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>订单状态明细</span>
          </template>
          <el-table :data="statusTableData" style="width: 100%">
            <el-table-column prop="status_name" label="订单状态" />
            <el-table-column prop="total_count" label="总数" width="120">
              <template #default="{ row }">
                <span class="highlight">{{ row.total_count }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="period_count" label="周期数" width="120" />
            <el-table-column prop="percentage" label="占比" width="120">
              <template #default="{ row }">
                <el-progress 
                  :percentage="row.percentage" 
                  :stroke-width="20"
                  :color="getProgressColor(row.status)"
                  :show-text="true"
                />
              </template>
            </el-table-column>
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
import { getOrderStats, exportOrderStats } from '@/api/stats'
import { exportStatsToExcel } from '@/utils/export'

const STATUS_NAMES = {
  pending: '待付款',
  pending_accept: '待接单',
  accepted: '已接单',
  in_progress: '制作中',
  paid: '待发货',
  shipped: '待收货',
  delivered: '已送达',
  completed: '已完成',
  cancelled: '已取消',
  rejected: '已拒绝',
  deleted: '已删除'
}

const STATUS_COLORS = {
  pending: '#409eff',
  pending_accept: '#e6a23c',
  accepted: '#67c23a',
  in_progress: '#909399',
  paid: '#409eff',
  shipped: '#e6a23c',
  delivered: '#67c23a',
  completed: '#67c23a',
  cancelled: '#f56c6c',
  rejected: '#f56c6c',
  deleted: '#909399'
}

const trendChartRef = ref(null)
const statusPieChartRef = ref(null)
const periodPieChartRef = ref(null)
let trendChart = null
let statusPieChart = null
let periodPieChart = null

const period = ref('week')
const dateRange = ref([])
const loading = ref(false)

const statsData = reactive({
  summary: {
    total_orders: 0,
    total_revenue: 0,
    total_cancelled: 0,
    period_orders: 0,
    period_revenue: 0,
    period_cancelled: 0,
    refund_rate: 0
  },
  status_counts: {},
  period_status_counts: {},
  daily_data: []
})

const statusTableData = computed(() => {
  const statusCounts = statsData.status_counts || {}
  const periodCounts = statsData.period_status_counts || {}
  const totalOrders = statsData.summary?.total_orders || 1
  
  const data = []
  for (const [status, count] of Object.entries(statusCounts)) {
    if (status === 'deleted') continue
    data.push({
      status,
      status_name: STATUS_NAMES[status] || status,
      total_count: count || 0,
      period_count: periodCounts[status] || 0,
      percentage: Math.round((count || 0) / totalOrders * 100)
    })
  }
  return data.sort((a, b) => b.total_count - a.total_count)
})

const disabledDate = (time) => {
  return time.getTime() > Date.now()
}

const getProgressColor = (status) => {
  return STATUS_COLORS[status] || '#909399'
}

const initCharts = () => {
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
  }
  if (statusPieChartRef.value) {
    statusPieChart = echarts.init(statusPieChartRef.value)
  }
  if (periodPieChartRef.value) {
    periodPieChart = echarts.init(periodPieChartRef.value)
  }
}

const generatePieData = (counts) => {
  const data = []
  for (const [status, count] of Object.entries(counts)) {
    if (status === 'deleted' || count === 0) continue
    data.push({
      value: count,
      name: STATUS_NAMES[status] || status,
      itemStyle: { color: STATUS_COLORS[status] || '#909399' }
    })
  }
  return data.sort((a, b) => b.value - a.value)
}

const updateCharts = () => {
  if (trendChart && statsData.daily_data?.length > 0) {
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' }
      },
      legend: {
        data: ['订单数', '收入', '取消数']
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
      yAxis: [
        {
          type: 'value',
          name: '数量',
          position: 'left'
        },
        {
          type: 'value',
          name: '收入(元)',
          position: 'right'
        }
      ],
      series: [
        {
          name: '订单数',
          type: 'line',
          smooth: true,
          data: statsData.daily_data.map(d => d.order_count || 0),
          itemStyle: { color: '#409eff' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
            ])
          }
        },
        {
          name: '收入',
          type: 'line',
          smooth: true,
          yAxisIndex: 1,
          data: statsData.daily_data.map(d => d.revenue || 0),
          itemStyle: { color: '#67c23a' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
              { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
            ])
          }
        },
        {
          name: '取消数',
          type: 'line',
          smooth: true,
          data: statsData.daily_data.map(d => d.cancelled_count || 0),
          itemStyle: { color: '#f56c6c' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(245, 108, 108, 0.3)' },
              { offset: 1, color: 'rgba(245, 108, 108, 0.05)' }
            ])
          }
        }
      ]
    }
    trendChart.setOption(option)
  }
  
  const totalPieData = generatePieData(statsData.status_counts || {})
  if (statusPieChart && totalPieData.length > 0) {
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
          data: totalPieData
        }
      ]
    }
    statusPieChart.setOption(option)
  }
  
  const periodPieData = generatePieData(statsData.period_status_counts || {})
  if (periodPieChart && periodPieData.length > 0) {
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
          data: periodPieData
        }
      ]
    }
    periodPieChart.setOption(option)
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
    
    const res = await getOrderStats(params)
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
    
    const res = await exportOrderStats(params)
    if (res.code === 0) {
      exportStatsToExcel(res.data, `order_stats_${new Date().toISOString().split('T')[0]}.xlsx`)
      ElMessage.success('导出成功')
    }
  } catch (error) {
    console.error('导出失败:', error)
  }
}

const handleResize = () => {
  trendChart?.resize()
  statusPieChart?.resize()
  periodPieChart?.resize()
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  trendChart?.dispose()
  statusPieChart?.dispose()
  periodPieChart?.dispose()
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
