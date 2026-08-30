import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as Icons from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

const app = createApp(App)

// 注册 Element Plus（中文）
app.use(ElementPlus, { locale: zhCn })

// 注册全部图标
for (const [name, comp] of Object.entries(Icons)) {
  app.component(name, comp)
}

app.use(router)
app.mount('#app')
