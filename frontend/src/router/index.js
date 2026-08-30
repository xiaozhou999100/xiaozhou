import { createRouter, createWebHistory } from 'vue-router'

import MainLayout from '../layout/MainLayout.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    redirect: '/twin',
    children: [
      {
        path: 'twin',
        name: 'Twin',
        component: () => import('../views/Twin.vue'),
        meta: { title: '数字孪生可视化', icon: 'Monitor' },
      },
      {
        path: 'equipment',
        name: 'Equipment',
        component: () => import('../views/Equipment.vue'),
        meta: { title: '车间设备台账', icon: 'Box' },
      },
      {
        path: 'monitoring',
        name: 'Monitoring',
        component: () => import('../views/Monitoring.vue'),
        meta: { title: '实时数据监测', icon: 'DataLine' },
      },
      {
        path: 'evaluation',
        name: 'Evaluation',
        component: () => import('../views/Evaluation.vue'),
        meta: { title: '健康与能耗评估', icon: 'Odometer' },
      },
      {
        path: 'alerts',
        name: 'Alerts',
        component: () => import('../views/Alerts.vue'),
        meta: { title: '孪生预警中心', icon: 'Bell' },
      },
      {
        path: 'work-orders',
        name: 'WorkOrders',
        component: () => import('../views/WorkOrders.vue'),
        meta: { title: '运维工单管理', icon: 'Tickets' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.afterEach((to) => {
  document.title = `${to.meta?.title || ''} - 数字孪生车间智能监控与运维平台`
})

export default router
