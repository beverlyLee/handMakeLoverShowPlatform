<template>
  <div class="page-card">
    <div class="page-header">
      <span class="page-title">退款管理</span>
      <div style="margin-left: auto; display: flex; gap: 12px;">
        <el-button type="success" @click="openStatsDialog">
          <el-icon><DataLine /></el-icon>
          统计分析
        </el-button>
      </div>
    </div>
    
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="全部退款" name="all" />
      <el-tab-pane label="待审核" name="pending">
        <template #label>
          <span>待审核</span>
          <el-tag v-if="pendingCount > 0" type="danger" size="small" style="margin-left: 4px;">
            {{ pendingCount }}
          </el-tag>
        </template>
      </el-tab-pane>
      <el-tab-pane label="异常退款" name="abnormal">
        <template #label>
          <span>异常退款</span>
          <el-tag v-if="abnormalCount > 0" type="warning" size="small" style="margin-left: 4px;">
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
      <el-select
        v-model="queryParams.refund_status"
        placeholder="退款状态"
        clearable
        style="width: 140px;"
        v-if="activeTab === 'all'"
      >
        <el-option
          v-for="(name, key) in refundStatusOptions"
          :key="key"
          :label="name"
          :value="key"
        />
      </el-select>
      <el-select
        v-model="queryParams.abnormal_reason_code"
        placeholder="异常原因"
        clearable
        style="width: 140px;"
        v-if="activeTab === 'abnormal'"
      >
        <el-option
          v-for="item in abnormalReasonOptions"
          :key="item.code"
          :label="item.name"
          :value="item.code"
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
      <el-table
        :data="tableData"
        stripe
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="id" label="订单号" width="160">
          <template #default="scope">
            <span class="order-id">{{ scope.row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="customer_nickname" label="用户" width="120">
          <template #default="scope">
            <div v-if="scope.row.customer_nickname">
              <div>{{ scope.row.customer_nickname }}</div>
              <div style="font-size: 12px; color: #999;">ID: {{ scope.row.user_id }}</div>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="teacher_nickname" label="老师" width="120">
          <template #default="scope">
            <div v-if="scope.row.teacher_nickname">
              <div>{{ scope.row.teacher_nickname }}</div>
              <div style="font-size: 12px; color: #999;">ID: {{ scope.row.teacher_id }}</div>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="refund_status_name" label="退款状态" width="120">
          <template #default="scope">
            <div style="display: flex; flex-direction: column; gap: 4px;">
              <el-tag :type="getRefundStatusType(scope.row.refund_status)" size="small">
                {{ scope.row.refund_status_name }}
              </el-tag>
              <div v-if="scope.row.is_teacher_overdue">
                <el-tag type="danger" size="small" effect="dark">
                  老师逾期未审
                </el-tag>
              </div>
              <div v-if="scope.row.is_abnormal">
                <el-tag type="warning" size="small" effect="dark">
                  异常订单
                </el-tag>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="order_status_name" label="订单状态" width="100">
          <template #default="scope">
            <el-tag :type="getOrderStatusType(scope.row.status)" size="small">
              {{ scope.row.status_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="refund_amount" label="退款金额" width="100">
          <template #default="scope">
            <span style="color: #ff6b35; font-weight: bold;">
              ¥{{ scope.row.refund_amount?.toFixed(2) || '0.00' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="pay_amount" label="订单金额" width="100">
          <template #default="scope">
            ¥{{ scope.row.pay_amount?.toFixed(2) || '0.00' }}
          </template>
        </el-table-column>
        <el-table-column prop="refund_reason" label="退款申请理由" min-width="180" v-if="activeTab === 'pending'">
          <template #default="scope">
            <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
              {{ scope.row.refund_reason || '-' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="abnormal_reason" label="异常原因" min-width="150" v-if="activeTab === 'abnormal'">
          <template #default="scope">
            <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
              {{ scope.row.abnormal_reason || scope.row.abnormal_reason_name || '-' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="凭证" width="200" v-if="activeTab === 'pending'">
          <template #default="scope">
            <div style="display: flex; gap: 4px;" v-if="scope.row.refund_proofs?.length">
              <el-image
                v-for="(proof, index) in scope.row.refund_proofs.slice(0, 3)"
                :key="index"
                :src="proof"
                fit="cover"
                style="width: 50px; height: 50px; border-radius: 4px; cursor: pointer;"
                :preview-src-list="scope.row.refund_proofs"
              >
                <template #error>
                  <el-icon :size="24"><Picture /></el-icon>
                </template>
              </el-image>
              <span v-if="scope.row.refund_proofs.length > 3" style="color: #999; font-size: 12px; line-height: 50px;">
                +{{ scope.row.refund_proofs.length - 3 }}
              </span>
            </div>
            <span v-else style="color: #999;">无凭证</span>
          </template>
        </el-table-column>
        <el-table-column prop="refund_time" label="申请时间" width="160" />
        <el-table-column label="操作" fixed="right" width="220">
          <template #default="scope">
            <div class="operation-btns">
              <el-button type="primary" link @click="handleView(scope.row)">
                详情
              </el-button>
              <el-button
                v-if="(scope.row.refund_status === 'pending') || activeTab === 'abnormal'"
                type="success"
                link
                @click="handleAudit(scope.row)"
              >
                审核
              </el-button>
              <el-button
                v-if="activeTab === 'abnormal'"
                type="warning"
                link
                @click="handleForceHandle(scope.row)"
              >
                强制处理
              </el-button>
              <el-button
                v-if="!scope.row.is_abnormal && scope.row.refund_status"
                type="danger"
                link
                @click="handleMarkAbnormal(scope.row)"
              >
                标记异常
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
    
    <el-dialog
      v-model="detailVisible"
      title="退款详情"
      width="800px"
    >
      <el-descriptions :column="2" border v-if="currentRefund">
        <el-descriptions-item label="订单号">{{ currentRefund.id }}</el-descriptions-item>
        <el-descriptions-item label="订单状态">
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <el-tag :type="getOrderStatusType(currentRefund.status)">
              {{ currentRefund.status_name }}
            </el-tag>
            <el-tag v-if="currentRefund.is_abnormal" type="warning" effect="dark">
              异常订单
            </el-tag>
            <el-tag :type="getRefundStatusType(currentRefund.refund_status)">
              {{ currentRefund.refund_status_name }}
            </el-tag>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="用户">
          {{ currentRefund.customer_nickname }} (ID: {{ currentRefund.user_id }})
        </el-descriptions-item>
        <el-descriptions-item label="老师">
          {{ currentRefund.teacher_nickname || '-' }} (ID: {{ currentRefund.teacher_id || '-' }})
        </el-descriptions-item>
        <el-descriptions-item label="订单金额">¥{{ currentRefund.total_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="实付金额">
          <span style="color: #ff6b35; font-weight: bold;">
            ¥{{ currentRefund.pay_amount?.toFixed(2) }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="申请退款金额">
          <span style="color: #ff6b35; font-weight: bold;">
            ¥{{ currentRefund.refund_amount?.toFixed(2) || '0.00' }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="申请时间">
          {{ currentRefund.refund_time || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="退款申请理由" :span="2">
          <div style="white-space: pre-wrap; line-height: 1.6;">
            {{ currentRefund.refund_reason || '暂无' }}
          </div>
        </el-descriptions-item>
      </el-descriptions>
      
      <div v-if="currentRefund.refund_proofs?.length" style="margin-top: 20px;">
        <h4 style="margin-bottom: 12px; font-weight: 600;">退款凭证</h4>
        <div style="display: flex; flex-wrap: wrap; gap: 12px;">
          <el-image
            v-for="(proof, index) in currentRefund.refund_proofs"
            :key="index"
            :src="proof"
            fit="cover"
            style="width: 120px; height: 120px; border-radius: 8px; cursor: pointer;"
            :preview-src-list="currentRefund.refund_proofs"
          >
            <template #error>
              <div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #f5f5f5;">
                <el-icon :size="32"><Picture /></el-icon>
              </div>
            </template>
          </el-image>
        </div>
      </div>
      
      <div v-if="currentRefund.items?.length" style="margin-top: 20px;">
        <h4 style="margin-bottom: 12px; font-weight: 600;">商品信息</h4>
        <el-table :data="currentRefund.items" size="small">
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
        <el-button
          v-if="(currentRefund.refund_status === 'pending') || activeTab === 'abnormal'"
          type="success"
          @click="handleAudit(currentRefund)"
        >
          审核
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="auditDialogVisible"
      title="退款审核"
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-if="currentRefund" style="margin-bottom: 20px; padding: 16px; background: #f5f5f5; border-radius: 8px;">
        <div style="font-weight: 600; margin-bottom: 8px;">订单信息</div>
        <div style="display: flex; justify-content: space-between; color: #666; font-size: 14px;">
          <span>订单号：{{ currentRefund.id }}</span>
          <span>实付金额：<span style="color: #ff6b35; font-weight: bold;">¥{{ currentRefund.pay_amount?.toFixed(2) }}</span></span>
        </div>
        <div v-if="currentRefund.is_teacher_overdue" style="margin-top: 8px; color: #f56c6c;">
          ⚠️ 老师已超过24小时未审核，管理员介入处理
        </div>
        <div v-if="currentRefund.is_abnormal" style="margin-top: 8px; color: #e6a23c;">
          ⚠️ 该订单为异常订单，请谨慎处理
        </div>
      </div>
      
      <el-form :model="auditForm" label-width="100px">
        <el-form-item label="审核操作" required>
          <el-radio-group v-model="auditForm.action">
            <el-radio value="approve" style="margin-right: 20px;">
              <span style="color: #67c23a; font-weight: bold;">同意退款</span>
            </el-radio>
            <el-radio value="reject">
              <span style="color: #f56c6c; font-weight: bold;">拒绝退款</span>
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="退款金额" v-if="auditForm.action === 'approve'">
          <el-input-number
            v-model="auditForm.refund_amount"
            :min="0"
            :max="currentRefund?.pay_amount || 999999"
            :precision="2"
            :step="10"
            style="width: 100%;"
          />
          <div style="font-size: 12px; color: #999; margin-top: 4px;">
            退款金额不能超过订单实付金额 ¥{{ currentRefund?.pay_amount?.toFixed(2) || '0.00' }}
          </div>
        </el-form-item>
        <el-form-item label="理由说明" :required="auditForm.action === 'reject'">
          <el-input
            v-model="auditForm.reason"
            type="textarea"
            :rows="4"
            :placeholder="auditForm.action === 'reject' ? '请输入拒绝理由（至少10个字符）' : '请输入处理理由（选填）'"
          />
          <div style="font-size: 12px; color: #999; margin-top: 4px;">
            已输入 {{ auditForm.reason.length }} 个字符
            <span v-if="auditForm.action === 'reject'" style="color: #f56c6c;">（至少10个字符）</span>
          </div>
        </el-form-item>
      </el-form>
      
      <div style="margin-top: 16px; padding: 12px; background: #ecf5ff; border-radius: 4px; color: #409eff;">
        <div style="font-weight: 600;">⚠️ 操作提示</div>
        <ul style="margin: 8px 0 0 16px; padding: 0;">
          <li v-if="auditForm.action === 'approve'">同意退款后，订单状态将更新为"退款中"，并同步推送消息通知用户</li>
          <li v-else>拒绝退款后，订单将恢复原状态，并同步推送消息通知用户</li>
        </ul>
      </div>
      
      <template #footer>
        <el-button @click="auditDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="confirmAudit"
          :loading="submitting"
          :disabled="auditForm.action === 'reject' && auditForm.reason.length < 10"
        >
          确认审核
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="forceHandleDialogVisible"
      title="强制处理异常退款"
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-if="currentRefund" style="margin-bottom: 20px; padding: 16px; background: #fdf6ec; border-radius: 8px; border: 1px solid #fde2c2;">
        <div style="font-weight: 600; color: #e6a23c; margin-bottom: 8px;">
          ⚠️ 异常订单处理
        </div>
        <div style="color: #666; font-size: 14px;">
          <div>订单号：{{ currentRefund.id }}</div>
          <div>当前订单状态：{{ currentRefund.status_name }}</div>
          <div>当前退款状态：{{ currentRefund.refund_status_name }}</div>
          <div v-if="currentRefund.abnormal_reason">异常原因：{{ currentRefund.abnormal_reason }}</div>
        </div>
      </div>
      
      <el-form :model="forceHandleForm" label-width="120px">
        <el-form-item label="目标退款状态">
          <el-select v-model="forceHandleForm.target_status" placeholder="选择退款状态（选填）" style="width: 100%;">
            <el-option label="不修改" value="" />
            <el-option label="同意退款" value="approved" />
            <el-option label="拒绝退款" value="rejected" />
            <el-option label="退款完成" value="completed" />
          </el-select>
          <div style="font-size: 12px; color: #999; margin-top: 4px;">
            选择后将强制更新退款状态
          </div>
        </el-form-item>
        <el-form-item label="目标订单状态">
          <el-select v-model="forceHandleForm.order_status" placeholder="选择订单状态（选填）" style="width: 100%;">
            <el-option label="不修改" value="" />
            <el-option label="已取消" value="cancelled" />
            <el-option label="已完成" value="completed" />
            <el-option label="退款中" value="refunding" />
          </el-select>
          <div style="font-size: 12px; color: #999; margin-top: 4px;">
            选择后将强制联动订单状态
          </div>
        </el-form-item>
        <el-form-item label="处理理由" required>
          <el-input
            v-model="forceHandleForm.reason"
            type="textarea"
            :rows="4"
            placeholder="请输入处理理由（至少10个字符）"
          />
          <div style="font-size: 12px; color: #999; margin-top: 4px;">
            已输入 {{ forceHandleForm.reason.length }} 个字符（至少10个字符）
          </div>
        </el-form-item>
      </el-form>
      
      <div style="margin-top: 16px; padding: 12px; background: #fef0f0; border-radius: 4px; color: #f56c6c;">
        <div style="font-weight: 600;">⚠️ 警告</div>
        <ul style="margin: 8px 0 0 16px; padding: 0;">
          <li>强制处理将直接修改订单和退款状态，请谨慎操作</li>
          <li>处理后将同步推送消息通知用户</li>
          <li>此操作将记录到审计日志</li>
        </ul>
      </div>
      
      <template #footer>
        <el-button @click="forceHandleDialogVisible = false">取消</el-button>
        <el-button
          type="danger"
          @click="confirmForceHandle"
          :loading="submitting"
          :disabled="forceHandleForm.reason.length < 10"
        >
          确认强制处理
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="markAbnormalDialogVisible"
      title="标记为异常"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="markAbnormalForm" label-width="100px">
        <el-form-item label="异常原因" required>
          <el-select v-model="markAbnormalForm.reason_code" placeholder="选择异常类型" style="width: 100%;">
            <el-option
              v-for="item in abnormalReasonOptions"
              :key="item.code"
              :label="item.name"
              :value="item.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="详细说明" required>
          <el-input
            v-model="markAbnormalForm.reason"
            type="textarea"
            :rows="4"
            placeholder="请输入详细说明（至少10个字符）"
          />
          <div style="font-size: 12px; color: #999; margin-top: 4px;">
            已输入 {{ markAbnormalForm.reason.length }} 个字符（至少10个字符）
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="markAbnormalDialogVisible = false">取消</el-button>
        <el-button
          type="warning"
          @click="confirmMarkAbnormal"
          :loading="submitting"
          :disabled="markAbnormalForm.reason.length < 10"
        >
          确认标记
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="statsDialogVisible"
      title="退款统计"
      width="900px"
    >
      <div style="margin-bottom: 20px;">
        <el-form :inline="true" :model="statsForm">
          <el-form-item label="时间范围">
            <el-radio-group v-model="statsForm.period">
              <el-radio value="week">本周</el-radio>
              <el-radio value="month">本月</el-radio>
              <el-radio value="quarter">本季度</el-radio>
              <el-radio value="year">本年</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchStats">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button type="success" @click="exportStats">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <div v-if="statsData.summary" style="margin-bottom: 20px;">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card shadow="hover">
              <div style="text-align: center;">
                <div style="font-size: 12px; color: #999;">退款申请数</div>
                <div style="font-size: 28px; font-weight: bold; color: #409eff; margin-top: 8px;">
                  {{ statsData.summary.total }}
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <div style="text-align: center;">
                <div style="font-size: 12px; color: #999;">已同意</div>
                <div style="font-size: 28px; font-weight: bold; color: #67c23a; margin-top: 8px;">
                  {{ statsData.summary.approved }}
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <div style="text-align: center;">
                <div style="font-size: 12px; color: #999;">待处理</div>
                <div style="font-size: 28px; font-weight: bold; color: #e6a23c; margin-top: 8px;">
                  {{ statsData.summary.pending }}
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <div style="text-align: center;">
                <div style="font-size: 12px; color: #999;">退款总额</div>
                <div style="font-size: 24px; font-weight: bold; color: #ff6b35; margin-top: 8px;">
                  ¥{{ statsData.summary.total_amount?.toFixed(2) }}
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
      
      <div v-if="statsData.status_stats" style="margin-bottom: 20px;">
        <h4 style="margin-bottom: 12px; font-weight: 600;">按状态统计</h4>
        <el-table :data="statusStatsList" size="small">
          <el-table-column prop="key" label="状态码" />
          <el-table-column prop="name" label="状态名称" />
          <el-table-column prop="count" label="数量">
            <template #default="scope">
              <el-tag v-if="scope.row.count > 0" :type="getRefundStatusType(scope.row.key)" size="small">
                {{ scope.row.count }}
              </el-tag>
              <span v-else>0</span>
            </template>
          </el-table-column>
          <el-table-column prop="percentage" label="占比" width="150">
            <template #default="scope">
              <el-progress
                :percentage="scope.row.percentage"
                :stroke-width="10"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <div v-if="statsData.daily_data?.length">
        <h4 style="margin-bottom: 12px; font-weight: 600;">每日趋势</h4>
        <el-table :data="statsData.daily_data" size="small">
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="total" label="申请数" width="80">
            <template #default="scope">
              <el-tag type="primary" size="small">{{ scope.row.total }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="approved" label="同意数" width="80">
            <template #default="scope">
              <el-tag type="success" size="small">{{ scope.row.approved }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="退款金额">
            <template #default="scope">
              <span style="color: #ff6b35; font-weight: bold;">¥{{ scope.row.amount?.toFixed(2) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <template #footer>
        <el-button @click="statsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataLine, Search, Refresh, Picture } from '@element-plus/icons-vue'
import {
  getRefunds,
  getPendingRefunds,
  getAbnormalRefunds,
  auditRefund,
  forceHandleRefund,
  markAsAbnormal,
  getRefundStats,
  exportRefundStats
} from '@/api/refunds'

const loading = ref(false)
const submitting = ref(false)
const tableData = ref([])
const total = ref(0)
const pendingCount = ref(0)
const abnormalCount = ref(0)
const activeTab = ref('all')
const dateRange = ref([])

const detailVisible = ref(false)
const auditDialogVisible = ref(false)
const forceHandleDialogVisible = ref(false)
const markAbnormalDialogVisible = ref(false)
const statsDialogVisible = ref(false)

const currentRefund = ref(null)
const statsData = ref({})

const refundStatusOptions = {
  pending: '待审核',
  approved: '已同意',
  rejected: '已拒绝',
  completed: '已完成'
}

const abnormalReasonOptions = [
  { code: 'system_error', name: '系统错误' },
  { code: 'payment_failed', name: '支付失败' },
  { code: 'refund_failed', name: '退款失败' },
  { code: 'status_stuck', name: '状态卡死' },
  { code: 'user_complaint', name: '用户投诉' },
  { code: 'other', name: '其他问题' }
]

const orderStatusOptions = {
  pending: '待付款',
  pending_accept: '待接单',
  accepted: '已接单',
  in_progress: '制作中',
  paid: '待发货',
  shipped: '待收货',
  delivered: '已送达',
  completed: '已完成',
  cancelled: '已取消',
  refunding: '退款中'
}

const queryParams = reactive({
  page: 1,
  size: 10,
  keyword: '',
  refund_status: '',
  abnormal_reason_code: '',
  is_abnormal: null,
  start_date: '',
  end_date: ''
})

const auditForm = reactive({
  action: 'approve',
  refund_amount: 0,
  reason: ''
})

const forceHandleForm = reactive({
  target_status: '',
  order_status: '',
  reason: ''
})

const markAbnormalForm = reactive({
  reason_code: 'system_error',
  reason: ''
})

const statsForm = reactive({
  period: 'week'
})

const statusStatsList = computed(() => {
  if (!statsData.value.status_stats) return []
  const total = Object.values(statsData.value.status_stats).reduce((sum, item) => sum + (item.count || 0), 0)
  return Object.entries(statsData.value.status_stats).map(([key, item]) => ({
    key,
    name: item.name,
    count: item.count,
    percentage: total > 0 ? Math.round((item.count / total) * 100) : 0
  }))
})

const getOrderStatusType = (status) => {
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
    refunding: 'warning',
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
    if (queryParams.refund_status) params.refund_status = queryParams.refund_status
    if (queryParams.abnormal_reason_code) params.abnormal_reason_code = queryParams.abnormal_reason_code
    if (queryParams.is_abnormal !== null) params.is_abnormal = queryParams.is_abnormal
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]?.toISOString().split('T')[0]
      params.end_date = dateRange.value[1]?.toISOString().split('T')[0]
    }
    
    let res
    if (activeTab.value === 'pending') {
      res = await getPendingRefunds(params)
    } else if (activeTab.value === 'abnormal') {
      res = await getAbnormalRefunds(params)
    } else {
      res = await getRefunds(params)
    }
    
    if (res.code === 0) {
      tableData.value = res.data.list || []
      total.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取数据失败:', e)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const fetchPendingCount = async () => {
  try {
    const params = { page: 1, size: 1 }
    const res = await getPendingRefunds(params)
    if (res.code === 0) {
      pendingCount.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取待审核数量失败:', e)
  }
}

const fetchAbnormalCount = async () => {
  try {
    const params = { page: 1, size: 1 }
    const res = await getAbnormalRefunds(params)
    if (res.code === 0) {
      abnormalCount.value = res.data.total || 0
    }
  } catch (e) {
    console.error('获取异常退款数量失败:', e)
  }
}

const handleTabChange = (tab) => {
  if (tab === 'pending') {
    queryParams.is_abnormal = false
    queryParams.refund_status = 'pending'
  } else if (tab === 'abnormal') {
    queryParams.is_abnormal = true
    queryParams.refund_status = ''
  } else {
    queryParams.is_abnormal = null
    queryParams.refund_status = ''
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
  queryParams.refund_status = ''
  queryParams.abnormal_reason_code = ''
  if (activeTab.value === 'pending') {
    queryParams.is_abnormal = false
    queryParams.refund_status = 'pending'
  } else if (activeTab.value === 'abnormal') {
    queryParams.is_abnormal = true
    queryParams.refund_status = ''
  } else {
    queryParams.is_abnormal = null
    queryParams.refund_status = ''
  }
  dateRange.value = []
  fetchData()
}

const handleView = (row) => {
  currentRefund.value = row
  detailVisible.value = true
}

const handleAudit = (row) => {
  currentRefund.value = row
  auditForm.action = 'approve'
  auditForm.refund_amount = row.pay_amount || 0
  auditForm.reason = ''
  auditDialogVisible.value = true
}

const confirmAudit = async () => {
  if (auditForm.action === 'reject' && auditForm.reason.length < 10) {
    ElMessage.warning('拒绝理由不能少于10个字符')
    return
  }
  
  try {
    let confirmMsg = ''
    if (auditForm.action === 'approve') {
      confirmMsg = `确定要同意退款吗？退款金额：¥${auditForm.refund_amount.toFixed(2)}。同意后订单状态将更新为"退款中"，并同步推送消息通知用户。`
    } else {
      confirmMsg = '确定要拒绝退款吗？拒绝后订单将恢复原状态，并同步推送消息通知用户。'
    }
    
    await ElMessageBox.confirm(confirmMsg, '确认审核', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    submitting.value = true
    const data = {
      action: auditForm.action,
      reason: auditForm.reason
    }
    if (auditForm.action === 'approve') {
      data.refund_amount = auditForm.refund_amount
    }
    
    const res = await auditRefund(currentRefund.value.id, data)
    if (res.code === 0) {
      ElMessage.success('审核成功')
      auditDialogVisible.value = false
      fetchData()
      fetchPendingCount()
      fetchAbnormalCount()
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.msg || '审核失败')
    }
  } finally {
    submitting.value = false
  }
}

const handleForceHandle = (row) => {
  currentRefund.value = row
  forceHandleForm.target_status = ''
  forceHandleForm.order_status = ''
  forceHandleForm.reason = ''
  forceHandleDialogVisible.value = true
}

const confirmForceHandle = async () => {
  if (forceHandleForm.reason.length < 10) {
    ElMessage.warning('处理理由不能少于10个字符')
    return
  }
  if (!forceHandleForm.target_status && !forceHandleForm.order_status) {
    ElMessage.warning('请至少选择一个要修改的状态')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      '确定要强制处理此异常退款吗？此操作将直接修改订单和退款状态，并同步推送消息通知用户。此操作不可恢复！',
      '确认强制处理',
      {
        confirmButtonText: '确认处理',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    submitting.value = true
    const data = { reason: forceHandleForm.reason }
    if (forceHandleForm.target_status) {
      data.target_status = forceHandleForm.target_status
    }
    if (forceHandleForm.order_status) {
      data.order_status = forceHandleForm.order_status
    }
    
    const res = await forceHandleRefund(currentRefund.value.id, data)
    if (res.code === 0) {
      ElMessage.success('处理成功')
      forceHandleDialogVisible.value = false
      fetchData()
      fetchPendingCount()
      fetchAbnormalCount()
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.msg || '处理失败')
    }
  } finally {
    submitting.value = false
  }
}

const handleMarkAbnormal = (row) => {
  currentRefund.value = row
  markAbnormalForm.reason_code = 'system_error'
  markAbnormalForm.reason = ''
  markAbnormalDialogVisible.value = true
}

const confirmMarkAbnormal = async () => {
  if (markAbnormalForm.reason.length < 10) {
    ElMessage.warning('详细说明不能少于10个字符')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      '确定要将此订单标记为异常吗？标记后将进入异常退款列表。',
      '确认标记',
      {
        confirmButtonText: '确认标记',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    submitting.value = true
    const res = await markAsAbnormal(currentRefund.value.id, {
      reason_code: markAbnormalForm.reason_code,
      reason: markAbnormalForm.reason
    })
    if (res.code === 0) {
      ElMessage.success('标记成功')
      markAbnormalDialogVisible.value = false
      fetchData()
      fetchPendingCount()
      fetchAbnormalCount()
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.msg || '标记失败')
    }
  } finally {
    submitting.value = false
  }
}

const openStatsDialog = () => {
  statsDialogVisible.value = true
  fetchStats()
}

const fetchStats = async () => {
  try {
    const params = {
      period: statsForm.period
    }
    
    const res = await getRefundStats(params)
    if (res.code === 0) {
      statsData.value = res.data
    }
  } catch (e) {
    console.error('获取统计数据失败:', e)
    ElMessage.error('获取统计数据失败')
  }
}

const exportStats = async () => {
  try {
    const params = {
      period: statsForm.period
    }
    
    const res = await exportRefundStats(params)
    if (res.code === 0) {
      const { csv_content, filename } = res.data
      const blob = new Blob(['\ufeff' + csv_content], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = filename
      link.click()
      ElMessage.success('导出成功')
    }
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  fetchData()
  fetchPendingCount()
  fetchAbnormalCount()
})
</script>

<style scoped>
.page-card {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
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
