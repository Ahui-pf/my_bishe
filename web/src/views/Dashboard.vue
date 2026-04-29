<template>
  <div class="page-stack">
    <section class="dashboard-hero glass-panel">
      <div class="hero-copy">
        <p class="eyebrow">Dashboard Overview</p>
        <h1 class="section-title">欢迎回来，系统已经准备好开始演示</h1>
        <p class="section-copy">
          这里集中展示检测统计、常用操作和最近活动，适合答辩时快速串起登录、检测、记录与报告这条完整链路。
        </p>

        <div class="hero-actions">
          <router-link to="/detect" class="accent-button">开始智能检测</router-link>
          <button type="button" class="ghost-button" @click="downloadReport">导出检测报告</button>
        </div>

        <div class="chip-row">
          <span class="soft-chip">图片检测与视频检测一体化</span>
          <span class="soft-chip">实时检测支持 WebSocket</span>
          <span class="soft-chip">检测记录自动同步到个人中心</span>
        </div>
      </div>

      <div class="hero-focus">
        <article class="focus-card">
          <span>累计检测次数</span>
          <strong>{{ stats.totalDetections }}</strong>
          <p>系统运行期间已完成的检测任务总数</p>
        </article>
        <article class="focus-card accent">
          <span>累计识别目标</span>
          <strong>{{ stats.totalTargets }}</strong>
          <p>用于体现模型在实际演示中的识别效果</p>
        </article>
      </div>
    </section>

    <section class="stats-grid">
      <article class="metric-card">
        <p class="metric-label">总检测次数</p>
        <p class="metric-value">{{ stats.totalDetections }}</p>
        <p class="metric-note">包含图片、视频和实时检测保存记录</p>
      </article>
      <article class="metric-card">
        <p class="metric-label">图片检测次数</p>
        <p class="metric-value">{{ stats.imageDetections }}</p>
        <p class="metric-note">适合快速演示上传与结果对比</p>
      </article>
      <article class="metric-card">
        <p class="metric-label">视频检测次数</p>
        <p class="metric-value">{{ stats.videoDetections }}</p>
        <p class="metric-note">展示长流程检测与采样优化效果</p>
      </article>
      <article class="metric-card">
        <p class="metric-label">识别目标总数</p>
        <p class="metric-value">{{ stats.totalTargets }}</p>
        <p class="metric-note">用于表现模型识别到的目标规模</p>
      </article>
    </section>

    <section class="dashboard-grid">
      <article class="section-panel quick-panel">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">Quick Actions</p>
            <h2>快捷操作</h2>
          </div>
          <p>把答辩中最常点开的功能聚合到一起。</p>
        </div>

        <div class="action-grid">
          <router-link to="/detect" class="action-card">
            <span class="action-tag">图像 / 视频</span>
            <h3>智能检测</h3>
            <p>上传图片或视频后直接完成推理、预览和结果展示。</p>
          </router-link>

          <router-link to="/realtime-detect" class="action-card">
            <span class="action-tag">Camera</span>
            <h3>实时检测</h3>
            <p>打开摄像头进行实时识别，适合展示系统交互性。</p>
          </router-link>

          <button type="button" class="action-card action-button" @click="viewHistory">
            <span class="action-tag">Records</span>
            <h3>最近记录</h3>
            <p>快速查看检测活动入口，方便衔接到个人中心与仪表板。</p>
          </button>

          <button type="button" class="action-card action-button accent" @click="downloadReport">
            <span class="action-tag">PDF / JSON</span>
            <h3>导出报告</h3>
            <p>汇总检测结果并下载报告，强化项目完整度展示。</p>
          </button>
        </div>
      </article>

      <article class="section-panel activity-panel">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">Recent Activity</p>
            <h2>最近活动</h2>
          </div>
          <p>默认展示最近 5 条检测记录。</p>
        </div>

        <div v-if="recentActivities.length" class="activity-list">
          <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
            <div class="activity-badge">{{ activity.badge }}</div>
            <div class="activity-copy">
              <div class="activity-top">
                <h3>{{ activity.title }}</h3>
                <span>{{ activity.time }}</span>
              </div>
              <p>{{ activity.description }}</p>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          <strong>还没有检测记录</strong>
          <span>完成一次图片或视频检测后，这里会自动出现最新活动。</span>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElLoading } from 'element-plus'
import { authHttp, modelHttp } from '@/api/http'

const router = useRouter()

const stats = ref({
  totalDetections: 0,
  imageDetections: 0,
  videoDetections: 0,
  totalTargets: 0
})

const recentActivities = ref([])

const loadStats = async () => {
  try {
    const response = await authHttp.get('/user/stats')
    if (!response) return

    stats.value = {
      totalDetections: response.totalDetections || 0,
      imageDetections: response.totalImages || 0,
      videoDetections: response.totalVideos || 0,
      totalTargets: response.totalTargets || response.totalDetections || 0
    }
  } catch (err) {
    console.error('加载统计数据失败:', err)
    ElMessage.error('加载统计数据失败')
  }
}

const loadRecentActivities = async () => {
  try {
    const response = await authHttp.get('/user/detection-history?limit=5')
    if (!Array.isArray(response)) {
      recentActivities.value = []
      return
    }

    recentActivities.value = response.map((record) => {
      const isImage = record.detection_type === 'image'

      return {
        id: record.id,
        badge: isImage ? '图' : '视',
        title: isImage ? '图片检测' : '视频检测',
        description: `文件：${record.file_name}，检测到 ${record.target_count || 0} 个目标`,
        time: formatTime(record.created_at)
      }
    })
  } catch (err) {
    console.error('加载最近活动失败:', err)
    recentActivities.value = []
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return '刚刚'

  const now = new Date()
  const time = new Date(timestamp)
  const diff = now - time

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  if (hours < 24) return `${hours} 小时前`
  if (days < 7) return `${days} 天前`
  return time.toLocaleDateString()
}

const viewHistory = () => {
  router.push('/profile')
  ElMessage.info('最近记录已同步到个人中心与仪表板')
}

const downloadReport = async () => {
  let loadingInstance = null

  try {
    ElMessage.info('正在生成检测报告，请稍候')

    loadingInstance = ElLoading.service({
      lock: true,
      text: '正在整理检测记录并生成报告...',
      background: 'rgba(15, 23, 42, 0.35)'
    })

    const formData = new FormData()
    formData.append('format', 'pdf')
    formData.append('limit', '100')

    const response = await modelHttp.post('/report/generate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 30000
    })

    if (response?.success && response.pdf_content) {
      const link = document.createElement('a')
      link.href = response.pdf_content
      link.download = response.download_filename || `detection_report_${new Date().toISOString().slice(0, 10)}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      ElMessage.success('PDF 报告下载成功')
      return
    }

    if (response?.success && (response.format === 'json' || response.records)) {
      const jsonContent = JSON.stringify(response, null, 2)
      const blob = new Blob([jsonContent], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `detection_report_${new Date().toISOString().slice(0, 10)}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      ElMessage.success(response.error ? `${response.error}，已导出 JSON 报告` : 'JSON 报告下载成功')
      return
    }

    ElMessage.error(response?.message || '报告生成失败')
  } catch (err) {
    console.error('下载报告失败:', err)

    if (err?.status === 401) {
      ElMessage.error('登录状态失效，请重新登录后再试')
      return
    }

    if (err?.status === 500) {
      ElMessage.error('报告服务异常，请稍后重试')
      return
    }

    ElMessage.error(err?.detail || err?.message || '下载报告失败')
  } finally {
    loadingInstance?.close()
  }
}

onMounted(() => {
  loadStats()
  loadRecentActivities()
})
</script>

<style scoped>
.dashboard-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(260px, 0.9fr);
  gap: 22px;
  padding: 28px;
  border-radius: 30px;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.hero-focus {
  display: grid;
  gap: 16px;
}

.focus-card {
  padding: 22px;
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94) 0%, rgba(236, 254, 255, 0.92) 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: var(--shadow-card);
}

.focus-card.accent {
  background: linear-gradient(180deg, rgba(255, 247, 237, 0.98) 0%, rgba(255, 255, 255, 0.94) 100%);
}

.focus-card span {
  display: block;
  font-size: 13px;
  color: var(--text-soft);
}

.focus-card strong {
  display: block;
  margin-top: 10px;
  font-size: 42px;
  line-height: 1;
  color: var(--text-main);
}

.focus-card p {
  margin: 10px 0 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(320px, 0.92fr);
  gap: 20px;
}

.quick-panel,
.activity-panel {
  padding: 24px;
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  margin-bottom: 20px;
}

.panel-heading h2 {
  margin: 0;
  font-size: 24px;
  color: var(--text-main);
}

.panel-heading p:last-child {
  max-width: 260px;
  margin: 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.action-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 180px;
  padding: 20px;
  border-radius: 22px;
  text-decoration: none;
  color: inherit;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(245, 250, 251, 0.96) 100%);
  border: 1px solid rgba(15, 23, 42, 0.07);
  box-shadow: var(--shadow-card);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.action-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-hover);
  border-color: rgba(14, 116, 144, 0.14);
}

.action-card h3 {
  margin: 0;
  font-size: 20px;
  color: var(--text-main);
}

.action-card p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.7;
}

.action-tag {
  align-self: flex-start;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(15, 118, 110, 0.1);
  color: var(--brand-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.action-button {
  border: none;
  cursor: pointer;
  text-align: left;
}

.action-card.accent .action-tag {
  background: rgba(249, 115, 22, 0.12);
  color: var(--brand-accent);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.activity-item {
  display: flex;
  gap: 16px;
  padding: 18px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 251, 252, 0.95) 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.activity-badge {
  flex: none;
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.14) 0%, rgba(14, 116, 144, 0.14) 100%);
  color: var(--brand-primary-strong);
  font-size: 16px;
  font-weight: 800;
}

.activity-copy {
  min-width: 0;
  flex: 1;
}

.activity-top {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: center;
}

.activity-top h3 {
  margin: 0;
  font-size: 17px;
}

.activity-top span {
  font-size: 12px;
  color: var(--text-soft);
  white-space: nowrap;
}

.activity-copy p {
  margin: 8px 0 0;
  color: var(--text-muted);
  line-height: 1.6;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .dashboard-grid,
  .dashboard-hero {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard-hero,
  .quick-panel,
  .activity-panel {
    padding: 20px;
  }

  .action-grid,
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .panel-heading,
  .activity-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .focus-card strong {
    font-size: 36px;
  }
}
</style>
