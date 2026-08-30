import axios from 'axios'
import { ElMessage } from 'element-plus'

// 统一 axios 实例：走 Vite 代理 /api → 后端 8000
const http = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

http.interceptors.response.use(
  (resp) => {
    const body = resp.data
    if (body && typeof body.code !== 'undefined') {
      if (body.code !== 0) {
        ElMessage.error(body.message || '请求失败')
        return Promise.reject(new Error(body.message))
      }
      return body.data
    }
    return body
  },
  (error) => {
    const detail = error.response?.data?.detail || error.message || '网络错误'
    ElMessage.error(detail)
    return Promise.reject(error)
  },
)

// ---- 设备台账 ----
export const listEquipment = (params) => http.get('/equipment', { params })
export const getEquipment = (id) => http.get(`/equipment/${id}`)
export const createEquipment = (payload) => http.post('/equipment', payload)
export const updateEquipment = (id, payload) => http.put(`/equipment/${id}`, payload)
export const deleteEquipment = (id) => http.delete(`/equipment/${id}`)

// ---- 传感器数据 ----
export const getSensorData = (id, params) => http.get(`/equipment/${id}/sensor-data`, { params })

// ---- 健康评估 ----
export const getEvaluations = (id, params) => http.get(`/equipment/${id}/evaluations`, { params })
export const evaluate = (id, payload = {}) => http.post(`/equipment/${id}/evaluate`, payload)

// ---- 算法服务 ----
export const anomalyCheck = (id) => http.post(`/equipment/${id}/anomaly-check`)
export const diagnose = (id, payload = {}) => http.post(`/equipment/${id}/diagnose`, payload)

// ---- 预警 ----
export const listAlerts = (params) => http.get('/alerts', { params })
export const createAlert = (payload) => http.post('/alerts', payload)
export const handleAlert = (id) => http.patch(`/alerts/${id}/handle`)

// ---- 工单 ----
export const listWorkOrders = (params) => http.get('/work-orders', { params })
export const createWorkOrder = (payload) => http.post('/work-orders', payload)
export const updateWorkOrderStatus = (id, payload) => http.patch(`/work-orders/${id}/status`, payload)

export default http
