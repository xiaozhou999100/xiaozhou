<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="设备编号/名称搜索" clearable style="width: 240px"
                  :prefix-icon="Search" @keyup.enter="load(1)" @clear="load(1)" />
        <el-select v-model="statusFilter" placeholder="孪生状态" clearable style="width: 140px" @change="load(1)">
          <el-option label="运行" value="运行" />
          <el-option label="待机" value="待机" />
          <el-option label="报警" value="报警" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="load(1)">查询</el-button>
        <div class="spacer"></div>
        <el-button type="primary" :icon="Plus" @click="openForm()">新增设备</el-button>
      </div>

      <el-table :data="items" v-loading="loading" stripe border>
        <el-table-column prop="device_code" label="设备编号" width="100" />
        <el-table-column prop="name" label="设备名称" min-width="140" />
        <el-table-column prop="model" label="型号" width="120" />
        <el-table-column prop="station" label="工位" width="90" />
        <el-table-column prop="install_date" label="投运日期" width="105" />
        <el-table-column label="孪生状态" width="88">
          <template #default="{ row }">
            <el-tag :type="statusType(row.twin_status)">{{ row.twin_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="健康等级" width="88">
          <template #default="{ row }">
            <el-tag :type="gradeType(row.health_grade)">{{ row.health_grade }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="备注" min-width="120" show-overflow-tooltip />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link :icon="DataLine"
                       @click="goMonitor(row)">监测</el-button>
            <el-button size="small" type="success" link :icon="Odometer"
                       @click="goEvaluation(row)">评估</el-button>
            <el-button size="small" link :icon="Edit" @click="openForm(row)">编辑</el-button>
            <el-button size="small" type="danger" link :icon="Delete"
                       @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination class="pager" background layout="total, prev, pager, next, sizes"
                     :total="total" v-model:current-page="page" v-model:page-size="pageSize"
                     :page-sizes="[10, 20, 50, 100]" @current-change="load()" @size-change="load(1)" />
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialog" :title="form.id ? '编辑设备' : '新增设备'" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="设备编号" required>
          <el-input v-model="form.device_code" :disabled="!!form.id" placeholder="如 DEV101" />
        </el-form-item>
        <el-form-item label="设备名称" required>
          <el-input v-model="form.name" placeholder="如 数控车床" />
        </el-form-item>
        <el-form-item label="型号">
          <el-input v-model="form.model" />
        </el-form-item>
        <el-form-item label="工位">
          <el-input v-model="form.station" placeholder="如 3-1" />
        </el-form-item>
        <el-form-item label="投运日期">
          <el-date-picker v-model="form.install_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="孪生状态">
          <el-select v-model="form.twin_status" style="width: 100%">
            <el-option label="运行" value="运行" />
            <el-option label="待机" value="待机" />
            <el-option label="报警" value="报警" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Edit, Delete, DataLine, Odometer } from '@element-plus/icons-vue'
import { listEquipment, createEquipment, updateEquipment, deleteEquipment } from '../api'

const route = useRoute()
const router = useRouter()

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const statusFilter = ref('')
const loading = ref(false)

const dialog = ref(false)
const saving = ref(false)
const form = reactive({
  id: null, device_code: '', name: '', model: '', station: '',
  install_date: null, twin_status: '运行', health_grade: '健康', description: '',
})

const emptyForm = () => ({
  id: null, device_code: '', name: '', model: '', station: '',
  install_date: null, twin_status: '运行', health_grade: '健康', description: '',
})

async function load(p = page.value) {
  loading.value = true
  try {
    const data = await listEquipment({
      page: p, page_size: pageSize.value, keyword: keyword.value || undefined,
      status: statusFilter.value || undefined,
    })
    items.value = data.items || []
    total.value = data.total || 0
    page.value = data.page || 1
  } finally {
    loading.value = false
  }
}

function openForm(row) {
  Object.assign(form, emptyForm(), row ? { ...row, id: row.id } : {})
  dialog.value = true
}

async function save() {
  if (!form.device_code || !form.name) {
    ElMessage.warning('设备编号与名称必填')
    return
  }
  saving.value = true
  try {
    if (form.id) {
      await updateEquipment(form.id, { ...form })
    } else {
      await createEquipment({ ...form })
    }
    ElMessage.success('保存成功')
    dialog.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除设备 ${row.device_code}（${row.name}）？`, '提示', { type: 'warning' })
  await deleteEquipment(row.id)
  ElMessage.success('已删除')
  load()
}

function goMonitor(row) {
  router.push({ path: '/monitoring', query: { id: row.id, code: row.device_code } })
}
function goEvaluation(row) {
  router.push({ path: '/evaluation', query: { id: row.id, code: row.device_code } })
}

function statusType(s) {
  return { 运行: 'success', 待机: 'warning', 报警: 'danger' }[s] || 'info'
}
function gradeType(g) {
  return { 健康: 'success', 注意: 'info', 预警: 'warning', 严重: 'danger' }[g] || 'info'
}

onMounted(() => {
  if (route.query.id) {
    // 从孪生页跳转，保持选中
  }
  load()
})
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
.pager {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
