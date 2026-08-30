<template>
  <el-row :gutter="12">
    <!-- 左侧：触发评估 + 指标仪表盘 -->
    <el-col :span="10">
      <el-card shadow="never">
        <div class="toolbar">
          <span class="label">设备：</span>
          <el-select v-model="equipmentId" filterable style="width: 240px" @change="loadHistory">
            <el-option v-for="eq in equipment" :key="eq.id" :label="`${eq.device_code} · ${eq.name}`"
                       :value="eq.id" />
          </el-select>
          <div class="spacer"></div>
          <el-button type="primary" :icon="Odometer" :loading="evaluating" @click="runEvaluate">
            触发随机森林评估
          </el-button>
        </div>

        <div v-if="latest" class="gauges">
          <div ref="gaugeRef" class="gauge"></div>
          <div class="gauge-meta">
            <p><b>健康等级：</b><el-tag :type="gradeType(latest.health_grade)">{{ latest.health_grade }}</el-tag></p>
            <p class="detail">{{ latest.detail }}</p>
            <p class="time">评估时间：{{ latest.eval_time }}</p>
          </div>
        </div>
        <el-empty v-else description="点击「触发随机森林评估」查看健康/能耗指标" />
      </el-card>
    </el-col>

    <!-- 右侧：历史评估记录 -->
    <el-col :span="14">
      <el-card shadow="never">
        <template #header><span>历史评估记录（按时间倒序）</span></template>
        <el-table :data="history" v-loading="historyLoading" stripe border>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="eval_time" label="评估时间" width="170" />
          <el-table-column label="健康度" width="90">
            <template #default="{ row }">
              <b :style="{ color: scoreColor(row.health_score) }">{{ row.health_score.toFixed(1) }}</b>
            </template>
          </el-table-column>
          <el-table-column label="能耗效率" width="90">
            <template #default="{ row }">{{ row.energy_efficiency.toFixed(1) }}</template>
          </el-table-column>
          <el-table-column label="负载率" width="80">
            <template #default="{ row }">{{ row.load_rate.toFixed(1) }}%</template>
          </el-table-column>
          <el-table-column label="健康等级" width="90">
            <template #default="{ row }">
              <el-tag :type="gradeType(row.health_grade)">{{ row.health_grade }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="detail" label="评估说明" min-width="260" show-overflow-tooltip />
        </el-table>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { Odometer } from '@element-plus/icons-vue'
import { listEquipment, evaluate, getEvaluations } from '../api'

const route = useRoute()
const equipment = ref([])
const equipmentId = ref(null)
const latest = ref(null)
const history = ref([])
const evaluating = ref(false)
const historyLoading = ref(false)
const gaugeRef = ref(null)
let gauge = null

async function loadEquipment() {
  const data = await listEquipment({ page: 1, page_size: 200 })
  equipment.value = data.items || []
  equipmentId.value = Number(route.query.id) || equipment.value[0]?.id
  await loadHistory()
}

async function loadHistory() {
  if (!equipmentId.value) return
  historyLoading.value = true
  try {
    const data = await getEvaluations(equipmentId.value, { limit: 50 })
    history.value = data.items || []
    latest.value = history.value[0] || null
    await nextTick()
    renderGauge()
  } finally {
    historyLoading.value = false
  }
}

async function runEvaluate() {
  if (!equipmentId.value) {
    ElMessage.warning('请先选择设备')
    return
  }
  evaluating.value = true
  try {
    await evaluate(equipmentId.value, {})
    ElMessage.success('评估完成（随机森林 RUL 预测）')
    await loadHistory()
  } finally {
    evaluating.value = false
  }
}

function renderGauge() {
  const rec = latest.value
  if (!rec || !gaugeRef.value) return
  if (!gauge) gauge = echarts.init(gaugeRef.value)
  const value = Number(rec.health_score) || 0
  gauge.setOption(
    {
      series: [
        {
          type: 'gauge',
          startAngle: 200,
          endAngle: -20,
          min: 0,
          max: 100,
          splitNumber: 5,
          radius: '95%',
          axisLine: {
            lineStyle: {
              width: 18,
              color: [
                [0.25, '#f56c6c'],
                [0.5, '#e6a23c'],
                [0.75, '#409eff'],
                [1, '#67c23a'],
              ],
            },
          },
          progress: { show: true, width: 18 },
          pointer: { length: '60%', width: 5 },
          axisTick: { distance: -22 },
          splitLine: { distance: -22, length: 8 },
          axisLabel: { distance: 18, fontSize: 11 },
          anchor: { show: true, size: 14 },
          title: { offsetCenter: [0, '38%'], fontSize: 13 },
          detail: {
            offsetCenter: [0, '68%'],
            fontSize: 22,
            formatter: '{value}',
          },
          data: [{ value, name: '健康度' }],
        },
      ],
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
  gauge?.resize()
}

onMounted(() => {
  loadEquipment()
  window.addEventListener('resize', resize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  gauge?.dispose()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
.toolbar .label {
  color: #606266;
  font-size: 13px;
}
.spacer {
  flex: 1;
}
.gauge {
  height: 340px;
}
.gauge-meta {
  margin-top: 6px;
}
.detail {
  color: #606266;
  font-size: 13px;
  line-height: 1.7;
}
.time {
  color: #909399;
  font-size: 12px;
}
</style>
