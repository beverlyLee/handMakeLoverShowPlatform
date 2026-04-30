<template>
  <div class="dashboard-page">
    <el-row :gutter="20" style="margin-bottom: 24px;">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.totalOrders || 0 }}</div>
          <div class="stat-label">总订单数</div>
          <div class="stat-trend up">
            <el-icon><TrendCharts /></el-icon>
            <span>较昨日 +{{ stats.today_orders || 0 }}</span>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card" style="background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%);">
          <div class="stat-value">¥{{ stats.total_amount?.toFixed(2) || '0.00' }}</div>
          <div class="stat-label">总销售额</div>
          <div class="stat-trend up">
            <el-icon><TrendCharts /></el-icon>
            <span>今日 +¥{{ stats.today_amount?.toFixed(2) || '0.00' }}</span>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card" style="background: linear-gradient(135deg, #52c41a 0%, #95de64 100%);">
          <div class="stat-value">{{ productCount }}</div>
          <div class="stat-label">商品总数</div>
          <div class="stat-trend up">
            <el-icon><TrendCharts /></el-icon>
            <span>在售商品</span>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card" style="background: linear-gradient(135deg, #faad14 0%, #ffc53d 100%);">
          <div class="stat-value">{{ stats.pending_accept || 0 }}</div>
          <div class="stat-label">待处理订单</div>
          <div class="stat-trend up" style="color: #fffbe6;">
            <el-icon><WarningFilled /></el-icon>
            <span>需要处理</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="14">
        <div class="page-card">
          <div class="page-header">
            <span class="page-title">销售趋势</span>
          </div>
          <div ref="salesChartRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="10">
        <div class="page-card">
          <div class="page-header">
            <span class="page-title">订单状态分布</span>
          </div>
          <div ref="orderChartRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 24px;">
      <el-col :xs="24" :lg="16">
        <div class="page-card">
          <div class="page-header">
            <span class="page-title">最近订单</span>
            <el-button type="primary" link @click="goToOrders">查看全部</el-button>
          </div>
          <el-table :data="recentOrders" stripe style="width: 100%">
            <el-table-column prop="id" label="订单号" width="180" />
            <el-table-column prop="customer_nickname" label="用户" width="100" />
            <el-table-column prop="status_name" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status_name }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="pay_amount" label="金额" width="100">
              <template #default="scope">
                ¥{{ scope.row.pay_amount?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="create_time" label="下单时间" min-width="150" />
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :lg="8">
        <div class="page-card">
          <div class="page-header">
            <span class="page-title">快速统计</span>
          </div>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="今日订单">
              <span style="color: #ff6b35; font-weight: bold;">{{ stats.today_orders || 0 }}</span> 单
            </el-descriptions-item>
            <el-descriptions-item label="今日销售额">
              <span style="color: #ff6b35; font-weight: bold;">¥{{ stats.today_amount?.toFixed(2) || '0.00' }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="制作中">
              <span style="color: #1890ff; font-weight: bold;">{{ stats.in_progress || 0 }}</span> 单
            </el-descriptions-item>
            <el-descriptions-item label="待发货">
              <span style="color: #faad14; font-weight: bold;">{{ stats.paid || 0 }}</span> 单
            </el-descriptions-item>
            <el-descriptions-item label="本月收入">
              <span style="color: #52c41a; font-weight: bold;">¥{{ stats.month_income?.toFixed(2) || '0.00' }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getDashboardStats, getProductStats, getRecentOrders } from '@/api/dashboard'

const router = useRouter()

const salesChartRef = ref(null)
const orderChartRef = ref(null)
let salesChart = null
let orderChart = null

const stats = ref({})
const productCount = ref(0)
const recentOrders = ref([])

const getStatusType = (status) => {
  const statusMap = {
    pending: 'warning',
    pending_accept: 'info',
    accepted: 'primary',
    in_progress: 'primary',
    paid: 'warning',
    shipped: 'info',
    delivered: 'success',
    completed: 'success',
    cancelled: 'danger',
    rejected: 'danger'
  }
  return statusMap[status] || 'info'
}

const dailyTrendData = ref([])
const statusCounts = ref({})

const loadData = async () => {
  try {
    const statsRes = await getDashboardStats()
    if (statsRes.code === 0) {
      stats.value = statsRes.data.stats || {}
      recentOrders.value = statsRes.data.recent_orders || []
      dailyTrendData.value = statsRes.data.daily_trend || []
      statusCounts.value = statsRes.data.status_counts || {}
      
      if (statsRes.data.products && statsRes.data.products.total) {
        productCount.value = statsRes.data.products.total
      }
    }
  } catch (e) {
    console.error('获取统计数据失败:', e)
    stats.value = {
      totalOrders: 156,
      total_amount: 28560.50,
      today_orders: 12,
      today_amount: 1580.00,
      pending_accept: 5,
      in_progress: 8,
      paid: 3,
      month_income: 12580.00,
      completed: 80,
      cancelled: 5
    }
    recentOrders.value = [
      { id: 'ORD20240430100001', customer_nickname: '手作爱好者', status: 'completed', status_name: '已完成', pay_amount: 299.00, create_time: '2024-04-30 10:30:00' },
      { id: 'ORD20240430091500', customer_nickname: 'DIY达人', status: 'paid', status_name: '待发货', pay_amount: 158.00, create_time: '2024-04-30 09:15:00' },
      { id: 'ORD20240429164500', customer_nickname: '编织女王', status: 'in_progress', status_name: '制作中', pay_amount: 420.00, create_time: '2024-04-29 16:45:00' }
    ]
    dailyTrendData.value = []
    statusCounts.value = {}
  }
  
  try {
    if (productCount.value === 0) {
      const productRes = await getProductStats()
      if (productRes.code === 0) {
        productCount.value = productRes.data.total || 0
      }
    }
  } catch (e) {
    productCount.value = 48
  }
  
  setTimeout(() => {
    updateSalesChart()
    updateOrderChart()
  }, 100)
}

const getChartData = () => {
  if (dailyTrendData.value && dailyTrendData.value.length > 0) {
    return {
      dates: dailyTrendData.value.map(d => d.date.slice(5)),
      revenues: dailyTrendData.value.map(d => d.revenue || 0),
      orders: dailyTrendData.value.map(d => d.orders || 0)
    }
  }
  return {
    dates: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    revenues: [1200, 1900, 1500, 2200, 1800, 2500, 2100],
    orders: [5, 8, 6, 10, 7, 12, 9]
  }
}

const getOrderStatusData = () => {
  if (statusCounts.value && Object.keys(statusCounts.value).length > 0) {
    const data = []
    const colorMap = {
      pending: '#faad14',
      pending_accept: '#1890ff',
      accepted: '#409eff',
      in_progress: '#409eff',
      paid: '#faad14',
      shipped: '#1890ff',
      delivered: '#52c41a',
      completed: '#52c41a',
      cancelled: '#ff4d4f',
      rejected: '#ff4d4f'
    }
    const nameMap = {
      pending: '待付款',
      pending_accept: '待接单',
      accepted: '已接单',
      in_progress: '制作中',
      paid: '待发货',
      shipped: '待收货',
      delivered: '已送达',
      completed: '已完成',
      cancelled: '已取消',
      rejected: '已拒绝'
    }
    
    for (const [status, count] of Object.entries(statusCounts.value)) {
      if (count > 0 && status !== 'deleted') {
        data.push({
          value: count,
          name: nameMap[status] || status,
          itemStyle: { color: colorMap[status] || '#999' }
        })
      }
    }
    return data.length > 0 ? data : [
      { value: 10, name: '待接单', itemStyle: { color: '#1890ff' } },
      { value: 15, name: '制作中', itemStyle: { color: '#409eff' } },
      { value: 8, name: '待发货', itemStyle: { color: '#faad14' } },
      { value: 50, name: '已完成', itemStyle: { color: '#52c41a' } },
      { value: 5, name: '已取消', itemStyle: { color: '#ff4d4f' } }
    ]
  }
  return [
    { value: stats.value.pending_accept || 10, name: '待接单', itemStyle: { color: '#1890ff' } },
    { value: stats.value.in_progress || 15, name: '制作中', itemStyle: { color: '#409eff' } },
    { value: stats.value.paid || 8, name: '待发货', itemStyle: { color: '#faad14' } },
    { value: stats.value.completed || 50, name: '已完成', itemStyle: { color: '#52c41a' } },
    { value: stats.value.cancelled || 5, name: '已取消', itemStyle: { color: '#ff4d4f' } }
  ]
}

const initSalesChart = () => {
  if (!salesChartRef.value) return
  
  if (salesChart) {
    salesChart.dispose()
  }
  
  salesChart = echarts.init(salesChartRef.value)
  updateSalesChart()
}

const updateSalesChart = () => {
  if (!salesChart) return
  
  const chartData = getChartData()
  
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#ff6b35',
      textStyle: {
        color: '#333'
      }
    },
    legend: {
      data: ['销售额', '订单数'],
      top: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: chartData.dates,
      axisLine: {
        lineStyle: {
          color: '#ddd'
        }
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '销售额(元)',
        axisLine: {
          lineStyle: {
            color: '#ddd'
          }
        },
        splitLine: {
          lineStyle: {
            color: '#f0f0f0'
          }
        }
      },
      {
        type: 'value',
        name: '订单数',
        axisLine: {
          lineStyle: {
            color: '#ddd'
          }
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: [
      {
        name: '销售额',
        type: 'line',
        smooth: true,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255, 107, 53, 0.3)' },
            { offset: 1, color: 'rgba(255, 107, 53, 0.05)' }
          ])
        },
        lineStyle: {
          color: '#ff6b35',
          width: 3
        },
        itemStyle: {
          color: '#ff6b35'
        },
        data: chartData.revenues
      },
      {
        name: '订单数',
        type: 'bar',
        yAxisIndex: 1,
        barWidth: '30%',
        itemStyle: {
          color: '#409eff',
          borderRadius: [4, 4, 0, 0]
        },
        data: chartData.orders
      }
    ]
  }
  
  salesChart.setOption(option, true)
}

const initOrderChart = () => {
  if (!orderChartRef.value) return
  
  if (orderChart) {
    orderChart.dispose()
  }
  
  orderChart = echarts.init(orderChartRef.value)
  updateOrderChart()
}

const updateOrderChart = () => {
  if (!orderChart) return
  
  const statusData = getOrderStatusData()
  
  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#ff6b35',
      textStyle: {
        color: '#333'
      },
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      bottom: '0%',
      left: 'center',
      type: 'scroll'
    },
    series: [
      {
        name: '订单状态',
        type: 'pie',
        radius: ['35%', '65%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: statusData
      }
    ]
  }
  
  orderChart.setOption(option, true)
}

const goToOrders = () => {
  router.push('/orders')
}

const handleResize = () => {
  salesChart?.resize()
  orderChart?.resize()
}

onMounted(async () => {
  await loadData()
  initSalesChart()
  initOrderChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  salesChart?.dispose()
  orderChart?.dispose()
})
</script>

<style scoped>
.dashboard-page {
  width: 100%;
}

.stat-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(255, 107, 53, 0.25);
}
</style>
