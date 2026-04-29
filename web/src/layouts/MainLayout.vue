<template>
  <div class="app-frame">
    <aside class="app-sidebar glass-panel">
      <div class="brand-block">
        <div class="brand-mark">AI</div>
        <div class="brand-copy">
          <p class="eyebrow">Graduation Demo</p>
          <h1>YOLO 路面病害检测平台</h1>
          <p>图片、视频与实时检测一体化展示界面</p>
        </div>
      </div>

      <nav class="nav-stack">
        <router-link
          v-for="item in visibleNavItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
        >
          <span class="nav-symbol">{{ item.symbol }}</span>
          <span class="nav-meta">
            <strong>{{ item.label }}</strong>
            <small>{{ item.description }}</small>
          </span>
        </router-link>
      </nav>

      <div class="sidebar-card">
        <p class="sidebar-card-label">当前页面</p>
        <strong>{{ currentPage.title }}</strong>
        <p>{{ currentPage.description }}</p>
        <div class="status-pill">
          <span class="status-dot"></span>
          {{ isAuthenticated ? '登录状态正常' : '等待登录' }}
        </div>
      </div>
    </aside>

    <main class="app-main">
      <header class="app-header">
        <div>
          <p class="eyebrow">Smart Detection Workspace</p>
          <h2>{{ currentPage.title }}</h2>
          <p>{{ currentPage.description }}</p>
        </div>
        <div class="header-note">
          <span class="header-note-tag">答辩展示模式</span>
          <strong>{{ currentPage.badge }}</strong>
        </div>
      </header>

      <section class="app-view">
        <router-view />
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { hasValidToken } from '@/utils/auth'

const route = useRoute()

const navItems = [
  {
    to: '/dashboard',
    label: '仪表板',
    description: '查看统计概览与最近活动',
    symbol: '览'
  },
  {
    to: '/detect',
    label: '智能检测',
    description: '上传图片或视频进行分析',
    symbol: '检'
  },
  {
    to: '/realtime-detect',
    label: '实时检测',
    description: '打开摄像头进行实时识别',
    symbol: '实'
  },
  {
    to: '/profile',
    label: '个人中心',
    description: '管理账号信息与报告操作',
    symbol: '我'
  },
  {
    to: '/help',
    label: '帮助文档',
    description: '查看使用说明与答辩流程',
    symbol: '助'
  }
]

const pageMap = {
  '/dashboard': {
    title: '系统仪表板',
    description: '集中展示检测总览、快捷操作与最近活动，方便答辩时快速切换。',
    badge: '数据总览'
  },
  '/detect': {
    title: '智能检测工作台',
    description: '支持图片与视频两种模式，上传、推理、结果对比都在同一页完成。',
    badge: '上传检测'
  },
  '/realtime-detect': {
    title: '实时检测控制台',
    description: '连接摄像头后进行低延迟检测，实时查看识别框与性能统计。',
    badge: '实时推理'
  },
  '/profile': {
    title: '个人中心',
    description: '维护用户资料、密码、统计信息与报告下载入口。',
    badge: '账号管理'
  },
  '/help': {
    title: '帮助文档',
    description: '提供系统简介、功能说明、参数解释与推荐演示顺序。',
    badge: '使用说明'
  }
}

const isAuthenticated = computed(() => {
  route.fullPath
  return hasValidToken()
})

const visibleNavItems = computed(() => navItems)

const currentPage = computed(() => {
  return pageMap[route.path] || {
    title: 'YOLO 检测平台',
    description: '面向毕业答辩演示的一体化智能检测系统。',
    badge: '系统页面'
  }
})
</script>

<style scoped>
.app-frame {
  display: grid;
  grid-template-columns: 308px minmax(0, 1fr);
  gap: 22px;
  min-height: 100vh;
  padding: 20px;
}

.app-sidebar {
  position: sticky;
  top: 20px;
  align-self: start;
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding: 24px;
  border-radius: 30px;
}

.brand-block {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 58px;
  height: 58px;
  border-radius: 18px;
  color: #ffffff;
  font-weight: 800;
  letter-spacing: 0.08em;
  background: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-primary-strong) 100%);
  box-shadow: 0 16px 28px rgba(15, 118, 110, 0.24);
}

.brand-copy h1 {
  margin: 0;
  font-size: 24px;
  line-height: 1.2;
  color: var(--text-main);
}

.brand-copy p:last-child {
  margin: 8px 0 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.nav-stack {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 18px;
  text-decoration: none;
  color: var(--text-main);
  border: 1px solid transparent;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.nav-link:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.72);
  border-color: rgba(15, 23, 42, 0.06);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
}

.nav-link.router-link-active {
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.14) 0%, rgba(14, 116, 144, 0.12) 100%);
  border-color: rgba(15, 118, 110, 0.2);
  box-shadow: 0 16px 28px rgba(15, 118, 110, 0.1);
}

.nav-symbol {
  flex: none;
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.9);
  color: var(--brand-primary-strong);
  font-size: 16px;
  font-weight: 800;
}

.nav-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-meta strong {
  font-size: 15px;
}

.nav-meta small {
  font-size: 12px;
  color: var(--text-soft);
}

.sidebar-card {
  margin-top: auto;
  padding: 18px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(244, 250, 251, 0.96) 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.sidebar-card-label {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-soft);
}

.sidebar-card strong {
  display: block;
  font-size: 18px;
}

.sidebar-card p {
  margin: 8px 0 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(15, 118, 110, 0.1);
  color: var(--brand-primary);
  font-size: 13px;
  font-weight: 700;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: currentColor;
}

.app-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  padding: 28px 30px;
  border-radius: 30px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.88) 0%, rgba(236, 254, 255, 0.82) 100%);
  border: 1px solid rgba(255, 255, 255, 0.75);
  box-shadow: var(--shadow-soft);
  backdrop-filter: blur(18px) saturate(140%);
}

.app-header h2 {
  margin: 0;
  font-size: 32px;
  line-height: 1.15;
  color: var(--text-main);
}

.app-header p:last-child {
  margin: 10px 0 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.header-note {
  flex: none;
  min-width: 170px;
  padding: 18px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(255, 247, 237, 0.96) 0%, rgba(255, 255, 255, 0.98) 100%);
  border: 1px solid rgba(249, 115, 22, 0.12);
  box-shadow: 0 14px 28px rgba(249, 115, 22, 0.08);
}

.header-note-tag {
  display: inline-block;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--brand-accent);
}

.header-note strong {
  display: block;
  margin-top: 10px;
  font-size: 22px;
  color: var(--text-main);
}

.app-view {
  min-width: 0;
}

@media (max-width: 1200px) {
  .app-frame {
    grid-template-columns: 1fr;
  }

  .app-sidebar {
    position: static;
  }

  .nav-stack {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }
}

@media (max-width: 768px) {
  .app-frame {
    padding: 14px;
    gap: 14px;
  }

  .app-sidebar,
  .app-header {
    padding: 20px;
    border-radius: 24px;
  }

  .app-header {
    flex-direction: column;
  }

  .app-header h2 {
    font-size: 28px;
  }

  .nav-stack {
    grid-template-columns: 1fr;
  }

  .header-note {
    width: 100%;
  }
}
</style>
