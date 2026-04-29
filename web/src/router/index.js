import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import Dashboard from '../views/Dashboard.vue'
import Detect from '../views/Detect.vue'
import RealtimeDetect from '../views/RealtimeDetect.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Profile from '../views/Profile.vue'
import Help from '../views/Help.vue'
import { clearStoredToken, hasValidToken } from '@/utils/auth'

const routes = [
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: Dashboard },
      { path: 'detect', component: Detect },
      { path: 'realtime-detect', component: RealtimeDetect },
      { path: 'profile', component: Profile },
      { path: 'help', component: Help }
    ]
  },
  { path: '/test', component: { template: '<div style="padding:16px">Test 渲染正常</div>' } },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const isAuthenticated = hasValidToken()

  if (!isAuthenticated && localStorage.getItem('token')) {
    clearStoredToken()
  }

  if ((to.path === '/login' || to.path === '/register') && isAuthenticated) {
    next('/dashboard')
    return
  }

  if (to.matched.some(record => record.meta.requiresAuth) && !isAuthenticated) {
    next('/login')
    return
  }

  next()
})

export default router
