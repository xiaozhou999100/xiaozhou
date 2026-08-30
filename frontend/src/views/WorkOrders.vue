<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-select v-model="filters.status" placeholder="状态" clearable style="width: 140px" @change="load">
        <el-option label="待处理" value="待处理" />
        <el-option label="维修中" value="维修中" />
        <el-option label="已完成" value="已完成" />
      </el-select>
      <el-button type="primary" :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
      <div class="spacer"></div>
      <el-button type="primary" :icon="Plus" @click="openForm()">新建工单</el-button>
    </div>

    <el-table :data="items" v-loading="loading" stripe border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="equipment_id" label="设备ID" width="80" />
      <el-table-column prop="alert_id" label="关联预警" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.alert_id" size="small">{{ row.alert_id }}</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="工单标题" min-width="200" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="diagnosis" label="诊断建议" min-width="200" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="warning" link :icon="Tools"
                     :disabled="row.status !== '待处理'" @click="setStatus(row, '维修中')">开始维修</el-button>
          <el-button size="small" type="success" link :icon="Check"
                     :disabled="row.status === '已完成'" @click="setStatus(row, '已完成')">完成</el-button>
          <el-button size="small" link :icon="View" @click="showDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建工单 -->
    <el-dialog v-model="dialog" title="新建运维工单" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="设备ID" required>
          <el-input-number v-model="form.equipment_id" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="工单标题" required>
          <el-input v-model="form.title" placeholder="如 更换HPT传感器" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="诊断建议">
          <el-input v-model="form.diagnosis" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Plus, Tools, Check, View } from '@element-plus/icons-vue'
import { listWorkOrders, createWorkOrder, updateWorkOrderStatus } from '../api'

const items = ref([])
const loading = ref(false)
const filters = reactive({ status: '' })
const dialog = ref(false)
const saving = ref(false)
const form = reactive({ equipment_id: 1, title: '', description: '', diagnosis: '' })

async function load() {
  loading.value = true
  try {
    const params = {}
    if (filters.status) params.status = filters.status
    params.limit = 200
    const data = await listWorkOrders(params)
    items.value = data.items || []
  } finally {
    loading.value = false
  }
}

async function setStatus(row, status) {
  await updateWorkOrderStatus(row.id, { status })
  ElMessage.success(`工单已更新为「${status}」`)
  load()
}

async function showDetail(row) {
  await ElMessageBox.alert(
    `<p><b>标题：</b>${row.title}</p>
     <p><b>描述：</b>${row.description || '-'}</p>
     <p><b>诊断建议：</b>${row.diagnosis || '-'}</p>
     <p><b>创建：</b>${row.created_at} · <b>更新：</b>${row.updated_at}</p>`,
    `工单 #${row.id} 详情`,
    { dangerouslyUseHTMLString: true },
  )
}

function openForm() {
  Object.assign(form, { equipment_id: 1, title: '', description: '', diagnosis: '' })
  dialog.value = true
}

async function save() {
  if (!form.title || !form.equipment_id) {
    ElMessage.warning('请填写设备ID与标题')
    return
  }
  saving.value = true
  try {
    await createWorkOrder({ ...form })
    ElMessage.success('工单创建成功')
    dialog.value = false
    load()
  } finally {
    saving.value = false
  }
}

function statusType(s) {
  return { 待处理: 'danger', 维修中: 'warning', 已完成: 'success' }[s] || 'info'
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
