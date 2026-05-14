<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <el-container class="wrap">
    <el-header class="header">
      <div class="brand">职工宿舍入住管理系统</div>
      <el-menu
        mode="horizontal"
        router
        default-active="/"
        background-color="#1f2d3d"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/">总览</el-menu-item>
        <el-menu-item index="/dorms">宿舍台账</el-menu-item>
        <el-menu-item index="/checkin">入住管理</el-menu-item>
        <el-menu-item index="/swap">调换房间</el-menu-item>
        <el-menu-item index="/checkout">退住管理</el-menu-item>
        <el-menu-item index="/fees">费用管理</el-menu-item>
        <el-menu-item index="/repairs">设施报修</el-menu-item>
      </el-menu>
    </el-header>
    <el-main>
      <RouterView />
    </el-main>
  </el-container>
</template>

<style>
html,
body,
#app {
  margin: 0;
  height: 100%;
}
.wrap {
  min-height: 100vh;
}
.header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: auto !important;
  padding: 8px 16px !important;
  background: #1f2d3d;
}
.brand {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}
</style>
