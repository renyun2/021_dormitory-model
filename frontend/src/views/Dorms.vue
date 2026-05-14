<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { http } from '../api'

const dorms = ref<{ id: number; building_number: string; gender: string; floors: number }[]>([])
const dormId = ref<number | null>(null)
const occ = ref<any[]>([])
const form = ref({
  building_number: '',
  gender: 'male',
  floors: 5,
})
const roomForm = ref({
  floor_number: 1,
  room_number: '',
  room_type: 'quad',
  status: 'normal',
})

const genderLabel = (g: string) =>
  ({ male: '男', female: '女', mixed: '混合' }[g] ?? g)

async function loadDorms() {
  const { data } = await http.get('/dormitories')
  dorms.value = data
  if (!dormId.value && data.length) dormId.value = data[0].id
}

async function loadOcc() {
  if (!dormId.value) return
  const { data } = await http.get(`/dormitories/${dormId.value}/occupancy`)
  occ.value = data
}

watch(dormId, loadOcc)

async function addDorm() {
  await http.post('/dormitories', form.value)
  ElMessage.success('已新增宿舍楼')
  form.value = { building_number: '', gender: 'male', floors: 5 }
  await loadDorms()
}

async function addRoom() {
  if (!dormId.value) return
  await http.post('/rooms', {
    dormitory_id: dormId.value,
    ...roomForm.value,
  })
  ElMessage.success('已新增房间并生成床位')
  roomForm.value.room_number = ''
  await loadOcc()
}

onMounted(async () => {
  await loadDorms()
  await loadOcc()
})

const occRows = computed(() => {
  const rows: any[] = []
  for (const r of occ.value) {
    for (const b of r.beds) {
      rows.push({
        ...b,
        room_number: r.room_number,
        room_type: r.room_type,
        room_status: r.room_status,
      })
    }
  }
  return rows
})
</script>

<template>
  <div class="row">
    <el-card header="楼栋列表">
      <el-scrollbar max-height="360px">
        <el-radio-group v-model="dormId" class="vertical">
          <div v-for="d in dorms" :key="d.id">
            <el-radio :label="d.id">{{ d.building_number }}（{{ genderLabel(d.gender) }}）</el-radio>
          </div>
        </el-radio-group>
      </el-scrollbar>
      <el-divider />
      <el-form :model="form" label-width="90px">
        <el-form-item label="楼栋号">
          <el-input v-model="form.building_number" placeholder="如 11号楼" />
        </el-form-item>
        <el-form-item label="性别分区">
          <el-select v-model="form.gender">
            <el-option label="男" value="male" />
            <el-option label="女" value="female" />
            <el-option label="混合" value="mixed" />
          </el-select>
        </el-form-item>
        <el-form-item label="层数">
          <el-input-number v-model="form.floors" :min="1" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="addDorm">保存楼栋</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    <el-card header="在当前楼栋新增房间">
      <el-form :model="roomForm" label-width="100px">
        <el-form-item label="楼层">
          <el-input-number v-model="roomForm.floor_number" :min="1" />
        </el-form-item>
        <el-form-item label="房间号文本">
          <el-input v-model="roomForm.room_number" placeholder="如 609" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="roomForm.room_type">
            <el-option label="单人间" value="single" />
            <el-option label="四人间" value="quad" />
            <el-option label="六人间" value="six" />
          </el-select>
        </el-form-item>
        <el-form-item label="房间状态">
          <el-select v-model="roomForm.status">
            <el-option label="正常" value="normal" />
            <el-option label="维修中" value="maintenance" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="addRoom">保存房间与床位</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    <el-card header="床位占用视图" style="flex: 1; min-height: 400px">
      <el-table :data="occRows" height="480" stripe>
        <el-table-column prop="room_number" label="房间" width="88" />
        <el-table-column prop="bed_code" label="床位编号" />
        <el-table-column prop="bed_status" label="床位状态" />
        <el-table-column prop="occupant" label="当前住户" />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}
.vertical {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
</style>
