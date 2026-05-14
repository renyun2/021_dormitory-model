<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { http } from '../api'

const dorms = ref(0)
const active = ref(0)
const openRepairs = ref(0)
const arrears = ref(0)

async function load() {
  const [d, a, r, f] = await Promise.all([
    http.get('/dormitories'),
    http.get('/checkin-records/active'),
    http.get('/repair-orders', { params: { status: 'open' } }),
    http.get('/fee-records', { params: { arrears_only: true } }),
  ])
  dorms.value = d.data.length
  active.value = a.data.length
  openRepairs.value = Array.isArray(r.data) ? r.data.length : 0
  arrears.value = Array.isArray(f.data) ? f.data.length : 0
}

onMounted(load)
</script>

<template>
  <el-row :gutter="16">
    <el-col :xs="24" :sm="12" :md="6">
      <el-card shadow="hover">
        <div class="tile-title">宿舍楼栋</div>
        <div class="tile-num">{{ dorms }}</div>
      </el-card>
    </el-col>
    <el-col :xs="24" :sm="12" :md="6">
      <el-card shadow="hover">
        <div class="tile-title">在住人数（记录）</div>
        <div class="tile-num">{{ active }}</div>
      </el-card>
    </el-col>
    <el-col :xs="24" :sm="12" :md="6">
      <el-card shadow="hover">
        <div class="tile-title">待处理报修</div>
        <div class="tile-num">{{ openRepairs }}</div>
      </el-card>
    </el-col>
    <el-col :xs="24" :sm="12" :md="6">
      <el-card shadow="hover">
        <div class="tile-title">欠缴账单条目</div>
        <div class="tile-num">{{ arrears }}</div>
      </el-card>
    </el-col>
  </el-row>
  <el-alert
    class="hint"
    type="info"
    show-icon
    title="Compose 默认入口：浏览器访问 http://localhost:8080"
  />
</template>

<style scoped>
.tile-title {
  color: #666;
  margin-bottom: 8px;
}
.tile-num {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}
.hint {
  margin-top: 24px;
}
</style>
