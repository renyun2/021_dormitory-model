<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { http } from '../api'

const active = ref<any[]>([])
const apps = ref<any[]>([])
const hist = ref<any[]>([])

const vacant = ref<any[]>([])

const newSwap = reactive({
  checkin_record_id: 0,
  reason: '',
})

const exec = reactive({
  swap_application_id: 0,
  target_bed_id: 0,
})

async function load() {
  const [a, s, h, b] = await Promise.all([
    http.get('/checkin-records/active'),
    http.get('/swap-applications'),
    http.get('/swap-histories'),
    http.get('/beds', { params: { status: 'vacant' } }),
  ])
  active.value = a.data
  apps.value = s.data
  hist.value = h.data
  vacant.value = b.data.slice(0, 200)
}

async function createSwap() {
  await http.post('/swap-applications', {
    checkin_record_id: newSwap.checkin_record_id,
    reason: newSwap.reason,
    expected_room_hint: null,
  })
  ElMessage.success('调换申请已提交')
  newSwap.reason = ''
  await load()
}

async function approve(id: number) {
  await http.patch(`/swap-applications/${id}/status`, { status: 'approved' })
  ElMessage.success('已批准')
  exec.swap_application_id = id
  exec.target_bed_id = vacant.value[0]?.id ?? 0
  await load()
}

async function doExec() {
  await http.post('/swap-applications/execute', {
    swap_application_id: exec.swap_application_id,
    target_bed_id: exec.target_bed_id,
  })
  ElMessage.success('调换已完成')
  await load()
}

onMounted(load)
</script>

<template>
  <el-row :gutter="16">
    <el-col :span="8">
      <el-card header="在住记录 ID 参考">
        <el-table :data="active.slice(0, 12)" height="240">
          <el-table-column prop="id" label="ID" />
          <el-table-column prop="employee_name" label="姓名" />
          <el-table-column prop="bed_id" label="床位" />
        </el-table>
      </el-card>
      <el-card header="发起调换" style="margin-top: 16px">
        <el-form label-width="110px">
          <el-form-item label="入住记录 ID">
            <el-input-number v-model="newSwap.checkin_record_id" :min="1" />
          </el-form-item>
          <el-form-item label="原因">
            <el-input v-model="newSwap.reason" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="createSwap">提交申请</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>
    <el-col :span="8">
      <el-card header="审批与执行">
        <el-table :data="apps.slice(0, 12)" height="220">
          <el-table-column prop="id" label="申请" width="70" />
          <el-table-column prop="checkin_record_id" label="入住ID" />
          <el-table-column prop="status" label="状态" />
          <el-table-column label="操作" width="90">
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
            <el-input-number v-model="exec.swap_application_id" :min="0" />
          </el-form-item>
          <el-form-item label="目标床位 ID">
            <el-select v-model="exec.target_bed_id" filterable style="width: 200px">
              <el-option v-for="b in vacant" :key="b.id" :label="`${b.id} ${b.bed_code}`" :value="b.id" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="danger" @click="doExec">执行调换</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>
    <el-col :span="8">
      <el-card header="调换历史">
        <el-table :data="hist.slice(0, 20)" height="520">
          <el-table-column prop="id" label="#" width="60" />
          <el-table-column prop="from_bed_id" label="原床" />
          <el-table-column prop="to_bed_id" label="新床" />
          <el-table-column prop="operated_at" label="时间" />
        </el-table>
      </el-card>
    </el-col>
  </el-row>
</template>
