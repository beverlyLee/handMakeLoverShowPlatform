<template>
  <div class="page-card">
    <div class="page-header">
      <span class="page-title">订单管理</span>
    </div>
    
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="全部订单" name="all" />
      <el-tab-pane label="异常订单" name="abnormal">
        <template #label>
          <span>异常订单</span>
          <el-tag v-if="abnormalCount > 0" type="danger" size="small" style="margin-left: 4px;">
            {{ abnormalCount }}
          </el-tag>
        </template>
      </el-tab-pane>
    </el-tabs>
    
    <div class="filter-bar">
      <el-input
        v-model="queryParams.keyword"
        placeholder="搜索订单号/用户昵称"
        clearable
        style="width: 200px;"
        @keyup.enter="handleSearch"
      />
      <el-input
        v-model="queryParams.user_id"
        placeholder="用户ID"
        clearable
        style="width: 120px;"
      />
      <el-input
        v-model="queryParams.teacher_id"
        placeholder="老师ID"
        clearable
        style="width: 120px;"
      />
      <el-select
        v-model="queryParams.status"
        placeholder="订单状态"
        clearable
        style="width: 140px;"
      >
        <el-option
          v-for="(name, key) in statusOptions"
          :key="key"
          :label="name"
          :value="key"
        />
      </el-select>
      <el-select
        v-model="queryParams.refund_status"
        placeholder="退款状态"
        clearable
        style="width: 140px;"
        v-if="activeTab === 'abnormal'"
      >
        <el-option
          v-for="(name, key) in refundStatusOptions"
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
      <el-button type="success" @click="showExportDialog">
        <el-icon><Download /></el-icon>
        导出
      </el-button>
    </div>
    
    <div class="table-wrapper">
      <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="订单号" width="160">
          <template #default="scope">
            <span class="order-id">{{ scope.row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="customer_nickname" label="用户" width="100" />
        <el-table-column prop="teacher_nickname" label="老师" width="100">
          <template #default="scope">
            {{ scope.row.teacher_nickname || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status_name" label="订单状态" width="120">
          <template #default="scope">
            <div style="display: flex; flex-direction: column; gap: 4px;">
              <el-tag :type="getStatusType(scope.row.status)" size="small">
                {{ scope.row.status_name }}
              </el-tag>
              <div v-if="scope.row.is_abnormal">
                <el-tag type="danger" size="small" effect="dark">异常</el-tag>
              </div>
              <div v-if="scope.row.refund_status && scope.row.refund_status !== 'none'">
                <el-tag :type="getRefundStatusType(scope.row.refund_status)" size="small">
                  {{ scope.row.refund_status_name }}
                </el-tag>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="商品信息" min-width="180">
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
        <el-table-column prop="pay_amount" label="实付金额" width="100">
          <template #default="scope">
            <span style="color: #ff6b35; font-weight: bold;">
              ¥{{ scope.row.pay_amount?.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="下单时间" width="160" />
        <el-table-column label="操作" fixed="right" width="280">
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
              <el-button
                v-if="scope.row.status !== 'completed' && scope.row.status !== 'cancelled'"
                type="danger"
                link
                @click="handleCancel(scope.row)"
              >
                取消
              </el-button>
              <el-dropdown v-if="scope.row.is_abnormal" @command="(cmd) => handleAbnormalAction(cmd, scope.row)">
                <el-button type="warning" link>
                  异常操作
                  <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="updateLogistics">修改物流</el-dropdown-item>
                    <el-dropdown-item command="refund">退款处理</el-dropdown-item>
                    <el-dropdown-item command="resolve">解除异常</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
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
    
    <el-dialog v-model="detailVisible" title="订单详情" width="800px">
      <el-descriptions :column="2" border v-if="currentOrder">
        <el-descriptions-item label="订单号">{{ currentOrder.id }}</el-descriptions-item>
        <el-descriptions-item label="订单状态">
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <el-tag :type="getStatusType(currentOrder.status)">
              {{ currentOrder.status_name }}
            </el-tag>
            <el-tag v-if="currentOrder.is_abnormal" type="danger" effect="dark">
              异常订单
            </el-tag>
            <el-tag 
              v-if="currentOrder.refund_status && currentOrder.refund_status !== 'none'"
              :type="getRefundStatusType(currentOrder.refund_status)"
            >
              {{ currentOrder.refund_status_name }}
            </el-tag>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="用户">{{ currentOrder.customer_nickname }}</el-descriptions-item>
        <el-descriptions-item label="老师">
          {{ currentOrder.teacher_nickname || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="下单时间">{{ currentOrder.create_time }}</el-descriptions-item>
        <el-descriptions-item label="支付时间">{{ currentOrder.pay_time || '-' }}</el-descriptions-item>
        <el-descriptions-item label="商品金额">¥{{ currentOrder.total_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="优惠金额">¥{{ currentOrder.discount_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="运费">¥{{ currentOrder.shipping_fee?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="实付金额">
          <span style="color: #ff6b35; font-weight: bold;">
            ¥{{ currentOrder.pay_amount?.toFixed(2) }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="支付方式">{{ currentOrder.pay_method_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="发货时间">{{ currentOrder.ship_time || '-' }}</el-descriptions-item>
      </el-descriptions>
      
      <div style="margin-top: 20px;">
        <h4 style="margin-bottom: 12px; font-weight: 600;">收货信息</h4>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="收货人">
            {{ currentOrder.address?.name }} {{ currentOrder.address?.phone }}
          </el-descriptions-item>
          <el-descriptions-item label="收货地址">
            {{ currentOrder.address?.province }}{{ currentOrder.address?.city }}
            {{ currentOrder.address?.district }}{{ currentOrder.address?.detail }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      
      <div v-if="currentOrder.shipping_company || currentOrder.tracking_number" style="margin-top: 20px;">
        <h4 style="margin-bottom: 12px; font-weight: 600;">物流信息</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="快递公司">
            {{ currentOrder.shipping_company || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="物流单号">
            {{ currentOrder.tracking_number || '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      
      <div v-if="currentOrder.is_abnormal" style="margin-top: 20px;">
        <h4 style="margin-bottom: 12px; font-weight: 600;">异常信息</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="异常原因">
            {{ currentOrder.abnormal_reason_name || currentOrder.abnormal_reason }}
          </el-descriptions-item>
          <el-descriptions-item label="异常时间">
            {{ currentOrder.abnormal_time || '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      
      <div v-if="currentOrder.refund_status && currentOrder.refund_status !== 'none'" style="margin-top: 20px;">
        <h4 style="margin-bottom: 12px; font-weight: 600;">退款信息</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="退款状态">
            <el-tag :type="getRefundStatusType(currentOrder.refund_status)">
              {{ currentOrder.refund_status_name }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="退款金额">
            ¥{{ currentOrder.refund_amount?.toFixed(2) || '0.00' }}
          </el-descriptions-item>
          <el-descriptions-item label="退款原因" :span="2">
            {{ currentOrder.refund_reason || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="退款时间">
            {{ currentOrder.refund_time || '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      
      <div v-if="currentOrder.remark" style="margin-top: 20px;">
        <h4 style="margin-bottom: 12px; font-weight: 600;">用户备注</h4>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="备注内容">
            {{ currentOrder.remark }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      
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
    
    <el-dialog v-model="cancelDialogVisible" title="取消订单" width="500px">
      <el-form :model="cancelForm" label-width="80px">
        <el-form-item label="取消理由" required>
          <el-input
            v-model="cancelForm.reason"
            type="textarea"
            :rows="4"
            placeholder="请输入取消理由（至少10个字符）"
          />
          <div style="font-size: 12px; color: #999; margin-top: 4px;">
            已输入 {{ cancelForm.reason.length }} 个字符
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cancelDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmCancel" :disabled="cancelForm.reason.length < 10">
          确认取消
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="shipDialogVisible" title="发货" width="500px">
      <el-form :model="shipForm" label-width="80px">
        <el-form-item label="快递公司" required>
          <el-select v-model="shipForm.shipping_company" placeholder="请选择快递公司" style="width: 100%;">
            <el-option label="顺丰速运" value="顺丰速运" />
            <el-option label="中通快递" value="中通快递" />
            <el-option label="圆通速递" value="圆通速递" />
            <el-option label="申通快递" value="申通快递" />
            <el-option label="韵达速递" value="韵达速递" />
            <el-option label="京东物流" value="京东物流" />
            <el-option label="邮政EMS" value="邮政EMS" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="物流单号" required>
          <el-input v-model="shipForm.tracking_number" placeholder="请输入物流单号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shipDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmShip" :disabled="!shipForm.shipping_company || !shipForm.tracking_number">
          确认发货
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="logisticsDialogVisible" title="修改物流信息" width="500px">
      <el-form :model="logisticsForm" label-width="80px">
        <el-form-item label="快递公司" required>
          <el-select v-model="logisticsForm.shipping_company" placeholder="请选择快递公司" style="width: 100%;">
            <el-option label="顺丰速运" value="顺丰速运" />
            <el-option label="中通快递" value="中通快递" />
            <el-option label="圆通速递" value="圆通速递" />
            <el-option label="申通快递" value="申通快递" />
            <el-option label="韵达速递" value="韵达速递" />
            <el-option label="京东物流" value="京东物流" />
            <el-option label="邮政EMS" value="邮政EMS" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="物流单号" required>
          <el-input v-model="logisticsForm.tracking_number" placeholder="请输入物流单号" />
        </el-form-item>
        <el-form-item label="修改理由">
          <el-input
            v-model="logisticsForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入修改理由（选填）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="logisticsDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmUpdateLogistics" :disabled="!logisticsForm.shipping_company || !logisticsForm.tracking_number">
          确认修改
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="refundDialogVisible" title="退款处理" width="500px">
      <el-form :model="refundForm" label-width="80px">
        <el-form-item label="退款状态" required>
          <el-radio-group v-model="refundForm.refund_status">
            <el-radio value="approved">同意退款</el-radio>
            <el-radio value="rejected">拒绝退款</el-radio>
            <el-radio value="completed">退款完成</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="退款金额">
          <el-input-number
            v-model="refundForm.refund_amount"
            :min="0"
            :precision="2"
            :disabled="refundForm.refund_status === 'rejected'"
          />
        </el-form-item>
        <el-form-item label="处理理由" required>
          <el-input
            v-model="refundForm.reason"
            type="textarea"
            :rows="4"
            placeholder="请输入处理理由（至少10个字符）"
          />
          <div style="font-size: 12px; color: #999; margin-top: 4px;">
            已输入 {{ refundForm.reason.length }} 个字符
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="refundDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="confirmRefund"
          :disabled="!refundForm.refund_status || refundForm.reason.length < 10"
        >
          确认处理
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="resolveDialogVisible" title="解除异常" width="500px">
      <el-form :model="resolveForm" label-width="80px">
        <el-form-item label="处理方式">
          <el-radio-group v-model="resolveForm.action">
            <el-radio value="resolve">仅解除异常</el-radio>
            <el-radio value="reopen">恢复订单流转</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="处理方案" required>
          <el-input
            v-model="resolveForm.resolution"
            type="textarea"
            :rows="4"
            placeholder="请输入处理方案（至少10个字符）"
          />
          <div style="font-size: 12px; color: #999; margin-top: 4px;">
            已输入 {{ resolveForm.resolution.length }} 个字符
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resolveDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="confirmResolve"
          :disabled="resolveForm.resolution.length < 10"
        >
          确认解除
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="exportDialogVisible" title="导出订单" width="600px">
      <el-form :model="exportForm" label-width="100px">
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="exportForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="订单状态">
          <el-select
            v-model="exportForm.status"
            placeholder="全部状态"
            clearable
            style="width: 100%;"
          >
            <el-option
              v-for="(name, key) in statusOptions"
              :key="key"
              :label="name"
              :value="key"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="导出字段">
          <el-checkbox-group v-model="exportForm.fields">
            <el-checkbox
              v-for="(name, key) in exportFields"
              :key="key"
              :label="key"
            >
              {{ name }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="exportDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmExport" :disabled="exportForm.fields.length === 0">
          确认导出
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getOrders,
  getOrderDetail,
  updateOrderStatus,
  markOrderAbnormal,
  resolveAbnormalOrder,
  updateOrderLogistics,
  processOrderRefund,
  exportOrders
} from '@/api/orders'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const abnormalCount = ref(0)
const activeTab = ref('all')
const dateRange = ref([])

const detailVisible = ref(false)
const currentOrder = ref(null)

const cancelDialogVisible = ref(false)
const cancelForm = reactive({ reason: '' })

const shipDialogVisible = ref(false)
const shipForm = reactive({ shipping_company: '', tracking_number: '' })

const logisticsDialogVisible = ref(false)
const logisticsForm = reactive({ shipping_company: '', tracking_number: '', reason: '' })

const refundDialogVisible = ref(false)
const refundForm = reactive({ refund_status: '', refund_amount: 0, reason: '' })

const resolveDialogVisible = ref(false)
const resolveForm = reactive({ action: 'resolve', resolution: '' })

const exportDialogVisible = ref(false)
const exportForm = reactive({
  dateRange: [],
  status: '',
  fields: ['id', 'customer_nickname', 'status_name', 'pay_amount', 'create_time']
})

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

const refundStatusOptions = {
  pending: '待处理',
  approved: '已同意',
  rejected: '已拒绝',
  completed: '已完成'
}

const exportFields = {
  id: '订单号',
  customer_nickname: '用户昵称',
  teacher_nickname: '老师昵称',
  status_name: '订单状态',
  pay_amount: '实付金额',
  total_amount: '商品金额',
  discount_amount: '优惠金额',
  shipping_fee: '运费',
  pay_method_name: '支付方式',
  is_abnormal: '是否异常',
  refund_status_name: '退款状态',
  refund_amount: '退款金额',
  create_time: '下单时间',
  pay_time: '支付时间',
  ship_time: '发货时间',
  complete_time: '完成时间'
}

const queryParams = reactive({
  page: 1,
  size: 10,
  keyword: '',
  status: '',
  user_id: '',
  teacher_id: '',
  is_abnormal: null,
  refund_status: '',
  start_date: '',
  end_date: ''
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

const getRefundStatusType = (status) => {
  const statusMap = {
    pending: 'warning',
    approved: 'primary',
    rejected: 'danger',
    completed: 'success'
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
    if (queryParams.keyword) params.keyword = queryParams.keyword
    if (queryParams.status) params.status = queryParams.status
    if (queryParams.user_id) params.user_id = queryParams.user_id
    if (queryParams.teacher_id) params.teacher_id = queryParams.teacher_id
    if (queryParams.refund_status) params.refund_status = queryParams.refund_status
    if (queryParams.is_abnormal !== null) params.is_abnormal = queryParams.is_abnormal
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]?.toISOString().split('T')[0]
      params.end_date = dateRange.value[1]?.toISOString().split('T')[0]
    }
    
    const res = await getOrders(params)
    if (res.code === 0) {
      tableData.value = res.data.list || res.data.orders || []
      total.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取订单列表失败:', e)
    ElMessage.error('获取订单列表失败')
  } finally {
    loading.value = false
  }
}

const fetchAbnormalCount = async () => {
  try {
    const params = { page: 1, size: 1, is_abnormal: true }
    const res = await getOrders(params)
    if (res.code === 0) {
      abnormalCount.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取异常订单数量失败:', e)
  }
}

const handleTabChange = (tab) => {
  if (tab === 'abnormal') {
    queryParams.is_abnormal = true
  } else {
    queryParams.is_abnormal = null
  }
  queryParams.page = 1
  fetchData()
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const resetQuery = () => {
  queryParams.page = 1
  queryParams.keyword = ''
  queryParams.status = ''
  queryParams.user_id = ''
  queryParams.teacher_id = ''
  queryParams.refund_status = ''
  queryParams.is_abnormal = activeTab.value === 'abnormal' ? true : null
  dateRange.value = []
  fetchData()
}

const handleView = async (row) => {
  try {
    const res = await getOrderDetail(row.id)
    if (res.code === 0) {
      currentOrder.value = res.data
      detailVisible.value = true
    }
  } catch (e) {
    currentOrder.value = row
    detailVisible.value = true
  }
}

const handleAccept = async (row) => {
  try {
    await ElMessageBox.confirm('确定要接单吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'success'
    })
    const res = await updateOrderStatus(row.id, { status: 'accepted' })
    if (res.code === 0) {
      ElMessage.success('接单成功')
      fetchData()
    }
  } catch {
    // 用户取消
  }
}

const handleShip = (row) => {
  currentOrder.value = row
  shipForm.shipping_company = ''
  shipForm.tracking_number = ''
  shipDialogVisible.value = true
}

const confirmShip = async () => {
  try {
    const res = await updateOrderStatus(currentOrder.value.id, {
      status: 'shipped',
      shipping_company: shipForm.shipping_company,
      tracking_number: shipForm.tracking_number
    })
    if (res.code === 0) {
      ElMessage.success('发货成功')
      shipDialogVisible.value = false
      fetchData()
    }
  } catch (e) {
    ElMessage.error('发货失败')
  }
}

const handleCancel = (row) => {
  currentOrder.value = row
  cancelForm.reason = ''
  cancelDialogVisible.value = true
}

const confirmCancel = async () => {
  if (cancelForm.reason.length < 10) {
    ElMessage.warning('取消理由至少需要10个字符')
    return
  }
  try {
    const res = await updateOrderStatus(currentOrder.value.id, {
      status: 'cancelled',
      reason: cancelForm.reason
    })
    if (res.code === 0) {
      ElMessage.success('订单已取消')
      cancelDialogVisible.value = false
      fetchData()
    }
  } catch (e) {
    ElMessage.error('取消失败')
  }
}

const handleAbnormalAction = (cmd, row) => {
  currentOrder.value = row
  switch (cmd) {
    case 'updateLogistics':
      logisticsForm.shipping_company = row.shipping_company || ''
      logisticsForm.tracking_number = row.tracking_number || ''
      logisticsForm.reason = ''
      logisticsDialogVisible.value = true
      break
    case 'refund':
      refundForm.refund_status = ''
      refundForm.refund_amount = row.pay_amount || 0
      refundForm.reason = ''
      refundDialogVisible.value = true
      break
    case 'resolve':
      resolveForm.action = 'resolve'
      resolveForm.resolution = ''
      resolveDialogVisible.value = true
      break
  }
}

const confirmUpdateLogistics = async () => {
  try {
    const res = await updateOrderLogistics(currentOrder.value.id, {
      shipping_company: logisticsForm.shipping_company,
      tracking_number: logisticsForm.tracking_number,
      reason: logisticsForm.reason
    })
    if (res.code === 0) {
      ElMessage.success('物流信息已更新')
      logisticsDialogVisible.value = false
      fetchData()
    }
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

const confirmRefund = async () => {
  if (refundForm.reason.length < 10) {
    ElMessage.warning('处理理由至少需要10个字符')
    return
  }
  try {
    const res = await processOrderRefund(currentOrder.value.id, {
      refund_status: refundForm.refund_status,
      refund_amount: refundForm.refund_amount,
      reason: refundForm.reason
    })
    if (res.code === 0) {
      ElMessage.success('退款处理成功')
      refundDialogVisible.value = false
      fetchData()
    }
  } catch (e) {
    ElMessage.error('处理失败')
  }
}

const confirmResolve = async () => {
  if (resolveForm.resolution.length < 10) {
    ElMessage.warning('处理方案至少需要10个字符')
    return
  }
  try {
    const res = await resolveAbnormalOrder(currentOrder.value.id, {
      resolution: resolveForm.resolution,
      action: resolveForm.action
    })
    if (res.code === 0) {
      ElMessage.success('异常已解除')
      resolveDialogVisible.value = false
      fetchData()
      fetchAbnormalCount()
    }
  } catch (e) {
    ElMessage.error('解除失败')
  }
}

const showExportDialog = () => {
  exportForm.dateRange = dateRange.value || []
  exportForm.status = queryParams.status
  exportDialogVisible.value = true
}

const confirmExport = async () => {
  try {
    const params = {}
    if (exportForm.dateRange && exportForm.dateRange.length === 2) {
      params.start_date = exportForm.dateRange[0]?.toISOString().split('T')[0]
      params.end_date = exportForm.dateRange[1]?.toISOString().split('T')[0]
    }
    if (exportForm.status) params.status = exportForm.status
    params.fields = exportForm.fields.join(',')
    
    const res = await exportOrders(params)
    if (res.code === 0) {
      const { csv_content, filename } = res.data
      const blob = new Blob(['\ufeff' + csv_content], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = filename
      link.click()
      ElMessage.success('导出成功')
      exportDialogVisible.value = false
    }
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  fetchData()
  fetchAbnormalCount()
})
</script>

<style scoped>
.page-card {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
  align-items: center;
}

.table-wrapper {
  margin-bottom: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
}

.operation-btns {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.order-id {
  font-family: monospace;
  color: #409eff;
  cursor: pointer;
}

.order-id:hover {
  text-decoration: underline;
}
</style>
