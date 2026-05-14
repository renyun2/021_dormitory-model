<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { http } from '../api'

const apps = ref<any[]>([])
const vacant = ref<any[]>([])

const newApp = reactive({
  applicant_name: '',
  employee_no: '',
  reason: '',
})

const assign = reactive({
  application_id: 0 as number,
  bed_id: 0 as number,
})

async function reload() {
  const [a, b] = await Promise.all([
    http.get('/checkin-applications'),
    http.get('/beds', { params: { status: 'vacant' } }),
  ])
  apps.value = a.data
  vacant.value = b.data.slice(0, 120)
}

function setApprove(id: number, status: string) {
  assign.application_id = id
  assign.bed_id = vacant.value[0]?.id ?? 0
}

async function submitApp() {
  await http.post('/checkin-applications', {
    applicant_name: newApp.applicant_name,
    employee_no: newApp.employee_no || null,
    reason: newApp.reason || null,
    expected_date: null,
  })
  ElMessage.success('入住申请已提交')
  Object.assign(newApp, { applicant_name: '', employee_no: '', reason: '' })
  await reload()
}

async function patch(id: number, status: string) {
  await http.patch(`/checkin-applications/${id}/status`, { status })
  ElMessage.success('状态已更新')
  await reload()
}

async function doAssign() {
  await http.post('/checkin-records/from-application', {
    application_id: assign.application_id,
    bed_id: assign.bed_id,
    checkin_date: new Date().toISOString().slice(0, 10),
    deposit_amount: 800,
    key_received: true,
  })
  ElMessage.success('已分配床位并生成入住记录')
  assign.application_id = 0
  await reload()
}

onMounted(reload)
</script>

<template>
  <el-row :gutter="16">
    <el-col :span="10">
      <el-card header="员工申请入住">
        <el-form label-width="80px">
          <el-form-item label="申请人">
            <el-input v-model="newApp.applicant_name" />
          </el-form-item>
          <el-form-item label="工号">
            <el-input v-model="newApp.employee_no" />
          </el-form-item>
          <el-form-item label="原因">
            <el-input type="textarea" v-model="newApp.reason" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="submitApp">提交</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>
    <el-col :span="14">
      <el-card header="申请审批与床位分配">
        <el-alert type="warning" title="请先对申请 PATCH 设为 approved，再选择床位下达入住。" show-icon class="mb" />
        <el-table :data="apps.slice(0, 18)" stripe>
          <el-table-column prop="id" label="编号" width="70" />
          <el-table-column prop="applicant_name" label="申请人" />
          <el-table-column prop="reason" label="事由" />
          <el-table-column prop="status" label="状态" width="96" />
          <el-table-column label="审批" width="180">
            <template #default="{ row }">
              <el-button size="small" @click="patch(row.id, 'approved')">批准</el-button>
              <el-button size="small" @click="patch(row.id, 'rejected')">拒绝</el-button>
              <el-button size="small" link type="primary" @click="setApprove(row.id, 'assign')">
                选床位
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-divider />
        <el-form inline>
          <el-form-item label="申请ID">
            <el-input-number v-model="assign.application_id" :min="0" />
          </el-form-item>
          <el-form-item label="空闲床位">
            <el-select v-model="assign.bed_id" filterable placeholder="选择床位 ID" style="width: 200px">
              <el-option
                v-for="b in vacant"
                :key="b.id"
                :label="`${b.id} / ${b.bed_code}`"
                :value="b.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="doAssign" :disabled="!assign.application_id || !assign.bed_id">
              分配并入床
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>
  </el-row>
</template>

<style scoped>
.mb {
  margin-bottom: 12px;
}
</style>
