<template>
  <el-container class="layout">
    <!-- 左侧导航 -->
    <el-aside width="200px" class="aside">
      <div class="logo">
        <el-icon :size="22"><Cpu /></el-icon>
        <span>数字孪生车间</span>
      </div>
      <el-menu :default-active="activeMenu" router class="menu" background-color="#001529"
               text-color="#a6adb4" active-text-color="#409eff">
        <el-menu-item v-for="r in menuItems" :key="r.path" :index="r.path">
          <el-icon><component :is="r.icon" /></el-icon>
          <span>{{ r.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <span class="page-title">{{ currentTitle }}</span>
        <span class="header-right">数字孪生车间智能监控与运维平台 · B/S 单机演示</span>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const menuItems = [
  { path: '/twin', title: '数字孪生可视化', icon: 'Monitor' },
  { path: '/equipment', title: '车间设备台账', icon: 'Box' },
  { path: '/monitoring', title: '实时数据监测', icon: 'DataLine' },
  { path: '/evaluation', title: '健康与能耗评估', icon: 'Odometer' },
  { path: '/alerts', title: '孪生预警中心', icon: 'Bell' },
  { path: '/work-orders', title: '运维工单管理', icon: 'Tickets' },
]

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '')
</script>

<style scoped>
.layout {
  height: 100vh;
}
.aside {
  background: #001529;
  color: #fff;
}
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 60px;
  padding: 0 20px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.menu {
  border-right: none;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #eee;
}
.page-title {
  font-size: 18px;
  font-weight: 600;
}
.header-right {
  color: #999;
  font-size: 13px;
}
.main {
  background: #f5f7fa;
  padding: 12px;
}
</style>
