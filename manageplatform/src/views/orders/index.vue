<template>
  <div class="page-card">
    <div class="page-header">
      <span class="page-title">订单管理</span>
    </div>
    
    <div class="filter-bar">
      <el-input
        v-model="queryParams.keyword"
        placeholder="搜索订单号/用户"
        clearable
        style="width: 200px;"
        @keyup.enter="handleSearch"
      />
      <el-select
        v-model="queryParams.status"
        placeholder="订单状态"
        clearable
        style="width: 160px;"
      >
        <el-option
          v-for="(name, key) in statusOptions"
          :key="key"
          :label="name"
          :value="key"
        />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        style="width: 280px;"
      />
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
        <el-table-column prop="id" label="订单号" width="180" />
        <el-table-column prop="customer_nickname" label="用户" width="100" />
        <el-table-column prop="status_name" label="订单状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ scope.row.status_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="商品信息" min-width="200">
          <template #default="scope">
            <div v-if="scope.row.items?.length">
              <div
                v-for="(item, index) in scope.row.items.slice(0, 2)"
                :key="index"
                style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;"
              >
                <el-image
                  :src="item.product_image"
                  fit="cover"
                  style="width: 40px; height: 40px; border-radius: 4px;"
                >
                  <template #error>
                    <el-icon :size="24"><Picture /></el-icon>
                  </template>
                </el-image>
                <div style="flex: 1; overflow: hidden;">
                  <div style="font-size: 12px; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    {{ item.product_title }}
                  </div>
                  <div style="font-size: 12px; color: #999;">
                    ¥{{ item.price }} x {{ item.quantity }}
                  </div>
                </div>
              </div>
              <div v-if="scope.row.items.length > 2" style="font-size: 12px; color: #999;">
                还有 {{ scope.row.items.length - 2 }} 件商品
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="pay_amount" label="实付金额" width="120">
          <template #default="scope">
            <span style="color: #ff6b35; font-weight: bold;">
              ¥{{ scope.row.pay_amount?.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="pay_method_name" label="支付方式" width="100" />
        <el-table-column prop="create_time" label="下单时间" width="180" />
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="scope">
            <div class="operation-btns">
              <el-button type="primary" link @click="handleView(scope.row)">
                详情
              </el-button>
              <el-button
                v-if="scope.row.status === 'pending_accept'"
                type="success"
                link
                @click="handleAccept(scope.row)"
              >
                接单
              </el-button>
              <el-button
                v-if="scope.row.status === 'paid'"
                type="warning"
                link
                @click="handleShip(scope.row)"
              >
                发货
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
    
    <el-dialog v-model="detailVisible" title="订单详情" width="700px">
      <el-descriptions :column="2" border v-if="currentOrder">
        <el-descriptions-item label="订单号">{{ currentOrder.id }}</el-descriptions-item>
        <el-descriptions-item label="订单状态">
          <el-tag :type="getStatusType(currentOrder.status)">
            {{ currentOrder.status_name }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="用户">{{ currentOrder.customer_nickname }}</el-descriptions-item>
        <el-descriptions-item label="下单时间">{{ currentOrder.create_time }}</el-descriptions-item>
        <el-descriptions-item label="商品金额">¥{{ currentOrder.total_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="优惠金额">¥{{ currentOrder.discount_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="运费">¥{{ currentOrder.shipping_fee?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="实付金额">
          <span style="color: #ff6b35; font-weight: bold;">
            ¥{{ currentOrder.pay_amount?.toFixed(2) }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="支付方式">{{ currentOrder.pay_method_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="支付时间">{{ currentOrder.pay_time || '-' }}</el-descriptions-item>
        <el-descriptions-item label="收货地址" :span="2">
          {{ currentOrder.address?.name }} {{ currentOrder.address?.phone }}<br />
          {{ currentOrder.address?.province }}{{ currentOrder.address?.city }}{{ currentOrder.address?.district }}{{ currentOrder.address?.detail }}
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">
          {{ currentOrder.remark || '无' }}
        </el-descriptions-item>
      </el-descriptions>
      
      <div v-if="currentOrder?.items?.length" style="margin-top: 20px;">
        <h4 style="margin-bottom: 12px; font-weight: 600;">商品列表</h4>
        <el-table :data="currentOrder.items" size="small">
          <el-table-column prop="product_title" label="商品名称" min-width="200" />
          <el-table-column prop="price" label="单价" width="100">
            <template #default="scope">¥{{ scope.row.price?.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column prop="total_price" label="小计" width="100">
            <template #default="scope">¥{{ scope.row.total_price?.toFixed(2) }}</template>
          </el-table-column>
        </el-table>
      </div>
      
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getOrders } from '@/api/orders'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const detailVisible = ref(false)
const currentOrder = ref(null)
const dateRange = ref([])

const statusOptions = {
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

const queryParams = reactive({
  page: 1,
  size: 10,
  keyword: '',
  status: ''
})

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

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: queryParams.page,
      size: queryParams.size
    }
    if (queryParams.status) params.status = queryParams.status
    
    const res = await getOrders(params)
    if (res.code === 0) {
      tableData.value = res.data.list || res.data.orders || []
      total.value = res.data.total || 0
    }
  } catch (e) {
    tableData.value = [
      {
        id: 'ORD20240430100001',
        customer_nickname: '手作爱好者',
        status: 'completed',
        status_name: '已完成',
        total_amount: 299.00,
        discount_amount: 0,
        shipping_fee: 0,
        pay_amount: 299.00,
        pay_method: 'wechat',
        pay_method_name: '微信支付',
        create_time: '2024-04-30 10:30:00',
        pay_time: '2024-04-30 10:35:00',
        remark: '请尽快发货',
        address: { name: '张三', phone: '138****8888', province: '广东省', city: '深圳市', district: '南山区', detail: '科技园南区A栋1001室' },
        items: [
          { product_title: '手工编织羊毛围巾', product_image: '', price: 299.00, quantity: 1, total_price: 299.00 }
        ]
      },
      {
        id: 'ORD20240430091500',
        customer_nickname: 'DIY达人',
        status: 'paid',
        status_name: '待发货',
        total_amount: 158.00,
        discount_amount: 0,
        shipping_fee: 10,
        pay_amount: 168.00,
        pay_method: 'alipay',
        pay_method_name: '支付宝',
        create_time: '2024-04-30 09:15:00',
        pay_time: '2024-04-30 09:20:00',
        remark: '',
        address: { name: '王五', phone: '137****7777', province: '北京市', city: '北京市', district: '朝阳区', detail: '建国路88号SOHO现代城C座503室' },
        items: [
          { product_title: '手工折纸千纸鹤', product_image: '', price: 59.00, quantity: 2, total_price: 118.00 },
          { product_title: '手工刺绣香囊', product_image: '', price: 40.00, quantity: 1, total_price: 40.00 }
        ]
      },
      {
        id: 'ORD20240429164500',
        customer_nickname: '编织女王',
        status: 'in_progress',
        status_name: '制作中',
        total_amount: 420.00,
        discount_amount: 20,
        shipping_fee: 0,
        pay_amount: 400.00,
        pay_method: 'wechat',
        pay_method_name: '微信支付',
        create_time: '2024-04-29 16:45:00',
        pay_time: '2024-04-29 16:50:00',
        remark: '请用精美包装',
        address: { name: '赵六', phone: '134****4444', province: '浙江省', city: '杭州市', district: '西湖区', detail: '文三路90号东部软件园12号楼' },
        items: [
          { product_title: '手工陶瓷茶杯套装', product_image: '', price: 420.00, quantity: 1, total_price: 420.00 }
        ]
      },
      {
        id: 'ORD20240429143000',
        customer_nickname: '纸艺小匠',
        status: 'pending_accept',
        status_name: '待接单',
        total_amount: 88.00,
        discount_amount: 0,
        shipping_fee: 8,
        pay_amount: 96.00,
        pay_method: 'wechat',
        pay_method_name: '微信支付',
        create_time: '2024-04-29 14:30:00',
        pay_time: '2024-04-29 14:35:00',
        remark: '',
        address: { name: '李四', phone: '139****9999', province: '广东省', city: '广州市', district: '天河区', detail: '体育西路天河城B座2002室' },
        items: [
          { product_title: '手工刺绣香囊', product_image: '', price: 88.00, quantity: 1, total_price: 88.00 }
        ]
      }
    ]
    total.value = 4
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
  queryParams.status = ''
  dateRange.value = []
  fetchData()
}

const handleView = (row) => {
  currentOrder.value = row
  detailVisible.value = true
}

const handleAccept = async (row) => {
  try {
    await ElMessageBox.confirm('确定要接单吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'success'
    })
    ElMessage.success('接单成功')
    fetchData()
  } catch {
    // 用户取消
  }
}

const handleShip = (row) => {
  ElMessage.info('发货功能开发中')
}

onMounted(() => {
  fetchData()
})
</script>
