<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { http } from '../api'

const configs = ref<any[]>([])
const fees = ref<any[]>([])
const year = ref(new Date().getFullYear())
const summary = ref<any>(null)
const arrearsOnly = ref(true)

async function reload() {
  const [c, f] = await Promise.all([
    http.get('/fee-configs'),
    http.get('/fee-records', { params: arrearsOnly.value ? { arrears_only: true } : {} }),
  ])
  configs.value = c.data
  fees.value = f.data.slice(0, 100)
}

async function refreshSummary() {
  const { data } = await http.get('/fee-records/year-summary', { params: { year: year.value } })
  summary.value = data
}

async function saveCfg(row: any) {
  await http.put(`/fee-configs/${row.room_type}`, { monthly_rate: row.monthly_rate })
  ElMessage.success('已更新')
  await reload()
}

async function genMonth() {
  const d = new Date()
  await http.post('/fee-records/generate-month', { year: d.getFullYear(), month: d.getMonth() + 1 })
  ElMessage.success('已按月生成账单（跳过已存在的月份）')
  await reload()
  await refreshSummary()
}

async function pay(row: any) {
  const rest = Number(row.amount_due) - Number(row.amount_paid || 0)
  if (rest <= 0) return
  await http.post(`/fee-records/${row.id}/payment`, { amount: rest })
  ElMessage.success('入账成功')
  await reload()
}

async function remind(row: any) {
  await http.post(`/fee-records/${row.id}/remind`)
  ElMessage.success('已记录提醒')
  await reload()
}

onMounted(async () => {
  await reload()
  await refreshSummary()
})

const summaryRows = computed(() => summary.value?.rows ?? [])
</script>

<template>
  <el-row :gutter="16">
    <el-col :span="10">
      <el-card header="住宿费标准（按月）">
        <el-table :data="configs" border>
          <el-table-column prop="room_type" label="房型" />
          <el-table-column label="金额">
            <template #default="{ row }">
              <el-input-number v-model="row.monthly_rate" :min="0" @change="saveCfg(row)" />
            </template>
          </el-table-column>
        </el-table>
        <div style="margin-top: 12px">
          <el-button type="primary" @click="genMonth">按当前月为在住住户批量生成账单</el-button>
        </div>
      </el-card>
      <el-card header="账单筛选" style="margin-top: 16px">
        <el-switch v-model="arrearsOnly" active-text="仅欠缴" @change="reload" />
      </el-card>
    </el-col>
    <el-col :span="14">
      <el-card header="账单明细（截断展示）">
        <el-table :data="fees" height="360" stripe>
          <el-table-column prop="id" label="#" width="60" />
          <el-table-column prop="billing_month" label="账期月" />
          <el-table-column prop="amount_due" label="应收" />
          <el-table-column prop="amount_paid" label="已收" />
          <el-table-column prop="reminder_count" label="提醒次数" />
          <el-table-column label="操作" width="140">
            <template #default="{ row }">
              <el-button size="small" @click="remind(row)">欠缴提醒</el-button>
              <el-button size="small" type="primary" @click="pay(row)">缴清差额</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
      <el-card header="年度汇总" style="margin-top: 16px">
        <el-space>
          <el-input-number v-model="year" :min="2020" :max="2099" @change="refreshSummary" />
          <el-button @click="refreshSummary">加载</el-button>
        </el-space>
        <el-table :data="summaryRows" style="margin-top: 12px">
          <el-table-column prop="month" label="月份" />
          <el-table-column prop="amount_due" label="应收合计" />
          <el-table-column prop="amount_paid" label="实收合计" />
        </el-table>
      </el-card>
    </el-col>
  </el-row>
</template>
