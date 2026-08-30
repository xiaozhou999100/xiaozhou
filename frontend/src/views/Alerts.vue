<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-select v-model="filters.level" placeholder="级别" clearable style="width: 120px" @change="load">
        <el-option label="提示" value="提示" />
        <el-option label="警告" value="警告" />
        <el-option label="严重" value="严重" />
      </el-select>
      <el-select v-model="filters.is_handled" placeholder="处理状态" clearable style="width: 140px" @change="load">
        <el-option label="未处理" :value="false" />
        <el-option label="已处理" :value="true" />
      </el-select>
      <el-button type="primary" :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
      <div class="spacer"></div>
      <el-button type="warning" :icon="AlarmClock" @click="runAnomalyCheck">孤立森林异常检测</el-button>
    </div>

    <el-table :data="items" v-loading="loading" stripe border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="equipment_id" label="设备ID" width="80" />
      <el-table-column prop="alert_type" label="预警类型" width="130" />
      <el-table-column label="级别" width="90">
        <template #default="{ row }">
          <el-tag :type="levelType(row.level)">{{ row.level }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="message" label="预警内容" min-width="260" show-overflow-tooltip />
      <el-table-column prop="sensor_point" label="关联点位" width="130" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_handled ? 'info' : 'danger'" size="small">
            {{ row.is_handled ? '已处理' : '未处理' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="产生时间" width="170" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="warning" link :icon="Tickets"
                     :disabled="row.is_handled" @click="toOrder(row)">生成工单</el-button>
          <el-button size="small" type="success" link :icon="Check"
                     :disabled="row.is_handled" @click="handle(row)">处理</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, AlarmClock, Tickets, Check } from '@element-plus/icons-vue'
import { listAlerts, handleAlert, createWorkOrder, anomalyCheck } from '../api'

const items = ref([])
const loading = ref(false)
const filters = reactive({ level: '', is_handled: null })

async function load() {
  loading.value = true
  try {
    const params = {}
    if (filters.level) params.level = filters.level
    if (filters.is_handled !== null && filters.is_handled !== '') params.is_handled = filters.is_handled
    params.limit = 200
    const data = await listAlerts(params)
    items.value = data.items || []
  } finally {
    loading.value = false
  }
}

async function handle(row) {
  await handleAlert(row.id)
  ElMessage.success('已标记处理')
  load()
}

async function toOrder(row) {
  await createWorkOrder({
    alert_id: row.id,
    equipment_id: row.equipment_id,
    title: `[预警]${row.alert_type}`,
    description: row.message,
  })
  ElMessage.success('已从预警生成运维工单')
  load()
}

async function runAnomalyCheck() {
  const { ElMessageBox } = await import('element-plus')
  let target = null
  try {
    const { value } = await ElMessageBox.prompt('请输入设备ID进行孤立森林异常检测', '异常检测', {
      inputPattern: /^\d+$/,
      inputErrorMessage: '请输入数字设备ID',
      inputValue: '1',
    })
    target = Number(value)
  } catch {
    return
  }
  const res = await anomalyCheck(target)
  ElMessage({
    type: res.is_anomaly ? 'warning' : 'success',
    message: `设备 #${target}：${res.message}`,
    duration: 6000,
  })
  load()
}

function levelType(l) {
  return { 提示: 'info', 警告: 'warning', 严重: 'danger' }[l] || 'info'
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
  align-items: center;
}
.spacer {
  flex: 1;
}
</style>
