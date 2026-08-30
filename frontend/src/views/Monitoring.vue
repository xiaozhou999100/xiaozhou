<template>
  <el-row :gutter="12">
    <!-- 左侧：设备选择 + 监测图 -->
    <el-col :span="16">
      <el-card shadow="never">
        <div class="toolbar">
          <span class="label">设备：</span>
          <el-select v-model="equipmentId" filterable style="width: 260px" @change="loadData">
            <el-option v-for="eq in equipment" :key="eq.id" :label="`${eq.device_code} · ${eq.name}`"
                       :value="eq.id" />
          </el-select>
          <span class="label" style="margin-left: 12px">传感器：</span>
          <el-checkbox-group v-model="selectedSensors">
            <el-checkbox v-for="s in sensorOptions" :key="s.key" :value="s.key" :label="s.label" />
          </el-checkbox-group>
          <div class="spacer"></div>
          <el-button :icon="Refresh" :loading="loading" @click="loadData">刷新</el-button>
        </div>

        <div ref="chartRef" class="chart" v-loading="loading"></div>

        <el-alert type="info" :closable="false" show-icon class="hint"
                  title="红点为模型判定异常周期；纵轴为 MinMax 归一化后的传感器值（0~1）。" />
      </el-card>
    </el-col>

    <!-- 右侧：最新周期关键指标 + 监测明细 -->
    <el-col :span="8">
      <el-card shadow="never" class="right-card">
        <template #header><span>最新周期概览（周期 #{{ latest?.cycle ?? '-' }}）</span></template>
        <el-descriptions :column="1" border size="small" v-if="latest">
          <el-descriptions-item label="健康度">
            <b :style="{ color: scoreColor(latest.health_score) }">{{ latest.health_score?.toFixed(1) }}</b>
          </el-descriptions-item>
          <el-descriptions-item label="健康等级">
            <el-tag :type="gradeType(latest.health_grade)">{{ latest.health_grade }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="RUL（剩余寿命）">{{ latest.rul?.toFixed(1) }} 周期</el-descriptions-item>
          <el-descriptions-item label="运行工况">
            设置1: {{ latest.op_setting_1_norm?.toFixed(3) }} / 设置2: {{ latest.op_setting_2_norm?.toFixed(3) }}
          </el-descriptions-item>
          <el-descriptions-item label="异常标记">
            <el-tag :type="latest.anomaly_label === 1 ? 'danger' : 'success'" size="small">
              {{ latest.anomaly_label === 1 ? '异常' : '正常' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <el-empty v-else description="暂无数据" />
      </el-card>

      <el-card shadow="never" class="right-card">
        <template #header><span>监测明细（最近 {{ items.length }} 个周期）</span></template>
        <el-table :data="items.slice(0, 12)" size="small" height="300" stripe>
          <el-table-column prop="cycle" label="周期" width="70" />
          <el-table-column label="健康度" width="80">
            <template #default="{ row }">{{ row.health_score?.toFixed(1) }}</template>
          </el-table-column>
          <el-table-column prop="sensor_13_norm" label="HPT排气(归一)" width="110">
            <template #default="{ row }">{{ row.sensor_13_norm?.toFixed(3) }}</template>
          </el-table-column>
          <el-table-column label="异常" width="70">
            <template #default="{ row }">
              <el-tag :type="row.anomaly_label === 1 ? 'danger' : 'success'" size="small">
                {{ row.anomaly_label === 1 ? '异常' : '正常' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { Refresh } from '@element-plus/icons-vue'
import { listEquipment, getSensorData } from '../api'

const route = useRoute()
const equipment = ref([])
const equipmentId = ref(null)
const items = ref([])
const latest = ref(null)
const loading = ref(false)
const chartRef = ref(null)
let chart = null

const sensorOptions = [
  { key: 'sensor_2_norm', label: '风扇入口温度' },
  { key: 'sensor_3_norm', label: 'LPC出口温度' },
  { key: 'sensor_4_norm', label: 'HPC出口温度' },
  { key: 'sensor_7_norm', label: 'HPC出口压力' },
  { key: 'sensor_13_norm', label: 'HPT排气温度' },
  { key: 'sensor_15_norm', label: '燃料流量' },
  { key: 'sensor_20_norm', label: '冷却空气温度' },
  { key: 'sensor_21_norm', label: '冷却空气压力' },
]
const selectedSensors = ref(['sensor_13_norm', 'sensor_7_norm'])

const SENSOR_NAMES = Object.fromEntries(sensorOptions.map((s) => [s.key, s.label]))

async function loadEquipment() {
  const data = await listEquipment({ page: 1, page_size: 200 })
  equipment.value = data.items || []
  if (equipmentId.value === null) {
    equipmentId.value = Number(route.query.id) || equipment.value[0]?.id
  }
  await loadData()
}

async function loadData() {
  if (!equipmentId.value) return
  loading.value = true
  try {
    const data = await getSensorData(equipmentId.value, { limit: 120, normalized: true })
    items.value = data.items || []
    latest.value = items.value[items.value.length - 1] || null
    await nextTick()
    renderChart()
  } finally {
    loading.value = false
  }
}

function renderChart() {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  const cycles = items.value.map((r) => r.cycle)
  const series = selectedSensors.value.map((key) => ({
    name: SENSOR_NAMES[key] || key,
    type: 'line',
    showSymbol: false,
    smooth: true,
    data: items.value.map((r) => r[key]),
  }))
  // 异常周期散点（红色高亮）
  const anomalyPoints = items.value
    .filter((r) => r.anomaly_label === 1)
    .map((r) => [r.cycle, 1.02])
  if (anomalyPoints.length) {
    series.push({
      name: '异常周期',
      type: 'scatter',
      symbolSize: 12,
      itemStyle: { color: '#f56c6c' },
      data: anomalyPoints,
    })
  }
  chart.setOption(
    {
      tooltip: { trigger: 'axis' },
      legend: { top: 0 },
      grid: { left: 40, right: 24, top: 36, bottom: 30 },
      xAxis: { type: 'category', data: cycles, name: '运行周期' },
      yAxis: { type: 'value', min: 0, max: 1.1, name: '归一化值' },
      series,
    },
    true,
  )
}

function scoreColor(v) {
  if (v >= 75) return '#67c23a'
  if (v >= 50) return '#e6a23c'
  if (v >= 25) return '#f56c6c'
  return '#b91c1c'
}
function gradeType(g) {
  return { 健康: 'success', 注意: 'info', 预警: 'warning', 严重: 'danger' }[g] || 'info'
}

function resize() {
  chart?.resize()
}

onMounted(() => {
  loadEquipment()
  window.addEventListener('resize', resize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart?.dispose()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 12px;
}
.toolbar .label {
  color: #606266;
  font-size: 13px;
}
.spacer {
  flex: 1;
}
.chart {
  height: 460px;
}
.hint {
  margin-top: 8px;
}
.right-card {
  margin-bottom: 12px;
}
</style>
