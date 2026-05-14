<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { http } from '../api'

const list = ref<any[]>([])
const rooms = ref<any[]>([])

const form = reactive({
  checkin_record_id: 0,
  category: 'daily',
  description: '',
  urgency: 'normal',
})

const adminRoom = reactive({
  room_id: 0 as number,
  category: 'other',
  description: '',
  urgency: 'normal',
})

const assignBody = reactive({ assignee: '维修班组', status: 'assigned' })

const rating = ref(5)

async function load() {
  const { data } = await http.get('/repair-orders')
  list.value = data
}

async function loadRooms() {
  const { data } = await http.get('/rooms')
  rooms.value = data.slice(0, 500)
}

async function residentSubmit() {
  await http.post(
    '/repair-orders/by-resident',
    {
      category: form.category,
      description: form.description,
      urgency: form.urgency,
    },
    { params: { checkin_record_id: form.checkin_record_id } },
  )
  ElMessage.success('工单已提交')
  form.description = ''
  await load()
}

async function adminSubmit() {
  await http.post('/repair-orders', { ...adminRoom })
  ElMessage.success('工单已建档')
  await load()
}

async function assign(id: number) {
  await http.patch(`/repair-orders/${id}/assign`, assignBody)
  ElMessage.success('已派单')
  await load()
}

async function done(id: number) {
  await http.patch(`/repair-orders/${id}/complete`, { rating: rating.value })
  ElMessage.success('已完成并记分')
  await load()
}

onMounted(async () => {
  await load()
  await loadRooms()
})
</script>

<template>
  <el-row :gutter="16">
    <el-col :span="9">
      <el-card header="住户报修">
        <el-form label-width="110px">
          <el-form-item label="入住记录 ID">
            <el-input-number v-model="form.checkin_record_id" :min="1" />
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="form.category">
              <el-option label="水电" value="water_electric" />
              <el-option label="门窗" value="door_window" />
              <el-option label="床铺" value="bed" />
              <el-option label="空调" value="aircon" />
              <el-option label="日常用品" value="daily" />
              <el-option label="其他" value="other" />
            </el-select>
          </el-form-item>
          <el-form-item label="紧急程度">
            <el-select v-model="form.urgency">
              <el-option label="低" value="low" />
              <el-option label="普通" value="normal" />
              <el-option label="高" value="high" />
              <el-option label="紧急" value="urgent" />
            </el-select>
          </el-form-item>
          <el-form-item label="描述">
            <el-input type="textarea" v-model="form.description" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="residentSubmit">提交（自动绑定所在房间）</el-button>
          </el-form-item>
        </el-form>
      </el-card>
      <el-card header="管理员按房间建档" style="margin-top: 16px">
        <el-form label-width="90px">
          <el-form-item label="房间">
            <el-select v-model="adminRoom.room_id" filterable style="width: 100%">
              <el-option v-for="r in rooms" :key="r.id" :label="`${r.room_number}(#${r.id})`" :value="r.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="adminRoom.description" />
          </el-form-item>
          <el-form-item>
            <el-button @click="adminSubmit">创建</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>
    <el-col :span="15">
      <el-card header="工单队列">
        <el-table :data="list.slice(0, 30)" stripe>
          <el-table-column prop="id" label="#" width="60" />
          <el-table-column prop="room_id" label="房间ID" />
          <el-table-column prop="category" label="类别" />
          <el-table-column prop="urgency" label="紧急度" />
          <el-table-column prop="status" label="状态" />
          <el-table-column prop="assignee" label="负责人" />
          <el-table-column label="流转" width="220">
            <template #default="{ row }">
              <el-button size="small" @click="assign(row.id)" :disabled="row.status === 'done'">接单</el-button>
              <el-button size="small" type="primary" @click="done(row.id)">完成评分</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-divider />
        <el-space>
          <span>完成时评分</span>
          <el-rate v-model="rating" />
        </el-space>
      </el-card>
    </el-col>
  </el-row>
</template>
