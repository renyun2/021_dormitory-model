<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { http } from '../api'

const active = ref<any[]>([])
const apps = ref<any[]>([])

const newApp = reactive({
  checkin_record_id: 0,
  planned_date: new Date().toISOString().slice(0, 10),
  reason: '',
})

const complete = reactive({
  checkout_application_id: 0,
  checkout_date: new Date().toISOString().slice(0, 10),
  inspection_damage: false,
  damage_notes: '',
  deposit_refund_amount: 400,
  key_returned: true,
})

async function load() {
  const [a, c] = await Promise.all([
    http.get('/checkin-records/active'),
    http.get('/checkout-applications'),
  ])
  active.value = a.data
  apps.value = c.data
}

async function createApp() {
  await http.post('/checkout-applications', {
    checkin_record_id: newApp.checkin_record_id,
    planned_date: newApp.planned_date,
    reason: newApp.reason || null,
  })
  ElMessage.success('退住申请已提交')
  await load()
}

async function approve(id: number) {
  await http.patch(`/checkout-applications/${id}/status`, { status: 'approved' })
  ElMessage.success('已批准退住')
  complete.checkout_application_id = id
  await load()
}

async function doComplete() {
  await http.post('/checkout-applications/complete', { ...complete })
  ElMessage.success('退住结单完成')
  await load()
}

onMounted(load)
</script>

<template>
  <el-row :gutter="16">
    <el-col :span="10">
      <el-card header="在住记录">
        <el-table :data="active.slice(0, 15)">
          <el-table-column prop="id" label="记录ID" />
          <el-table-column prop="employee_name" label="姓名" />
          <el-table-column prop="deposit_amount" label="押金" />
        </el-table>
      </el-card>
      <el-card header="员工申请退住" style="margin-top: 16px">
        <el-form label-width="110px">
          <el-form-item label="入住记录 ID">
            <el-input-number v-model="newApp.checkin_record_id" :min="1" />
          </el-form-item>
          <el-form-item label="计划退房日">
            <el-date-picker v-model="newApp.planned_date" type="date" value-format="YYYY-MM-DD" />
          </el-form-item>
          <el-form-item label="原因">
            <el-input v-model="newApp.reason" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="createApp">提交申请</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>
    <el-col :span="14">
      <el-card header="审批与查房结单">
        <el-table :data="apps.slice(0, 15)">
          <el-table-column prop="id" label="申请#" />
          <el-table-column prop="checkin_record_id" label="入住ID" />
          <el-table-column prop="planned_date" label="计划" />
          <el-table-column prop="status" label="状态" />
          <el-table-column label="审批" width="100">
            <template #default="{ row }">
              <el-button size="small" @click="approve(row.id)" :disabled="row.status !== 'pending'">
                批准
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-divider />
        <el-form label-width="120px">
          <el-form-item label="申请 ID">
            <el-input-number v-model="complete.checkout_application_id" :min="0" />
          </el-form-item>
          <el-form-item label="实际退房">
            <el-date-picker v-model="complete.checkout_date" type="date" value-format="YYYY-MM-DD" />
          </el-form-item>
          <el-form-item label="有损坏">
            <el-switch v-model="complete.inspection_damage" />
          </el-form-item>
          <el-form-item label="损坏描述">
            <el-input v-model="complete.damage_notes" />
          </el-form-item>
          <el-form-item label="退还押金金额">
            <el-input-number v-model="complete.deposit_refund_amount" :min="0" />
          </el-form-item>
          <el-form-item label="钥匙归还">
            <el-switch v-model="complete.key_returned" />
          </el-form-item>
          <el-form-item>
            <el-button type="danger" @click="doComplete">完成退住</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>
  </el-row>
</template>
