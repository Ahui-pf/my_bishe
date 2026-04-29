import { createApp, h } from 'vue'
import { RouterView } from 'vue-router'
import router from './router/index.js'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './styles/theme.css'

// 使用渲染函数并显式渲染 RouterView
createApp({ render: () => h(RouterView) })
  .use(router)
  .use(ElementPlus)
  .mount('#app')
