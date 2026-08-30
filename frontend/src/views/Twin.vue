<template>
  <div class="twin-page">
    <!-- 顶部统计概览 -->
    <el-row :gutter="12" class="stat-row">
      <el-col :span="6" v-for="s in stats" :key="s.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">{{ s.label }}</div>
          <div class="stat-value" :style="{ color: s.color }">{{ s.value }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="twin-card">
      <template #header>
        <div class="card-header">
          <span><el-icon><Monitor /></el-icon> 车间布局 · 设备孪生状态</span>
          <div>
            <span class="legend" v-for="l in legend" :key="l.label">
              <i class="dot" :style="{ background: l.color }"></i>{{ l.label }}
            </span>
            <el-button size="small" type="primary" :icon="Refresh" :loading="loading" @click="load">
              刷新孪生
            </el-button>
          </div>
        </div>
      </template>

      <div class="floor" v-loading="loading">
        <div class="floor-title">智能车间 3 号产线</div>
        <div class="device-grid">
          <div
            v-for="(eq, i) in equipment"
            :key="eq.id"
            class="device-node"
            :class="`status-${eq.twin_status}`"
            @click="openDetail(eq)"
          >
            <div class="node-head">
              <span class="node-code">{{ eq.device_code }}</span>
              <i class="pulse" :class="eq.twin_status === '报警' ? 'on' : ''"></i>
            </div>
            <div class="node-name">{{ eq.name }}</div>
            <div class="node-station">{{ eq.station }}</div>
            <div class="node-tags">
              <el-tag size="small" :type="statusType(eq.twin_status)">{{ eq.twin_status }}</el-tag>
              <el-tag size="small" :type="gradeType(eq.health_grade)">{{ eq.health_grade }}</el-tag>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 设备详情抽屉 -->
    <el-drawer v-model="drawer" size="420px" :title="current?.name">
      <template v-if="current">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="设备编号">{{ current.device_code }}</el-descriptions-item>
          <el-descriptions-item label="型号">{{ current.model || '-' }}</el-descriptions-item>
          <el-descriptions-item label="工位">{{ current.station || '-' }}</el-descriptions-item>
          <el-descriptions-item label="投运日期">{{ current.install_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="孪生状态">
            <el-tag :type="statusType(current.twin_status)">{{ current.twin_status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="健康等级">
            <el-tag :type="gradeType(current.health_grade)">{{ current.health_grade }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div class="drawer-actions">
          <el-button type="primary" :icon="DataLine" @click="go('/monitoring', current)">
            实时监测
          </el-button>
          <el-button :icon="Odometer" @click="go('/evaluation', current)">健康评估</el-button>
          <el-button :icon="Search" @click="quickDiagnose(current)">一键诊断</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, DataLine, Odometer, Search, Monitor } from '@element-plus/icons-vue'
import { listEquipment, diagnose } from '../api'

const router = useRouter()
const equipment = ref([])
const loading = ref(false)
const drawer = ref(false)
const current = ref(null)

const legend = [
  { label: '运行', color: '#67c23a' },
  { label: '待机', color: '#e6a23c' },
  { label: '报警', color: '#f56c6c' },
]

const stats = computed(() => {
  const total = equipment.value.length
  const run = equipment.value.filter((e) => e.twin_status === '运行').length
  const alarm = equipment.value.filter((e) => e.twin_status === '报警').length
  const severe = equipment.value.filter((e) => ['严重', '预警'].includes(e.health_grade)).length
  return [
    { label: '设备总数', value: total, color: '#409eff' },
    { label: '运行中', value: run, color: '#67c23a' },
    { label: '报警中', value: alarm, color: '#f56c6c' },
    { label: '需关注(预警/严重)', value: severe, color: '#e6a23c' },
  ]
})

async function load() {
  loading.value = true
  try {
    const data = await listEquipment({ page: 1, page_size: 200 })
    equipment.value = data.items || []
  } finally {
    loading.value = false
  }
}

function openDetail(eq) {
  current.value = eq
  drawer.value = true
}

function go(path, eq) {
  drawer.value = false
  router.push({ path, query: { id: eq.id, code: eq.device_code } })
}

async function quickDiagnose(eq) {
  drawer.value = false
  try {
    const res = await diagnose(eq.id, { create_order: false })
    const top = res.diagnoses?.[0]
    ElMessage({
      message: top
        ? `诊断结论[${top.code}] ${top.name}（${top.level}）· ${top.advice}`
        : '未命中明显故障规则，设备运行状态良好',
      type: top?.level === '严重' ? 'error' : top?.level === '警告' ? 'warning' : 'success',
      duration: 6000,
    })
  } catch {
    /* 错误已由拦截器提示 */
  }
}

function statusType(s) {
  return { 运行: 'success', 待机: 'warning', 报警: 'danger' }[s] || 'info'
}
function gradeType(g) {
  return { 健康: 'success', 注意: 'info', 预警: 'warning', 严重: 'danger' }[g] || 'info'
}

onMounted(load)
</script>

<style scoped>
.stat-row {
  margin-bottom: 12px;
}
.stat-card {
  text-align: center;
}
.stat-label {
  color: #909399;
  font-size: 13px;
}
.stat-value {
  font-size: 26px;
  font-weight: 700;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.legend {
  margin-right: 14px;
  font-size: 13px;
  color: #606266;
}
.legend .dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 5px;
}
.floor {
  border: 1px dashed #c0c4cc;
  border-radius: 8px;
  padding: 16px;
  background: #fafcff;
  min-height: 420px;
}
.floor-title {
  text-align: center;
  font-weight: 600;
  color: #606266;
  margin-bottom: 16px;
}
.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}
.device-node {
  border: 2px solid #dcdfe6;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  background: #fff;
  transition: transform 0.15s;
}
.device-node:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
}
.device-node.status-运行 {
  border-left: 5px solid #67c23a;
}
.device-node.status-待机 {
  border-left: 5px solid #e6a23c;
}
.device-node.status-报警 {
  border-left: 5px solid #f56c6c;
}
.node-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.node-code {
  font-weight: 700;
  color: #303133;
}
.pulse {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #c0c4cc;
}
.pulse.on {
  background: #f56c6c;
  animation: blink 1s infinite;
}
@keyframes blink {
  50% {
    opacity: 0.2;
  }
}
.node-name {
  margin: 6px 0 2px;
  font-size: 14px;
}
.node-station {
  color: #909399;
  font-size: 12px;
  margin-bottom: 8px;
}
.node-tags {
  display: flex;
  gap: 6px;
}
.drawer-actions {
  margin-top: 18px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
